#!/bin/bash
export PATH=/usr/bin:/usr/local/bin:$PATH
/usr/bin/npx -y feishu-mcp@latest \
  --feishu-app-id=<FEISHU_APP_ID> \
  --feishu-app-secret=<FEISHU_APP_SECRET> \
  --feishu-auth-type=tenant \
  --enabled-modules=document \
  --port 3333 \
  --feishu-scope-validation=false
