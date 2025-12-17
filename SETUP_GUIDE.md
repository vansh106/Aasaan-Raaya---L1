# Setup Guide - ERP Agentic AI Chatbot

Complete step-by-step guide to get the chatbot running.

## Prerequisites

Before you begin, ensure you have:

- [x] Python 3.10 or higher installed
- [x] Node.js 18 or higher installed
- [x] Google Gemini API key ([Get one here](https://ai.google.dev/))
- [x] Access to your ERP system APIs
- [x] Valid ERP authentication cookies

## Step 1: Get Gemini API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy the key (you'll need it later)

## Step 2: Get ERP Authentication Credentials

1. Open your ERP system in a browser
2. Log in to your account
3. Open Developer Tools (F12)
4. Go to Network tab
5. Make any request to the ERP
6. Find the request and copy these headers:
   - `XSRF-TOKEN` cookie value
   - `pocket_construction_manager_session` cookie value
7. Save these values (you'll need them later)

## Step 3: Clone/Download the Project

```bash
cd ~/Desktop
# Project should be at: ~/Desktop/Aasaan-raya
```

## Step 4: Backend Setup

### 4.1 Create Virtual Environment

```bash
cd Aasaan-raya/backend
python3 -m venv venv
```

### 4.2 Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 4.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI
- Uvicorn
- Pydantic
- Google Generative AI SDK
- HTTPX
- And other dependencies

### 4.4 Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your favorite editor:

```bash
nano .env  # or vim, code, etc.
```

Update these values:

```env
GEMINI_API_KEY=AIza...your_actual_gemini_key
ERP_BASE_URL=https://dev.l.pocketconstructionmanager.com
ERP_COOKIE_XSRF_TOKEN=your_xsrf_token_value
ERP_COOKIE_SESSION=your_session_cookie_value
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Important Notes:**
- Replace `AIza...your_actual_gemini_key` with your actual Gemini API key
- Replace `your_xsrf_token_value` with the XSRF-TOKEN cookie from Step 2
- Replace `your_session_cookie_value` with the session cookie from Step 2
- Keep the cookie values WITHOUT the `XSRF-TOKEN=` or cookie name prefix
- Don't add quotes around the values

### 4.5 Verify Backend Setup

Check that all files are in place:

```bash
ls -la
# Should see: main.py, config.py, requirements.txt, .env, etc.

ls -la data/
# Should see: api_catalog.json

ls -la services/
# Should see: agent_service.py, gemini_service.py, api_caller.py
```

### 4.6 Start Backend Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 4.7 Test Backend

Open a new terminal and test:

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","apis_loaded":1}

# List APIs
curl http://localhost:8000/api/apis
```

Leave the backend running and proceed to frontend setup.

## Step 5: Frontend Setup

### 5.1 Open New Terminal

Keep the backend running in the first terminal. Open a new terminal window/tab.

### 5.2 Navigate to Frontend Directory

```bash
cd ~/Desktop/Aasaan-raya/frontend
```

### 5.3 Install Node Dependencies

```bash
npm install
```

This will install:
- React
- TypeScript
- Vite
- Tailwind CSS
- Axios
- And other dependencies

Wait for installation to complete (may take 2-3 minutes).

### 5.4 Configure Frontend Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Set the backend URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 5.5 Start Frontend Development Server

```bash
npm run dev
```

You should see:

```
  VITE v5.0.12  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  press h to show help
```

## Step 6: Test the Application

### 6.1 Open Browser

Navigate to: http://localhost:5173

You should see:
- Header: "ERP AI Assistant"
- Chat interface with a welcome message
- Input field at the bottom

### 6.2 Test with Sample Queries

Try these queries:

1. **Simple query:**
   ```
   Show me all supplier payables
   ```

2. **Specific query:**
   ```
   What is the total amount owed to suppliers?
   ```

3. **Filtered query:**
   ```
   List all invoices from Alpha Structures
   ```

4. **Analysis query:**
   ```
   Which invoices are overdue?
   ```

### 6.3 Verify the Response

The chatbot should:
1. Show "Thinking..." indicator
2. Display which API was selected
3. Provide a natural language answer
4. Show the response in a formatted message

## Step 7: Verify Everything Works

### Backend Checklist

- [ ] Backend server is running on port 8000
- [ ] `/health` endpoint returns success
- [ ] No errors in backend terminal
- [ ] Gemini API key is valid
- [ ] ERP cookies are valid

### Frontend Checklist

- [ ] Frontend server is running on port 5173
- [ ] Chat interface loads properly
- [ ] Can send messages
- [ ] Receives responses from backend
- [ ] No CORS errors in browser console

## Troubleshooting

### Backend Issues

**Issue: Import errors**
```
Solution:
1. Activate virtual environment
2. Reinstall dependencies: pip install -r requirements.txt
```

**Issue: Gemini API error**
```
Solution:
1. Check GEMINI_API_KEY in .env
2. Verify key at https://ai.google.dev/
3. Check API quota/limits
```

**Issue: ERP API returns 401/403**
```
Solution:
1. Refresh ERP cookies (they expire)
2. Log in to ERP again
3. Copy new cookie values
4. Update .env file
5. Restart backend server
```

**Issue: Module not found**
```
Solution:
1. Make sure you're in backend directory
2. Check virtual environment is activated
3. Run: pip install -r requirements.txt
```

### Frontend Issues

**Issue: npm install fails**
```
Solution:
1. Delete node_modules: rm -rf node_modules
2. Delete package-lock.json: rm package-lock.json
3. Run: npm install
```

**Issue: CORS error in browser**
```
Solution:
1. Check backend CORS_ORIGINS includes http://localhost:5173
2. Restart backend server
3. Clear browser cache
```

**Issue: Can't connect to backend**
```
Solution:
1. Verify backend is running
2. Check VITE_API_BASE_URL in frontend/.env
3. Test backend directly: curl http://localhost:8000/health
```

**Issue: Build errors**
```
Solution:
1. Check TypeScript errors
2. Run: npm run build
3. Fix any errors shown
```

## Next Steps

### Add More APIs

1. Edit `backend/data/api_catalog.json`
2. Add new API definitions
3. Restart backend server
4. Test with relevant queries

### Customize the UI

1. Edit `frontend/tailwind.config.js` for colors
2. Modify components in `frontend/src/components/`
3. Changes hot-reload automatically

### Deploy to Production

See main README.md for deployment instructions.

## Common Questions

**Q: How long do ERP cookies last?**
A: Typically 24 hours. You'll need to refresh them daily.

**Q: Can I add multiple ERP systems?**
A: Yes, modify the API caller service to support multiple base URLs.

**Q: Is Gemini API free?**
A: Gemini has a free tier with rate limits. Check Google AI pricing.

**Q: Can I use a different LLM?**
A: Yes, replace GeminiService with your preferred LLM API.

**Q: How do I update the API catalog?**
A: Edit `backend/data/api_catalog.json` and restart the backend.

## Getting Help

1. Check the troubleshooting section above
2. Review backend logs in terminal
3. Check browser console for errors
4. Review API documentation at http://localhost:8000/docs

## Success!

If you've completed all steps and the chatbot is responding to queries, congratulations! You've successfully set up the ERP Agentic AI Chatbot.

Try experimenting with different queries and adding more APIs to the catalog.


