#!/bin/bash

# Detailed test script to verify Redis write-behind strategy

BASE_URL="http://localhost:8000"
SESSION_ID="detailed-test-$(date +%s)"
COMPANY_ID="88"

# Load environment variables
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

if [ -z "$API_KEY" ]; then
    echo "❌ API_KEY not found"
    exit 1
fi

echo "========================================="
echo "🧪 Detailed Chat Session & Write-Behind Test"
echo "========================================="
echo "📍 Session ID: $SESSION_ID"
echo "========================================="
echo ""

# Function to check Redis buffer
check_redis_buffer() {
    local count=$(redis-cli LLEN chat:session:$SESSION_ID:buffer 2>/dev/null)
    echo "   📦 Redis buffer entries: $count"
}

# Function to check MongoDB
check_mongodb() {
    local count=$(mongosh --quiet --eval "use erp_chatbot; db.chat_sessions.findOne({session_id: '$SESSION_ID'}).messages.length" 2>/dev/null || echo "0")
    echo "   💾 MongoDB persisted messages: $count"
}

echo "─────────────────────────────────────────"
echo "🔄 Test 1: Send first message"
echo "─────────────────────────────────────────"
echo "👤 User: Remember these: color=blue, fruit=apple, city=Paris"
echo ""

RESPONSE1=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Remember these: color=blue, fruit=apple, city=Paris\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response')[:150])"
echo ""
echo "⏱️  Immediately after request:"
check_redis_buffer
check_mongodb
echo ""

echo "⏱️  Waiting 2 seconds..."
sleep 2
check_redis_buffer
check_mongodb
echo ""

echo "⏱️  Waiting 12 more seconds (total 14s, flush delay is 10s)..."
sleep 12
check_redis_buffer
check_mongodb
echo ""

echo "─────────────────────────────────────────"
echo "🔄 Test 2: Test context recall"
echo "─────────────────────────────────────────"
echo "👤 User: What color did I tell you?"
echo ""

RESPONSE2=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What color did I tell you?\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response')[:150])"
echo ""
check_redis_buffer
check_mongodb
echo ""

echo "─────────────────────────────────────────"
echo "🔄 Test 3: Test more context recall"
echo "─────────────────────────────────────────"
echo "👤 User: What fruit and city did I mention?"
echo ""

RESPONSE3=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What fruit and city did I mention?\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response')[:150])"
echo ""
check_redis_buffer
check_mongodb
echo ""

echo "⏱️  Waiting 12 seconds for final flush..."
sleep 12
check_redis_buffer
check_mongodb
echo ""

echo "========================================="
echo "✅ Test completed!"
echo "========================================="
echo ""
echo "📊 Expected behavior:"
echo "   1. Redis buffer fills immediately after each request"
echo "   2. After ~10s delay, buffer flushes to MongoDB"
echo "   3. All messages persist in MongoDB"
echo "   4. Context is maintained across all messages"
echo ""
echo "🎯 Context verification:"
echo "   - Response 2 should mention 'blue'"
echo "   - Response 3 should mention 'apple' and 'Paris'"
echo ""

