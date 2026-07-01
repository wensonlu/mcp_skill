# 飞书 MCP

通过 MCP 协议将飞书文档能力暴露给 AI Agent（Claude Code / Cursor / Windsurf 等），实现搜索、读取、创建、编辑飞书云文档。

> 📖 完整部署文档：[DEPLOYMENT.md](./DEPLOYMENT.md)
> 🤖 AI 一键部署 Prompt：[DEPLOY-PROMPT.md](./DEPLOY-PROMPT.md)

## 快速开始

```bash
# 服务器端（部署完成后）
curl http://<服务器IP>/feishu-mcp/health
# → OK

# 客户端（Claude Code）
claude mcp add -s user --transport http feishu-mcp http://<服务器IP>/feishu-mcp
claude mcp list  # 确认显示 ✔ Connected
```

## 目录结构

```
feishu/
├── README.md                # 本文件
├── DEPLOYMENT.md            # 完整部署文档
├── DEPLOY-PROMPT.md         # AI 一键部署 Prompt
├── scripts/
│   └── run.sh               # 启动脚本（含脱敏占位符）
└── config/
    ├── feishu-mcp.service   # systemd 服务定义
    └── nginx-feishu-mcp.conf # Nginx 反向代理
```

## 架构

```
本地 Claude Code
    │  HTTP MCP 协议
    ▼
http://<服务器IP>/feishu-mcp
    │  Nginx（端口 80）反向代理
    ▼
http://127.0.0.1:3333/mcp
    │  feishu-mcp 服务
    ▼
飞书开放平台 API
```

## 提供的 MCP 工具

| 工具 | 功能 |
|------|------|
| `search_feishu_documents` | 搜索云文档 |
| `get_feishu_document_info` | 获取文档基本信息 |
| `get_feishu_document_blocks` | 获取文档块结构 |
| `create_feishu_document` | 创建新文档 |
| `batch_create_feishu_blocks` | 批量创建内容块 |
| `update_feishu_block_text` | 更新文本内容 |
| `delete_feishu_document_blocks` | 删除文档块 |
| `get_feishu_folder_files` | 获取文件夹文件列表 |
| `create_feishu_folder` | 创建文件夹 |
| `get_feishu_image_resource` | 获取图片资源 |
| `get_feishu_whiteboard_content` | 获取画板内容 |
| `create_feishu_table` | 创建表格 |

## License

MIT
