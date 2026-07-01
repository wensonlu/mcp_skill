---
name: feishu-link-to-obsidian
description: >-
  Exports Feishu/Lark wiki or docx links to cleaned Markdown under the user's
  Obsidian vault using MCP feishu_reader; downloads embedded images and videos
  into a per-note asset folder and rewrites Markdown to local relative paths.
  Use when the user pastes Feishu/Lark document URLs, asks to save a Feishu doc
  to Obsidian, or wants the same export workflow including media extraction.
---

# 飞书链接 → Obsidian Markdown（含图片/视频落盘）

当用户发来**飞书/ Lark 文档链接**且希望落到 Obsidian 时，按下面流程执行；无需用户重复说明 MCP 名称。

## 默认输出

- **目录**：用户未指定其他路径时，使用本机约定的 Obsidian vault（建议通过环境变量或 agent 配置设定，例如 `~/Obsidian`）
- **文件名**：使用文档标题 + `.md`；若标题含 `\/:*?"<>|` 等非法字符，替换为全角或 `-`，并去掉首尾空格
- **资源目录（与笔记配对）**：与 `.md` **同 basename** 的文件夹，用于放本页引用的二进制资源（Obsidian 常见「笔记同名文件夹」习惯）：
  - 若笔记为 `~/Obsidian/SDUI调研.md`，则资源根为 `~/Obsidian/SDUI调研/`（不存在则创建）
  - 媒体文件命名：`media-001.png`、`media-002.jpg`、`media-003.mp4`… 按在文中**首次出现顺序**递增；同一 URL 只下载一次，多处引用共用同一文件名
- **Frontmatter**（在最终写入前更新）：

```yaml
---
title: "<文档标题>"
source: "<完整 URL>"
exported: "<YYYY-MM-DD>"
assets_dir: "<相对于 vault 根的路径，如 SDUI调研/>"
media_downloaded: <整数，成功落盘的媒体数>
media_failed: <整数，可选，下载失败数>
---
```

`exported` 使用对话中的 **Today** 日期。若用户指定其他 vault 路径，`assets_dir` 写**相对该 vault 根**的目录（例如 `Clippings/某标题/`）。

## MCP 调用（必读）

1. 调用 `call_mcp_tool` 前，读取 **`user-code-generate-mcp-server`** / **`feishu_reader`** 的 JSON schema，确认参数无误后再调用。
2. 使用 **`feishu_reader`**：
   - `feishuUrls`：完整链接数组（一条也用数组）
   - `todo_prompt`：在下列**固定中文模板**上，仅可按「多篇序号」微调，**不得删减**与图片/视频相关的句子：

