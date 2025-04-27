# Step 1: Get session ID (adding -v for verbose output)
curl -v -N http://localhost:8931/sse

# Step 2: Once you get the session ID, use it in your request
# Replace YOUR_SESSION_ID with the ID from the response headers
curl -X POST "http://localhost:8931/sse?sessionId=YOUR_SESSION_ID" \
-H "Content-Type: application/json" \
-d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}'

# Alternative: Use single command with grep to extract session ID automatically
SESSION_ID=$(curl -v -N http://localhost:8931/sse 2>&1 | grep -o 'sessionId=[a-zA-Z0-9-]*' | cut -d'=' -f2)
