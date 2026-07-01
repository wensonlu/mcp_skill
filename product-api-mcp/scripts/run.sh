#!/bin/bash
# Product API MCP Server 启动脚本
# 部署路径: /opt/product-api-mcp/run.sh
export PATH=/usr/bin:/usr/local/bin:$PATH
cd /opt/product-api-mcp
exec /usr/local/bin/uvicorn mcp_server:app --host 0.0.0.0 --port 8765
