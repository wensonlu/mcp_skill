---
# 飞书 MCP 部署 Prompt
# 用法：把此内容发给 AI Agent，它会自动完成飞书 MCP 的部署
# 替换以下占位符：
#   <服务器IP>     — 你的云服务器公网 IP
#   <SSH密码>      — root 密码
#   <AppID>        — 飞书应用 App ID
#   <AppSecret>    — 飞书应用 App Secret
---

## 任务：部署飞书 MCP 到服务器

请帮我把 feishu-mcp 部署到一台腾讯云服务器上，让 Claude Code 可以通过 MCP 协议读写飞书文档。

### 服务器信息
- IP: <服务器IP>
- 端口: 22
- 用户: root
- 密码: <SSH密码>
- 系统: OpenCloudOS 9.4（CentOS 系）

### 飞书应用凭证
- App ID: <AppID>
- App Secret: <AppSecret>

### 部署要求

1. **安装 Node.js 20+**
   ```bash
   dnf install -y nodejs
   ```

2. **创建启动脚本** `/opt/feishu-mcp/run.sh`：
   ```bash
   #!/bin/bash
   export PATH=/usr/bin:/usr/local/bin:$PATH
   /usr/bin/npx -y feishu-mcp@latest \
     --feishu-app-id=<AppID> \
     --feishu-app-secret=<AppSecret> \
     --feishu-auth-type=tenant \
     --enabled-modules=document \
     --port 3333 \
     --feishu-scope-validation=false
   ```
   然后 `chmod +x /opt/feishu-mcp/run.sh`

3. **配置 systemd 服务** `/etc/systemd/system/feishu-mcp.service`：
   ```ini
   [Unit]
   Description=Feishu MCP Server
   After=network.target
   [Service]
   Type=simple
   ExecStart=/opt/feishu-mcp/run.sh
   Restart=always
   RestartSec=5
   User=root
   Environment=NODE_ENV=production
   Environment=PATH=/usr/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/root/bin
   [Install]
   WantedBy=multi-user.target
   ```
   然后 `systemctl daemon-reload && systemctl enable feishu-mcp && systemctl start feishu-mcp`

4. **配置 Nginx 反向代理**（让 MCP 通过 80 端口以 `/feishu-mcp` 路径访问）：

   安装 nginx：`dnf install -y nginx`

   创建 `/etc/nginx/conf.d/feishu-mcp.conf`：
   ```nginx
   server {
       listen 80;
       server_name _;
       location = /feishu-mcp/health {
           access_log off;
           return 200 "OK";
           add_header Content-Type text/plain;
       }
       location /feishu-mcp {
           proxy_pass http://127.0.0.1:3333/mcp;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header Connection "";
           proxy_buffering off;
           proxy_cache off;
           chunked_transfer_encoding on;
           proxy_read_timeout 86400s;
       }
   }
   ```
   然后 `nginx -t && systemctl enable nginx && systemctl start nginx`

5. **验证所有服务都正常运行**：
   - `systemctl is-active feishu-mcp` → active
   - `systemctl is-active nginx` → active
   - `ss -tlnp | grep 3333` → 在监听
   - `curl -s http://localhost:3333/mcp` → 有响应（含 MCP 协议错误码正常）
   - 从本机 `curl http://<服务器IP>/feishu-mcp/health` → OK

6. **如果更新了 App Secret**，记得清缓存再重启：
   ```bash
   rm -rf /root/.cache/feishu-mcp/*
   systemctl restart feishu-mcp
   ```

7. **配置到 Claude Code**（在本地执行）：
   ```bash
   claude mcp remove feishu-mcp -s user 2>/dev/null
   claude mcp add -s user --transport http feishu-mcp http://<服务器IP>/feishu-mcp
   ```

### 最终验证

运行 `claude mcp list`，应显示：
```
feishu-mcp: http://<服务器IP>/feishu-mcp (HTTP) - ✔ Connected
```
