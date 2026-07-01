# 商品列表 API + MCP

> 把一个 FastAPI 商品接口包装成 MCP Server，让 AI 客户端（Claude Code CLI / Cursor 等）通过 MCP 协议直接调用，无需关心认证。

---

## 目录结构

```
product-api-mcp/
├── README.md                       # 本文件
├── DEPLOYMENT.md                   # 完整部署文档
├── DEPLOY-PROMPT.md                # AI 一键部署 Prompt
├── main.py                         # FastAPI 商品接口主程序
├── mcp_server.py                   # MCP Server（AI 网关）
├── requirements.txt                # Python 依赖
├── scripts/
│   ├── deploy.sh                   # 一键部署脚本
│   └── run.sh                      # MCP Server 启动脚本
└── config/
    ├── product-api.service         # FastAPI systemd 服务
    ├── product-api-mcp.service     # MCP Server systemd 服务
    └── nginx-product-api-mcp.conf  # Nginx 反向代理配置
```

---

## 功能特性

- **商品列表 API** — 真实电商数据结构（20 个字段），支持分页、筛选、排序
- **Swagger 文档** — 自动生成 `/docs`、`/openapi.json`
- **Basic Auth + JWT 鉴权** — 双层认证保护
- **MCP Server** — SSE 传输，自动处理认证，AI 客户端零感知
- **systemd 服务** — 开机自启，异常自动重启
- **Nginx 反向代理** — 统一管理所有路由

---

## 快速部署

```bash
# 1. 复制整个 product-api-mcp 目录到服务器
scp -r product-api-mcp/ root@YOUR_SERVER_IP:/opt/

# 2. 登录服务器执行一键部署
ssh root@YOUR_SERVER_IP
cd /opt/product-api-mcp
chmod +x scripts/*.sh
./scripts/deploy.sh
```

详细步骤见 [`DEPLOYMENT.md`](./DEPLOYMENT.md)。

---

## MCP 暴露的工具

| Tool | 作用 |
|------|------|
| `get_products` | 获取商品列表（分页、筛选、排序） |
| `get_product_detail` | 获取单个商品详情（20 个字段） |
| `get_openapi_spec` | 获取完整 OpenAPI 接口规范 |

---

## Claude Code CLI 接入

在用户项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "product-api-mcp": {
      "type": "sse",
      "url": "http://YOUR_SERVER_IP/mcp/events"
    }
  }
}
```

AI 客户端即可像调用本地工具一样使用商品接口：

```
> 帮我查一下有哪些电子产品在卖，按评分排序
> iPhone 16 Pro Max 的详细信息是什么
> 这个 API 有哪些接口？看看 openapi 规范
```

---

## 凭证配置

凭证配置在 **MCP Server 层**（systemd 环境变量），AI 客户端完全不需要知道：

| 变量 | 说明 | 示例 |
|------|------|------|
| `MCP_API_BASE` | 后端 FastAPI 地址 | `http://localhost:8000` |
| `MCP_AUTH_USERNAME` | Basic Auth + JWT 登录账号 | `docs` |
| `MCP_AUTH_PASSWORD` | Basic Auth + JWT 登录密码 | `<your password>` |

修改后重启服务生效：

```bash
systemctl restart product-api-mcp
```

---

## 安全规范

部署前请检查：

- ✅ 代码中所有 `YOUR_SERVER_IP` 已替换为真实公网 IP（仅在文档示例中保留）
- ✅ 代码中所有 `YOUR_PASSWORD_HERE` 已替换为真实密码
- ✅ 服务器 Nginx htpasswd 已创建（`htpasswd -c -b /etc/nginx/.htpasswd user pass`）
- ✅ 服务器防火墙/安全组已放行 80 端口
