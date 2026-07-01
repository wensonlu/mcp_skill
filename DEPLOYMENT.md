# 飞书 MCP 部署接入文档

> 将飞书文档能力通过 MCP 协议暴露给 AI Agent（Claude Code），实现搜索、读取、创建、编辑飞书文档。
>
> 部署服务器：腾讯云 43.130.249.71 | OS: OpenCloudOS 9.4 | Node.js: v20.20.0

---

## 一、架构总览

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
飞书开放平台 API → 读写你的文档
```

## 二、准备工作

### 2.1 飞书开放平台创建应用

1. 打开 [飞书开放平台](https://open.feishu.cn) → 开发者后台
2. 创建企业自建应用（或使用已有应用）
3. 记录 **App ID** 和 **App Secret**（凭证与基础信息页面）
4. **权限管理** → 添加所需权限（至少）：
   - `docx:document` / `docx:document:readonly` — 文档读写
   - `drive:drive` / `drive:drive:readonly` — 云空间
   - `drive:file` — 文件管理
   - `search:drive:search` — 搜索文档
   - `wiki:space:read` / `wiki:wiki:readonly` — 知识库
5. **版本管理与发布** → 创建版本 → 发布（需管理员审核）

### 2.2 服务器环境要求

| 项目 | 版本/要求 |
|------|-----------|
| OS | CentOS / OpenCloudOS / Ubuntu |
| Node.js | ≥ 20.x |
| npm | ≥ 10.x |
| systemd | 用于管理服务 |
| Nginx | 用于反向代理（可选但推荐） |

---

## 三、部署步骤

### 步骤 1：安装 Node.js

```bash
# OpenCloudOS / CentOS / RHEL
dnf install -y nodejs

# Ubuntu / Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 验证
node --version    # 应 ≥ v20.x
npm --version
```

### 步骤 2：创建启动脚本

```bash
mkdir -p /opt/feishu-mcp
```

创建 `/opt/feishu-mcp/run.sh`：

```bash
#!/bin/bash
export PATH=/usr/bin:/usr/local/bin:$PATH
/usr/bin/npx -y feishu-mcp@latest \
  --feishu-app-id=<FEISHU_APP_ID> \
  --feishu-app-secret=<FEISHU_APP_SECRET> \
  --feishu-auth-type=tenant \
  --enabled-modules=document \
  --port 3333 \
  --feishu-scope-validation=false
```

```bash
chmod +x /opt/feishu-mcp/run.sh
```

> **说明**：`--feishu-scope-validation=false` 跳过了 feishu-mcp 内置的权限预检（否则即使已在开放平台开通权限，也可能因 scope 查询缓存不同步而报错），实际 API 调用使用 token 自身的权限。

### 步骤 3：配置 systemd 服务

创建 `/etc/systemd/system/feishu-mcp.service`：

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

启动：

```bash
systemctl daemon-reload
systemctl enable feishu-mcp
systemctl start feishu-mcp
systemctl status feishu-mcp     # 确认 active (running)
```

### 步骤 4：配置 Nginx 反向代理（可选但推荐）

创建 `/etc/nginx/conf.d/feishu-mcp.conf`：

```nginx
server {
    listen 80;
    server_name _;

    # 健康检查
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

```bash
nginx -t                    # 测试配置
systemctl enable nginx
systemctl start nginx
```

---

## 四、客户端配置（Claude Code）

### 4.1 添加 MCP 服务器

```bash
# 全局配置（所有项目可用）
claude mcp add -s user --transport http feishu-mcp http://<服务器IP>/feishu-mcp

# 或项目级配置
claude mcp add -s local --transport http feishu-mcp http://<服务器IP>/feishu-mcp
```

### 4.2 验证连接

```bash
claude mcp list
# 应显示: feishu-mcp → ✔ Connected
```

---

## 五、常用管理命令

### 服务端

| 命令 | 用途 |
|------|------|
| `systemctl status feishu-mcp` | 查看服务状态 |
| `systemctl restart feishu-mcp` | 重启服务 |
| `systemctl stop feishu-mcp` | 停止服务 |
| `journalctl -u feishu-mcp -f` | 实时查看日志 |
| `journalctl -u feishu-mcp -n 50` | 查看最近 50 条日志 |

### 更新 feishu-mcp 版本

重启服务即可，npx 会自动拉取最新版：

```bash
systemctl restart feishu-mcp
```

### 更换 App Secret

```bash
# 1. 修改 /opt/feishu-mcp/run.sh 中的密钥
# 2. 清除旧 token 缓存
rm -rf /root/.cache/feishu-mcp/*
# 3. 重启服务
systemctl restart feishu-mcp
```

---

## 六、排错指南

### 6.1 "app secret invalid"（错误码 10014）

**原因**：App Secret 不正确或已过期重置。

**解决**：
```bash
# 在飞书开放平台重新生成 Secret
# 更新 run.sh 后重启
systemctl restart feishu-mcp
```

### 6.2 "权限不足，缺少以下权限"

**原因**：feishu-mcp 内置权限预检发现 scope 不足。

**解决**：
1. 在飞书开放平台添加缺失的权限并重新发布版本
2. 或在启动参数加 `--feishu-scope-validation=false` 跳过预检（推荐快速方案）

### 6.3 服务启动失败（status=203/EXEC）

**原因**：ExecStart 中的命令路径不对。

**解决**：改用包装脚本方式，在脚本中 export PATH。

### 6.4 端口被占用

```bash
lsof -i :3333
kill -9 <PID>
systemctl restart feishu-mcp
```

---

## 七、安全注意

1. **永远不要把真实的 App Secret 提交到 Git 仓库**。本仓库使用 `<FEISHU_APP_ID>` 和 `<FEISHU_APP_SECRET>` 占位符。
2. GitHub 默认开启 secret scanning，会拒绝含有真实飞书 / 阿里云 / AWS 等密钥的 commit。
3. **Nginx 加 IP 白名单** 或使用 Basic Auth 保护 `/feishu-mcp` 端点，避免被公网滥用。

---

## 八、当前部署参数（参考）

| 参数 | 值 |
|------|-----|
| 服务器 IP | `<替换为你的服务器 IP>` |
| App ID | `<替换为你的 App ID>` |
| App Secret | `<替换为你的 App Secret>` |
| feishu-mcp 版本 | 0.3.2 |
| Node.js | v20.20.0 |
| 操作系统 | OpenCloudOS 9.4 |
