#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function hasGitDir(candidate) {
  return existsSync(path.join(candidate, '.git'));
}

function findGitRoot(startDir) {
  let current = path.resolve(startDir);
  while (true) {
    if (hasGitDir(current)) return current;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function resolveRepoRoot() {
  const explicitRoot = process.env.IOS_INCREMENTAL_SYNC_ROOT;
  const candidates = [
    explicitRoot,
    process.cwd(),
    path.resolve(__dirname, '../../../..'),
    path.resolve(__dirname, '../../..'),
    findGitRoot(process.cwd()),
    findGitRoot(__dirname),
  ].filter(Boolean);

  const repoRoot = candidates.find(hasGitDir);
  if (!repoRoot) {
    throw new Error('Expected to run inside a Git repository. Set IOS_INCREMENTAL_SYNC_ROOT to the Dog Project root if needed.');
  }

  return repoRoot;
}

const repoRoot = resolveRepoRoot();

const ignoredPrefixes = [
  'node_modules/',
  'frontend/node_modules/',
  'rn-app/node_modules/',
  'frontend/dist/',
  'frontend/ios/App/App/public/',
  'frontend/ios/App/App/rn_bundle/',
  'rn-app/dist/',
  'rn-app/.expo/',
  '.git/',
];

const h5Prefixes = [
  'frontend/src/',
  'frontend/public/',
];

const h5Files = new Set([
  'frontend/index.html',
  'frontend/vite.config.js',
  'frontend/vitest.config.js',
  'frontend/tailwind.config.js',
  'frontend/postcss.config.js',
  'frontend/eslint.config.js',
]);

const rnJsPrefixes = [
  'rn-app/src/',
  'rn-app/assets/',
];

const rnJsFiles = new Set([
  'rn-app/App.js',
  'rn-app/index.js',
  'rn-app/app.json',
  'rn-app/metro.config.js',
]);

const nativePrefixes = [
  'frontend/ios/',
  'rn-app/ios/',
  'rn-app/android/',
];

const nativeFiles = new Set([
  'frontend/capacitor.config.json',
  'frontend/package.json',
  'frontend/pnpm-lock.yaml',
  'frontend/package-lock.json',
  'frontend/ios/App/Podfile',
  'frontend/ios/App/Podfile.lock',
  'rn-app/package.json',
  'rn-app/pnpm-lock.yaml',
  'rn-app/package-lock.json',
]);

function normalizePath(filePath) {
  return String(filePath || '')
    .replace(/\\/g, '/')
    .replace(/^\.\//, '')
    .trim();
}

function isIgnored(filePath) {
  return ignoredPrefixes.some((prefix) => filePath === prefix.slice(0, -1) || filePath.startsWith(prefix));
}

function isH5Path(filePath) {
  return h5Files.has(filePath) || h5Prefixes.some((prefix) => filePath.startsWith(prefix));
}

function isRnJsPath(filePath) {
  return rnJsFiles.has(filePath) || rnJsPrefixes.some((prefix) => filePath.startsWith(prefix));
}

function isNativePath(filePath) {
  return nativeFiles.has(filePath) || nativePrefixes.some((prefix) => filePath.startsWith(prefix));
}

export function classifyChangedPaths(paths) {
  const relevantPaths = [...new Set(paths.map(normalizePath).filter(Boolean))]
    .filter((filePath) => !isIgnored(filePath));

  const hasNative = relevantPaths.some(isNativePath);
  const hasH5 = relevantPaths.some((filePath) => !isNativePath(filePath) && isH5Path(filePath));
  const hasRnJs = relevantPaths.some((filePath) => !isNativePath(filePath) && isRnJsPath(filePath));

  const actions = [];
  if (hasH5) actions.push('h5-sync');
  if (hasRnJs) actions.push('rn-bundle');
  if (hasNative) actions.push('native-build');

  return { hasH5, hasRnJs, hasNative, actions };
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    stdio: 'inherit',
    shell: false,
    env: process.env,
  });

  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}`);
  }
}

function capture(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: 'utf8',
    shell: false,
    env: process.env,
  });

  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}`);
  }

  return result.stdout;
}

