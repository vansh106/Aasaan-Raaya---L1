# ERP Agentic AI Chatbot

An intelligent AI-powered chatbot that dynamically queries ERP APIs based on natural language questions. Built with FastAPI, React, and Google Gemini.

## 🌟 Features

- **Intelligent API Selection**: Uses Gemini AI to automatically select the most relevant APIs based on user queries
- **Real-time Data Fetching**: Dynamically calls ERP APIs with appropriate parameters
- **Natural Language Responses**: Interprets API data and provides human-readable answers
- **Extensible API Catalog**: Easy to add new APIs to the system
- **Modern UI**: Beautiful, responsive chat interface built with React and Tailwind CSS

## 🏗️ Architecture

### Workflow

1. **User Query** → User asks a question in natural language
2. **API Selection** → Gemini analyzes the query and selects relevant APIs from the catalog
3. **Data Fetching** → System calls selected APIs with appropriate parameters
4. **Data Interpretation** → Gemini interprets the API responses
5. **Response** → User receives a natural language answer

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Google Gemini (LLM for agent logic)
- Pydantic (Data validation)
- HTTPX (Async HTTP client)

**Frontend:**
- React 18 with TypeScript
- Vite (Build tool)
- Tailwind CSS (Styling)
- Axios (HTTP client)

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API Key
- Access to ERP APIs with valid credentials

## 🚀 Installation & Setup

### Backend Setup

1. **Navigate to backend directory:**
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

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ERP_BASE_URL=https://dev.l.pocketconstructionmanager.com
   ERP_COOKIE_XSRF_TOKEN=your_xsrf_token
   ERP_COOKIE_SESSION=your_session_cookie
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

5. **Run the backend server:**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## 📖 Usage

### Using the Chatbot

1. Open the frontend at `http://localhost:5173`
2. Type your question in the chat input
3. Examples:
   - "Show me all outstanding supplier payments"
   - "What is the total amount owed to suppliers?"
   - "List all invoices from Alpha Structures"
   - "How much have we paid to contractors?"
   - "Which invoices are overdue?"

### Adding New APIs to the Catalog

Edit `backend/data/api_catalog.json` and add your API definition:

```json
{
  "id": "your_api_id",
  "name": "Human Readable Name",
  "description": "Detailed description of what this API does and when to use it",
  "endpoint": "/your-api-endpoint",
  "method": "GET",
  "parameters": [
    {
      "name": "param_name",
      "type": "query",
      "description": "Parameter description",
      "required": true,
      "example": "example_value"
    }
  ],
  "tags": ["tag1", "tag2"],
  "examples": [
    "Example question 1",
    "Example question 2"
  ],
  "response_description": "Description of the response data structure"
}
```

**Parameter Types:**
- `query` - URL query parameter
- `path` - Path parameter (e.g., `/users/{id}`)
- `form` - Form data
- `body` - JSON body

**HTTP Methods:**
- `GET`, `POST`, `PUT`, `DELETE`, `PATCH`

### API Endpoints

**Backend API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Main Endpoints:**
- `POST /api/chat` - Send a chat message
- `GET /api/apis` - List all available APIs
- `POST /api/apis` - Add a new API to catalog
- `GET /health` - Health check

## 🔧 Configuration

### Backend Configuration (`backend/config.py`)

The backend uses Pydantic Settings for configuration management. All settings can be configured via environment variables:

- `GEMINI_API_KEY` - Your Google Gemini API key
- `ERP_BASE_URL` - Base URL of your ERP system
- `ERP_COOKIE_XSRF_TOKEN` - XSRF token for authentication
- `ERP_COOKIE_SESSION` - Session cookie for authentication
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)

### API Catalog Structure

The API catalog (`backend/data/api_catalog.json`) contains all available APIs. Each API definition includes:

- Metadata (id, name, description)
- Endpoint and HTTP method
- Parameter definitions
- Tags for categorization
- Example use cases
- Response description

## 🧠 How It Works

### Agent Service

The `AgentService` orchestrates the entire workflow:

1. **Load API Catalog**: Loads available APIs from `api_catalog.json`
2. **Process Query**: 
   - Converts catalog to dict format
   - Calls Gemini to select relevant APIs
   - Extracts/infers parameter values
3. **Call APIs**: Makes HTTP requests to selected endpoints
4. **Interpret Results**: Uses Gemini to generate natural language response

### Gemini Service

The `GeminiService` handles all LLM interactions:

- **API Selection**: Analyzes user query against API catalog
- **Data Interpretation**: Converts API responses to natural language
- **Parameter Inference**: Extracts parameter values from queries

### API Caller Service

The `APICallerService` handles dynamic API calls:

- Builds URLs with path parameters
- Separates query, form, and body parameters
- Handles authentication headers
- Returns structured responses

## 📝 Project Structure

```
Aasaan-raya/
├── backend/
│   ├── data/
│   │   └── api_catalog.json       # API definitions
│   ├── models/
│   │   └── api_catalog.py         # Pydantic models
│   ├── services/
│   │   ├── agent_service.py       # Main orchestration
│   │   ├── gemini_service.py      # LLM integration
│   │   └── api_caller.py          # API calling logic
│   ├── config.py                  # Configuration
│   ├── main.py                    # FastAPI app
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx  # Main chat UI
│   │   │   ├── Header.tsx         # App header
│   │   │   └── Message.tsx        # Message component
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript types
│   │   ├── App.tsx                # Root component
│   │   ├── main.tsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── package.json              # Node dependencies
│   └── vite.config.ts            # Vite configuration
└── README.md                      # This file
```

## 🔐 Security Notes

- Store API credentials securely in `.env` files
- Never commit `.env` files to version control
- Use environment-specific configurations
- Implement proper authentication in production
- Validate all user inputs
- Use HTTPS in production

## 🚀 Deployment

### Backend Deployment

1. Set up a production server (AWS, GCP, Azure, etc.)
2. Configure environment variables
3. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
4. Set up reverse proxy (Nginx/Apache)
5. Enable HTTPS

### Frontend Deployment

1. Build the production bundle:
   ```bash
   npm run build
   ```
2. Deploy the `dist` folder to:
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - Any static hosting service

3. Update `VITE_API_BASE_URL` to production backend URL

## 🤝 Contributing

To add more ERP APIs:

1. Document the API endpoint, parameters, and response
2. Add the API definition to `api_catalog.json`
3. Test with sample queries
4. Update the documentation

## 📄 License

MIT License - feel free to use this project for your needs.

## 🐛 Troubleshooting

### Backend Issues

**Issue**: Import errors
- **Solution**: Make sure you're in the virtual environment and all dependencies are installed

**Issue**: CORS errors
- **Solution**: Check CORS_ORIGINS in .env includes your frontend URL

**Issue**: API calls failing
- **Solution**: Verify ERP credentials are correct in .env

### Frontend Issues

**Issue**: API connection failed
- **Solution**: Ensure backend is running and VITE_API_BASE_URL is correct

**Issue**: Build errors
- **Solution**: Delete node_modules and package-lock.json, then run `npm install` again

## 📞 Support

For issues or questions, please check:
1. The troubleshooting section above
2. Backend API documentation at `/docs`
3. Console logs for error messages

## 🎯 Future Enhancements

- [ ] Multi-turn conversations with context
- [ ] Support for authentication flows
- [ ] API response caching
- [ ] Advanced query understanding
- [ ] Export chat history
- [ ] Voice input support
- [ ] Multi-language support
- [ ] Analytics dashboard


