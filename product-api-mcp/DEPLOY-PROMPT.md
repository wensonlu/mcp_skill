# 商品 API MCP 部署 Prompt
# 用法：把此内容发给 AI Agent，它会自动完成商品 API MCP 的部署
# 替换以下占位符：
#   <服务器IP>     — 你的云服务器公网 IP
#   <SSH密码>      — root 密码
#   <API账号>      — Basic Auth 用户名（如 docs）
#   <API密码>      — Basic Auth + JWT 登录密码
---

## 任务：部署 product-api-mcp 到服务器

请帮我把 product-api-mcp（FastAPI 商品接口 + MCP Server）部署到一台腾讯云服务器上，让 Claude Code CLI 可以通过 MCP 协议查询商品信息。

### 服务器信息
- IP: <服务器IP>
- 端口: 22
- 用户: root
- 密码: <SSH密码>
- 系统: OpenCloudOS 9.4（CentOS 系）

### 部署内容
1. FastAPI 商品接口（端口 8000）— 需要 Basic Auth
2. MCP Server（端口 8765）— AI 客户端直接调用，无需额外认证
3. Nginx 反向代理（端口 80）— 统一入口

### 部署步骤

1. **安装依赖**
   ```bash
   ssh root@<服务器IP>
   pip3 install -r requirements.txt
   ```

2. **创建 Basic Auth 用户**
   ```bash
   htpasswd -c -b /etc/nginx/.htpasswd <API账号> <API密码>
   ```

3. **部署代码到 /opt/product-api-mcp**
   ```bash
   mkdir -p /opt/product-api-mcp
   cp -r main.py mcp_server.py requirements.txt scripts config /opt/product-api-mcp/
   ```

4. **配置 systemd 服务**（替换 YOUR_PASSWORD_HERE 为真实密码）
   ```bash
   sed 's/YOUR_PASSWORD_HERE/<API密码>/g' config/product-api-mcp.service > /etc/systemd/system/product-api-mcp.service
   sed 's/YOUR_PASSWORD_HERE/<API密码>/g' config/product-api.service > /etc/systemd/system/product-api.service
   systemctl daemon-reload
   systemctl enable --now product-api
   systemctl enable --now product-api-mcp
   ```

5. **配置 Nginx**（追加到现有 feishu-mcp.conf 的 server 块中）
   ```bash
   cat config/nginx-product-api-mcp.conf >> /etc/nginx/conf.d/feishu-mcp.conf
   nginx -t && systemctl reload nginx
   ```

6. **验证**
   ```bash
   systemctl status product-api product-api-mcp --no-pager
   curl -u <API账号>:<API密码> http://localhost/api/products | head -10
   curl -sN http://localhost/mcp/events | head -5
   ```

### 部署完成标志
- `systemctl status product-api` 显示 active (running)
- `systemctl status product-api-mcp` 显示 active (running)
- 8765 端口和 8000 端口都有监听
- `http://<服务器IP>/api/products` 用 Basic Auth 可访问
- `http://<服务器IP>/mcp/events` SSE 流可连接

### Claude Code CLI 接入配置
部署完成后，告知用户在项目根目录创建 `.mcp.json`：
```json
{
  "mcpServers": {
    "product-api-mcp": {
      "type": "sse",
      "url": "http://<服务器IP>/mcp/events"
    }
  }
}
```

### 提供的 MCP 工具
- `get_products` - 商品列表查询
- `get_product_detail` - 商品详情
- `get_openapi_spec` - OpenAPI 规范

### 注意事项
- 代码已脱敏，所有 `YOUR_SERVER_IP` 和 `YOUR_PASSWORD_HERE` 占位符部署时必须替换
- 凭证统一管理：htpasswd（Basic Auth）= MCP_AUTH_PASSWORD（JWT 登录）= 商品 API JWT 登录密码
- 部署完成后建议立即测试所有 MCP 工具