function getChangedPathsSince(ref) {
  const output = capture('git', ['diff', '--name-only', ref, '--']);
  return output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function getGitSnapshot() {
  const output = capture('git', ['status', '--porcelain=v1']);
  return output
    .split(/\r?\n/)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .map((line) => line.includes(' -> ') ? line.split(' -> ').pop() : line);
}

function executeActions(actions, { dryRun = false } = {}) {
  if (actions.length === 0) {
    console.log('No H5/RN/iOS sync action needed.');
    return;
  }

  if (actions.includes('h5-sync')) {
    const command = 'pnpm build && npx cap copy ios';
    console.log(`[h5-sync] cd frontend && ${command}`);
    if (!dryRun) {
      run('pnpm', ['build'], { cwd: path.join(repoRoot, 'frontend') });
      run('npx', ['cap', 'copy', 'ios'], { cwd: path.join(repoRoot, 'frontend') });
    }
  }

  if (actions.includes('rn-bundle')) {
    console.log('[rn-bundle] cd rn-app && pnpm bundle:ios');
    if (!dryRun) {
      run('pnpm', ['bundle:ios'], { cwd: path.join(repoRoot, 'rn-app') });
    }
  }

  if (actions.includes('native-build')) {
    console.log('[native-build] Native-impact change detected. Rebuild iOS deliberately.');
    console.log('Recommended: cd frontend/ios/App && pod install && xcodebuild -workspace App.xcworkspace -scheme App -configuration Debug -sdk iphonesimulator -destination "platform=iOS Simulator,name=iPhone 17" CODE_SIGNING_ALLOWED=NO -quiet build');
  }
}

function parseArgs(argv) {
  const options = {
    changed: [],
    since: 'HEAD',
    dryRun: false,
    watch: false,
    intervalMs: 1200,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--changed') {
      options.changed.push(...String(argv[index + 1] || '').split(','));
      index += 1;
    } else if (arg === '--since') {
      options.since = argv[index + 1] || options.since;
      index += 1;
    } else if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--watch') {
      options.watch = true;
    } else if (arg === '--interval-ms') {
      options.intervalMs = Number(argv[index + 1] || options.intervalMs);
      index += 1;
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    }
  }

  return options;
}

function printHelp() {
  console.log(`Usage:
  node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --dry-run --changed frontend/src/App.jsx,rn-app/App.js
  node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --dry-run --since HEAD
  node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --watch

Environment:
  IOS_INCREMENTAL_SYNC_ROOT=/path/to/dog_project

Actions:
  h5-sync      cd frontend && pnpm build && npx cap copy ios
  rn-bundle    cd rn-app && pnpm bundle:ios
  native-build prompt only; rebuild iOS deliberately
`);
}

async function watchLoop(options) {
  console.log(`Watching git working tree every ${options.intervalMs}ms. Press Ctrl+C to stop.`);
  let lastKey = '';
  let running = false;

  setInterval(() => {
    if (running) return;
    const changed = getGitSnapshot();
    const key = changed.sort().join('\n');
    if (!key || key === lastKey) return;

    running = true;
    lastKey = key;
    try {
      const result = classifyChangedPaths(changed);
      console.log(`Changed paths:\n${changed.map((item) => `- ${item}`).join('\n')}`);
      console.log(`Actions: ${result.actions.join(', ') || 'none'}`);
      executeActions(result.actions, options);
    } catch (error) {
      console.error(error.message);
    } finally {
      running = false;
    }
  }, options.intervalMs);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  if (!existsSync(path.join(repoRoot, '.git')) || !statSync(path.join(repoRoot, '.git')).isDirectory()) {
    throw new Error(`Expected repo root at ${repoRoot}`);
  }

  if (options.watch) {
    await watchLoop(options);
    return;
  }

  const changed = options.changed.length > 0 ? options.changed : getChangedPathsSince(options.since);
  const result = classifyChangedPaths(changed);
  console.log(JSON.stringify({ changed: changed.map(normalizePath).filter(Boolean), ...result }, null, 2));
  executeActions(result.actions, options);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