> 请输出该文档的完整正文，使用标准 Markdown：保留标题层级(# ## ###)、列表、表格、代码块与链接；**保留所有图片与视频的原链接**（包括 `![](url)`、`![alt](url)`、裸写的 `http(s)://...` 图片/视频地址、以及飞书 `open.feishu.cn/open-apis/drive/v1/medias/.../download` 等媒体链接），不要改成纯文字描述；不要省略章节。若文末有「图片资源列表」或类似清单，请**原样保留**其中的 Token 与 URL，便于后续下载。不要附加「用户要求」复述；不要输出「图片保存目录」这句固定提示（其它技术说明可保留）。

   - `depth`：有嵌套子文档时用 `2`，否则 `1`

3. 若 `feishu_reader` 不可用：可试 **`user-feishu2md`** / **`get_document_info`** 取元信息并告知用户正文/媒体需换网络或权限。

## 清洗 MCP 返回正文

从返回文本中只保留**文档本体**：

- 删除开头：`# 飞书文档 N`、`- URL:`、`- 标题:`、`文档内容:` 等包装行
- 删除尾部：从 `# 用户要求：` 起至文末的**任务复述**；**单独成行**的 `**图片保存目录**: ...` 若仅为 MCP 占位提示可删；若正文内「图片资源列表」属于**文档内容**则**保留**，待媒体处理后再视情况精简（见下）
- 表格内 `<br/>` / `<br>`：改为空格或换行

## 媒体提取与 Markdown 改写（必做）

在写入 `.md` 之前或之后（推荐**先**落盘临时正文再改写，避免超长 diff），对**清洗后的正文**执行：

### 1) 收集候选 URL

用正则/手工扫描收集（去重）：

- Markdown 图片：`!\[.*?\]\((https?://[^)]+)\)`
- Markdown 链接指向常见静态后缀：`\[.*?\]\((https?://[^)]+\.(png|jpe?g|gif|webp|svg|bmp|ico|mp4|webm|mov|m4v))\)`（大小写不敏感）
- 裸 URL 行内：`https://prod-files-secure\.[^)\s]+\.(png|jpe?g|webp|gif)` 等
- 飞书开放平台媒体：`https://open\.feishu\.cn/open-apis/drive/v1/medias/[^/\s]+/download`
- `feishu_reader` 返回的「图片资源列表」中的 Token：若能拼出可下载 URL 或与正文 URL 对应，一并纳入；**无法匿名下载**时记入 `media_failed` 并在正文保留原链接

### 2) 下载到 `assets_dir`

- 创建目录：`<vault>/<与 md 同名的文件夹>/`（见上文约定）
- 对每个 URL：`curl -fL --connect-timeout 15 --max-time 120 -o "<vault>/<笔记名>/media-NNN.<ext>" "<URL>"`（或等价的 `fetch`/Node），根据 `Content-Type` 或 URL 推断扩展名；无法推断时先用 `.bin`，再在 Markdown 里用链接而非图片嵌入
- **403/401**：保留远程 URL，不强行替换；在 frontmatter `media_failed` 或文末 HTML 注释中记录一行原因（勿写敏感 token 全文，可截断）
- **体积**：单文件默认跳过 **> 80MB**（可在用户指令中覆盖阈值）；跳过时在注释中说明

### 3) 改写正文中的引用

将已下载成功的 URL 全部替换为**相对于 `.md` 文件**的 Obsidian 友好路径（与「笔记同名文件夹」一致）：

- 图片：优先 `![[笔记文件夹名/media-001.png]]`（wikilink），或与用户 vault 习惯一致时用 `![](笔记文件夹名/media-001.png)`；**同一 vault 内二选一，全篇统一**
- 视频：优先 `![[笔记文件夹名/media-003.mp4]]`；若 Obsidian 版本/embed 不支持，退化为 `[视频](笔记文件夹名/media-003.mp4)` 或 `<video controls src="笔记文件夹名/media-003.mp4" width="100%"></video>`（仅当用户习惯 HTML）

替换完成后，可删除纯清单型的「图片资源列表」段落（若信息与 `media-*` 文件名已冗余）；若仍含未下载项，保留清单并标注「需登录后下载」。

### 4) 与 `html_to_image` 的关系

仅当正文含**需渲染成图**的 HTML 片段且无现成图片 URL、且 **`user-feishu2md` / `html_to_image`** 可用时，才调用生成 PNG，再把返回的 URL 走一遍「下载 → 落盘 → 改写」。不要为普通飞书插图主动调用。

## 写入与验收

- 使用 `Write` 写入 `<Obsidian vault>/<文件名>.md`（及已创建的媒体目录与文件）
- 覆盖同名文件前：Glob 检查并征得用户确认或改名（与旧版规则一致）
- 回复中文：**笔记绝对路径**、**资源目录路径**、成功/失败媒体数量、原文链接

## 用户覆盖配置

若用户指定 vault 子目录（如 `Clippings/`）或自定义 `assets` 目录名，以用户指令为准，并写入 frontmatter `assets_dir` / `note`。

## 不要做

- 不把企业内网正文或媒体**上传**到公开第三方
- 不省略权限/下载失败信息；如实说明 403 与是否需要本机飞书登录态
