# MCP Skills 仓库

本仓库收集各种 MCP（Model Context Protocol）服务器部署包。

## 目录结构

每个 MCP 作为独立的子目录组织：

```
mcp_skill/
├── README.md                # 本文件
├── feishu/                  # 飞书 MCP - 文档读写
│   ├── README.md
│   ├── DEPLOYMENT.md
│   ├── DEPLOY-PROMPT.md
│   ├── scripts/
│   │   └── run.sh
│   └── config/
│       ├── feishu-mcp.service
│       └── nginx-feishu-mcp.conf
└── product-api-mcp/         # 商品 API MCP - 商品查询
    ├── README.md
    ├── DEPLOYMENT.md
    ├── DEPLOY-PROMPT.md
    ├── main.py
    ├── mcp_server.py
    ├── requirements.txt
    ├── scripts/
    │   ├── deploy.sh
    │   └── run.sh
    └── config/
        ├── product-api.service
        ├── product-api-mcp.service
        └── nginx-product-api-mcp.conf
```

## 已收录的 MCP

| MCP | 路径 | 功能 | 状态 |
|-----|------|------|------|
| 飞书 | [`feishu/`](./feishu/) | 飞书文档搜索/读取/创建/编辑 | ✅ 已完成 |
| 商品 API | [`product-api-mcp/`](./product-api-mcp/) | 商品列表/详情查询 | ✅ 已完成 |

## 通用规范

每个 MCP 子目录都包含：

- `README.md` - 快速介绍
- `DEPLOYMENT.md` - 完整部署文档
- `DEPLOY-PROMPT.md` - AI 一键部署 Prompt
- `scripts/` - 启动脚本
- `config/` - 系统配置（systemd / nginx 等）

## 安全规范

- **不提交任何真实凭证**（App ID / App Secret / Token 等）
- 使用 `<FEISHU_APP_ID>` 这样的占位符
- 真实配置存放在服务器本地，不进版本控制
