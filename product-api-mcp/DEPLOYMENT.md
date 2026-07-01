# 商品 API MCP 部署文档

> 将 FastAPI 商品接口通过 MCP 协议暴露给 AI Agent（Claude Code CLI），实现商品列表查询、详情获取、OpenAPI 规范访问。

---

## 一、架构总览

```
本地 Claude Code CLI / AI Agent
    │  HTTP MCP 协议 (SSE)
    ▼
http://YOUR_SERVER_IP/mcp/events
    │  Nginx (端口 80) 反向代理
    ▼
http://127.0.0.1:8765/mcp/
    │  MCP Server (mcp_server.py)
    │  内部自动 Basic Auth + JWT 登录
    ▼
http://127.0.0.1:8000/products
    │  FastAPI 商品接口 (main.py)
    ▼
返回商品数据
```

---

## 二、部署步骤

### 1. 准备服务器

- 操作系统：Linux（已测试 OpenCloudOS 9.4 / CentOS 7+ / Ubuntu 20+）
- Python 3.8+
- Nginx 1.18+
- 公网 IP 开放 80 端口

### 2. 上传代码

```bash
scp -r product-api-mcp/ root@YOUR_SERVER_IP:/opt/
```

### 3. 安装 Python 依赖

```bash
ssh root@YOUR_SERVER_IP
cd /opt/product-api-mcp
pip3 install -r requirements.txt
```

### 4. 创建 Nginx Basic Auth

```bash
htpasswd -c -b /etc/nginx/.htpasswd docs YOUR_PASSWORD_HERE
```

### 5. 部署 systemd 服务

```bash
cp config/product-api.service     /etc/systemd/system/
cp config/product-api-mcp.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now product-api
systemctl enable --now product-api-mcp
```

修改 `product-api-mcp.service` 中的 `MCP_AUTH_PASSWORD` 改为真实密码。

### 6. 配置 Nginx 反向代理

将 `config/nginx-product-api-mcp.conf` 中的 location 块追加到现有 server 块（或独立建一个 conf 文件）：

```bash
cat config/nginx-product-api-mcp.conf >> /etc/nginx/conf.d/feishu-mcp.conf
nginx -t && systemctl reload nginx
```

### 7. 验证

```bash
# 检查服务状态
systemctl status product-api product-api-mcp --no-pager

# 验证商品 API
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u docs:YOUR_PASSWORD_HERE http://localhost/api/products

# 验证 MCP SSE
curl -sN http://localhost/mcp/events
```

---

## 三、Claude Code CLI 接入

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

启动 Claude Code CLI 即可使用商品接口工具。

---

## 四、MCP 工具列表

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_products` | page, page_size, category, min_price, max_price, keyword, sort_by, sort_order, brand, is_new, is_hot, tag | 商品列表查询 |
| `get_product_detail` | product_id | 商品详情 |
| `get_openapi_spec` | 无 | 获取 OpenAPI 规范 |

---

## 五、运维命令

```bash
# 查看服务状态
systemctl status product-api
systemctl status product-api-mcp

# 查看日志
journalctl -u product-api -f
journalctl -u product-api-mcp -f

# 重启服务
systemctl restart product-api
systemctl restart product-api-mcp

# 重新加载 Nginx
nginx -t && systemctl reload nginx
```

---

## 六、故障排查

| 现象 | 排查 |
|------|------|
| MCP 连接不上 | `systemctl status product-api-mcp` / `ss -tlnp \| grep 8765` |
| 工具调用返回认证错误 | 检查 `product-api-mcp.service` 中的环境变量 |
| 商品 API 返回 401 | 检查 `/etc/nginx/.htpasswd` 是否与 `MCP_AUTH_USERNAME/PASSWORD` 一致 |
| 端口 80 不通 | 检查腾讯云安全组是否放行 |
