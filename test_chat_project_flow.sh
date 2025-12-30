#!/bin/bash

# Test script for Chat API Flow with automatic project selection
# This demonstrates:
# 1. Client sends only: query, session_id, company_id
# 2. LLM fetches projects via Bootstrap API
# 3. LLM selects appropriate project_id
# 4. LLM calls relevant project-specific APIs
# 5. LLM generates final response

BASE_URL="http://localhost:8000"
SESSION_ID="test-project-flow-$(date +%s)"
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
echo "🧪 Testing Chat API with Project Selection"
echo "========================================="
echo "📍 Base URL: $BASE_URL"
echo "🔑 API Key: ${API_KEY:0:10}..."
echo "🏢 Company ID: $COMPANY_ID"
echo "💬 Session ID: $SESSION_ID"
echo "========================================="
echo ""

# Test 1: Query with explicit project name
echo "─────────────────────────────────────────"
echo "🔄 Test 1: Query with project name mentioned"
echo "─────────────────────────────────────────"
echo "👤 User: Show me outstanding supplier payments for Paradise apartments"
echo ""

RESPONSE1=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Show me outstanding supplier payments for Paradise apartments\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data, indent=2))"
echo ""
echo "📋 Extracted fields:"
echo "$RESPONSE1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Success: {data.get('success')}')
print(f\"   Project: {data.get('project')}\")
print(f\"   Selected APIs: {len(data.get('selected_apis', []))} API(s)\")
print(f\"   Needs Clarification: {data.get('needs_clarification')}\")
print(f\"   Processing Time: {data.get('processing_time_ms')} ms\")
"
echo ""

sleep 3

# Test 2: Query without explicit project (ambiguous)
echo "─────────────────────────────────────────"
echo "🔄 Test 2: Ambiguous query (no project mentioned)"
echo "─────────────────────────────────────────"
echo "👤 User: What are today's expenses?"
echo ""

RESPONSE2=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are today's expenses?\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response'))"
echo ""
echo "📋 Extracted fields:"
echo "$RESPONSE2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Success: {data.get('success')}\")
print(f\"   Project: {data.get('project')}\")
print(f\"   Needs Clarification: {data.get('needs_clarification')}\")
if data.get('alternative_projects'):
    print(f\"   Alternative Projects: {data.get('alternative_projects')}\")
"
echo ""

sleep 3

# Test 3: Query with different project
echo "─────────────────────────────────────────"
echo "🔄 Test 3: Query with different project name"
echo "─────────────────────────────────────────"
echo "👤 User: Show me contractor cashflow for Elanza project"
echo ""

RESPONSE3=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Show me contractor cashflow for Elanza project\",
    \"company_id\": \"$COMPANY_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "🤖 Assistant:"
echo "$RESPONSE3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response'))"
echo ""
echo "📋 Extracted fields:"
echo "$RESPONSE3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Success: {data.get('success')}\")
print(f\"   Project: {data.get('project')}\")
print(f\"   Selected APIs: {len(data.get('selected_apis', []))} API(s)\")
"
echo ""

echo "========================================="
echo "✅ Test completed!"
echo "========================================="
echo ""
echo "📊 Expected Behavior:"
echo "   ✓ Test 1: Should detect 'Paradise apartments' project"
echo "   ✓ Test 2: May ask for clarification or use default project"
echo "   ✓ Test 3: Should detect 'Elanza' project"
echo ""
echo "🔍 Verify that:"
echo "   - Bootstrap API was called to fetch projects"
echo "   - LLM selected appropriate project_id"
echo "   - Relevant APIs were called with project context"
echo "   - Natural language response was generated"
echo ""

