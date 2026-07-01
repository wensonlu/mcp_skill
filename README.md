# Feishu MCP 部署包

本目录包含 `feishu-mcp` 的完整部署源码，用于在 Linux 服务器上以 MCP 协议暴露飞书文档能力给 AI Agent。

## 目录结构

```
feishu-mcp-package/
├── README.md                          # 本文件
├── DEPLOYMENT.md                      # 完整的部署接入文档
├── DEPLOY-PROMPT.md                   # 一键部署的 AI Prompt
├── scripts/
│   └── run.sh                         # feishu-mcp 启动脚本
└── config/
    ├── feishu-mcp.service             # systemd 服务文件
    └── nginx-feishu-mcp.conf          # Nginx 反向代理配置
```

## 文件说明

| 文件 | 部署到服务器的位置 | 用途 |
|------|-------------------|------|
| `scripts/run.sh` | `/opt/feishu-mcp/run.sh` | feishu-mcp 启动入口 |
| `config/feishu-mcp.service` | `/etc/systemd/system/feishu-mcp.service` | systemd 服务定义 |
| `config/nginx-feishu-mcp.conf` | `/etc/nginx/conf.d/feishu-mcp.conf` | Nginx 反向代理 |

## 部署方式

### 方式一：阅读 DEPLOYMENT.md 手动部署
参见 `DEPLOYMENT.md`，包含详细的步骤说明。

### 方式二：把 DEPLOY-PROMPT.md 发给 AI
复制 `DEPLOY-PROMPT.md` 内容，替换占位符后发给 AI Agent，它会自动完成部署。

## 部署后的访问地址

```
http://<服务器IP>/feishu-mcp
```

Claude Code 配置示例：

```bash
claude mcp add -s user --transport http feishu-mcp http://<服务器IP>/feishu-mcp
```

## 服务管理命令

```bash
systemctl status feishu-mcp      # 查看状态
systemctl restart feishu-mcp     # 重启
journalctl -u feishu-mcp -f      # 实时日志
curl http://<IP>/feishu-mcp/health   # 健康检查
```

## ⚠️ 安全提示

本仓库使用占位符 `<FEISHU_APP_ID>` 和 `<FEISHU_APP_SECRET>`，**不要提交真实的 App ID 和 App Secret 到 Git**。GitHub 会自动拒绝含有真实密钥的 commit。

## License

MIT
