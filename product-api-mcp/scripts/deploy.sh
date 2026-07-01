#!/bin/bash
# 商品 API + MCP Server 一键部署脚本
# 用法: ./deploy.sh
set -e

DEPLOY_DIR="/opt/product-api-mcp"
SERVICE_DIR="/etc/systemd/system"

echo "==== 1. 创建部署目录 ===="
mkdir -p $DEPLOY_DIR

echo "==== 2. 复制代码 ===="
cp main.py mcp_server.py requirements.txt $DEPLOY_DIR/
chmod +x scripts/run.sh

echo "==== 3. 安装依赖 ===="
pip3 install -r requirements.txt

echo "==== 4. 创建 htpasswd（Basic Auth） ===="
read -p "请输入商品 API 账号: " API_USER
read -s -p "请输入商品 API 密码: " API_PASS
echo ""
htpasswd -c -b /etc/nginx/.htpasswd "$API_USER" "$API_PASS"

echo "==== 5. 部署 systemd 服务 ===="
sed "s/YOUR_PASSWORD_HERE/$API_PASS/g" config/product-api.service > $SERVICE_DIR/product-api.service
sed "s/YOUR_PASSWORD_HERE/$API_PASS/g" config/product-api-mcp.service > $SERVICE_DIR/product-api-mcp.service
systemctl daemon-reload
systemctl enable --now product-api
systemctl enable --now product-api-mcp

echo "==== 6. 配置 Nginx ===="
cat config/nginx-product-api-mcp.conf >> /etc/nginx/conf.d/feishu-mcp.conf
nginx -t && systemctl reload nginx

echo "==== 7. 验证 ===="
sleep 2
systemctl status product-api --no-pager | head -5
echo "---"
systemctl status product-api-mcp --no-pager | head -5
echo "---"
curl -s -o /dev/null -w "商品 API: HTTP %{http_code}\n" -u "$API_USER:$API_PASS" http://localhost/api/products
curl -s -o /dev/null -w "MCP SSE:  HTTP %{http_code}\n" http://localhost/mcp/events

echo ""
echo "==== 部署完成 ===="
echo "商品 API:    http://YOUR_SERVER_IP/api/products"
echo "Swagger UI:  http://YOUR_SERVER_IP/docs"
echo "MCP SSE:     http://YOUR_SERVER_IP/mcp/events"
echo "MCP Message: http://YOUR_SERVER_IP/mcp/message"
echo ""
echo "Claude Code CLI 接入配置 .mcp.json："
cat << EOF
{
  "mcpServers": {
    "product-api-mcp": {
      "type": "sse",
      "url": "http://YOUR_SERVER_IP/mcp/events"
    }
  }
}
EOF
