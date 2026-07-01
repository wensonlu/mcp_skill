import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { classifyChangedPaths } from '../scripts/ios-incremental-sync.mjs';

describe('classifyChangedPaths', () => {
  it('syncs only H5 output when only frontend web source changes', () => {
    assert.deepEqual(
      classifyChangedPaths([
        'frontend/src/pages/Home.jsx',
        'frontend/src/components/BottomNav.jsx',
      ]),
      {
        hasH5: true,
        hasRnJs: false,
        hasNative: false,
        actions: ['h5-sync'],
      }
    );
  });

  it('syncs only RN bundle when RN JavaScript changes without native changes', () => {
    assert.deepEqual(
      classifyChangedPaths([
        'rn-app/App.js',
        'rn-app/src/screens/RnDemoScreen.js',
      ]),
      {
        hasH5: false,
        hasRnJs: true,
        hasNative: false,
        actions: ['rn-bundle'],
      }
    );
  });

  it('requires native build when iOS, Podfile, app config, or RN dependency files change', () => {
    assert.deepEqual(
      classifyChangedPaths([
        'frontend/ios/App/App/RNHostManager.swift',
        'frontend/ios/App/Podfile',
        'rn-app/package.json',
      ]),
      {
        hasH5: false,
        hasRnJs: false,
        hasNative: true,
        actions: ['native-build'],
      }
    );
  });

  it('combines H5 sync with RN bundle for mixed JS-only changes', () => {
    assert.deepEqual(
      classifyChangedPaths([
        'frontend/src/pages/ForumDetail.jsx',
        'rn-app/src/services/api.js',
      ]),
      {
        hasH5: true,
        hasRnJs: true,
        hasNative: false,
        actions: ['h5-sync', 'rn-bundle'],
      }
    );
  });

  it('ignores generated outputs and docs when deciding actions', () => {
    assert.deepEqual(
      classifyChangedPaths([
        'frontend/dist/assets/index.js',
        'frontend/ios/App/App/public/assets/index.js',
        'frontend/ios/App/App/rn_bundle/main.jsbundle',
        'docs/plans/example.md',
      ]),
      {
        hasH5: false,
        hasRnJs: false,
        hasNative: false,
        actions: [],
      }
    );
  });
});
