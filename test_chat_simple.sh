#!/bin/bash

# Simple bash script to test chat session management
# This reads the API key from the backend's .env if needed

BASE_URL="http://localhost:8000"
SESSION_ID="test-session-$(date +%s)"
COMPANY_ID="88"

# Try to read API key from backend .env
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# If API_KEY still not set, prompt user
if [ -z "$API_KEY" ]; then
    echo "❌ API_KEY not found in environment or backend/.env"
    echo "Please set it: export API_KEY='your-key'"
    exit 1
fi

echo "========================================="
echo "🧪 Testing Chat Session Management"
echo "========================================="
echo "📍 Base URL: $BASE_URL"
echo "🔑 API Key: ${API_KEY:0:10}..."
echo "🏢 Company ID: $COMPANY_ID"
echo "💬 Session ID: $SESSION_ID"
echo "========================================="
echo ""

# Test 1: First message with context setup
echo "─────────────────────────────────────────"
echo "🔄 Message 1: Setting context"
echo "─────────────────────────────────────────"
echo "👤 User: My name is Alice and I like the number 42"
echo ""

RESPONSE1=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"My name is Alice and I like the number 42\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response'))"
echo ""

sleep 3

# Test 2: Query that requires context from message 1
echo "─────────────────────────────────────────"
echo "🔄 Message 2: Testing context memory"
echo "─────────────────────────────────────────"
echo "👤 User: What is my name?"
echo ""

RESPONSE2=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What is my name?\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response'))"
echo ""

sleep 3

# Test 3: Another context query
echo "─────────────────────────────────────────"
echo "🔄 Message 3: Testing number recall"
echo "─────────────────────────────────────────"
echo "👤 User: What number did I say I like?"
echo ""

RESPONSE3=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What number did I say I like?\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response'))"
echo ""

echo "========================================="
echo "✅ Test completed!"
echo "========================================="
echo ""
echo "📊 Verification:"
echo "   - Response 2 should mention 'Alice'"
echo "   - Response 3 should mention '42'"
echo ""
echo "🔍 Check database:"
echo "   MongoDB: db.chat_sessions.find({session_id: '$SESSION_ID'})"
echo "   Redis: LRANGE chat:session:$SESSION_ID:buffer 0 -1"
echo ""

