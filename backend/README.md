# ERP Agentic Chatbot Backend

A robust, scalable FastAPI backend for AI-powered ERP interactions.

## Features

- **🔐 API Key Authentication** - Secure endpoints with API key validation
- **📚 Swagger Documentation** - Interactive API documentation at `/docs`
- **🤖 Multi-LLM Support** - Switch between OpenAI, Gemini, Anthropic via env config (LiteLLM)
- **🗄️ MongoDB Storage** - NoSQL database for company/project data
- **🏢 Multi-tenant** - Support for multiple companies and projects
- **🎯 Smart Project Selection** - AI automatically detects which project you're asking about
- **⚡ Latency Optimized** - Async operations, connection pooling, response caching
- **🐳 Docker Ready** - Containerized deployment with docker-compose

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ERP System    │────▶│  Init API       │────▶│    MongoDB      │
│   (on login)    │     │  /api/init      │     │  (Projects)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│   User Query    │────▶│  Chat API       │──────────────┘
│                 │     │  /api/chat      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Project  │ │   API    │ │   Data   │
              │Selection │ │Selection │ │Interpret │
              │  (LLM)   │ │  (LLM)   │ │  (LLM)   │
              └──────────┘ └──────────┘ └──────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ ERP API  │ │ ERP API  │ │ ERP API  │
              │  Call 1  │ │  Call 2  │ │  Call N  │
              └──────────┘ └──────────┘ └──────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB (local or Docker)
- API key for LLM provider (Gemini, OpenAI, or Anthropic)

### Installation

1. **Clone and navigate:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start MongoDB** (if not using Docker):
```bash
mongod --dbpath /path/to/data
```

6. **Run the server:**
```bash
uvicorn main:app --reload
```

7. **Access documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | **Required** - API key for authentication | - |
| `LLM_MODEL` | LLM model identifier | `gemini/gemini-2.0-flash` |
| `LLM_API_KEY` | **Required** - API key for LLM provider | - |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `ERP_BASE_URL` | **Required** - Base URL for ERP APIs | - |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `DEBUG` | Enable debug mode | `false` |

### Supported LLM Models

LiteLLM supports 100+ LLM providers. Common examples:

```bash
# OpenAI
LLM_MODEL=gpt-4
LLM_MODEL=gpt-3.5-turbo

# Google Gemini
LLM_MODEL=gemini/gemini-2.0-flash
LLM_MODEL=gemini/gemini-pro

# Anthropic
LLM_MODEL=claude-3-opus
LLM_MODEL=claude-3-sonnet

# Azure OpenAI
LLM_MODEL=azure/gpt-4
```

## API Endpoints

### Authentication

All endpoints (except `/health`) require API key authentication:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/chat
```

### Core Endpoints

#### Initialize Company
```bash
POST /api/init
Content-Type: application/json
X-API-Key: your-api-key

{
  "company_id": "88",
  "company_name": "Acme Construction",
  "force_refresh": false
}
```

#### Chat Query
```bash
POST /api/chat
Content-Type: application/json
X-API-Key: your-api-key

{
  "query": "Show me all outstanding supplier payments",
  "company_id": "88",
  "project_id": null  // Optional - auto-detected if not provided
}
```

#### List APIs
```bash
GET /api/apis
X-API-Key: your-api-key
```

#### Get Company
```bash
GET /api/companies/{company_id}
X-API-Key: your-api-key
```

### Response Format

```json
{
  "success": true,
  "response": "## Summary\n\nYou have 5 outstanding payments...",
  "project": {
    "id": "165",
    "name": "Downtown Office Complex"
  },
  "selected_apis": [...],
  "processing_time_ms": 1234.56
}
```

## Project Selection Logic

The system automatically selects the appropriate project based on:

1. **Explicit mention** - User mentions project name in query
2. **Keywords** - Match against project keywords/aliases
3. **Context** - Use conversation context if available
4. **Default project** - Fall back to company's default project

If the system cannot determine the project with confidence, it prompts the user:

```json
{
  "success": false,
  "needs_clarification": true,
  "response": "Please specify which project: Downtown Office, Riverside Residential, or Highway Mall?",
  "alternative_projects": ["Downtown Office", "Riverside Residential", "Highway Mall"]
}
```

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "error": {
    "message": "Project clarification needed"
  },
  "needs_clarification": true,
  "status_code": 400
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing API key |
| 403 | Forbidden - Invalid API key |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Performance Optimization

### Latency Reduction Strategies

1. **Parallel API Calls** - Multiple ERP API calls execute concurrently
2. **Connection Pooling** - Reuse HTTP connections with `httpx`
3. **Response Caching** - Cache LLM responses for identical queries
4. **Async Operations** - All I/O operations are async
5. **HTTP/2 Support** - Enabled for multiplexing

### Caching

LLM responses are cached based on:
- Query content
- Selected model
- TTL (configurable, default 5 minutes)

Disable caching per-request or globally:
```bash
ENABLE_CACHE=false
```

## Security

### API Key Generation

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Rate Limiting

Default: 100 requests per 60 seconds per API key

Configure via environment:
```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Best Practices

- Use HTTPS in production
- Rotate API keys regularly
- Use separate API keys for different environments
- Enable rate limiting

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

## Directory Structure

```
backend/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-container orchestration
├── middleware/
│   ├── __init__.py
│   └── auth.py          # API key authentication
├── models/
│   ├── __init__.py
│   ├── api_catalog.py   # API definition models
│   └── company.py       # Company/Project models
├── services/
│   ├── __init__.py
│   ├── agent_service.py # Main orchestration
│   ├── llm_service.py   # LiteLLM integration
│   ├── api_caller.py    # ERP API client
│   └── database.py      # MongoDB operations
├── data/
│   └── api_catalog.json # API definitions
└── nginx/
    └── nginx.conf       # Reverse proxy config
```

## Extending the API Catalog

Add new ERP APIs to `data/api_catalog.json`:

```json
{
  "apis": [
    {
      "id": "new_api_endpoint",
      "name": "New API",
      "description": "Description for AI to understand when to use this API",
      "endpoint": "/api/endpoint",
      "method": "GET",
      "parameters": [
        {
          "name": "projectId",
          "type": "query",
          "description": "Project ID",
          "required": true
        }
      ],
      "tags": ["category1", "category2"],
      "examples": [
        "Example query that would use this API",
        "Another example query"
      ],
      "response_description": "What this API returns"
    }
  ]
}
```

## License

MIT
