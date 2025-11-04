# Quick Start Guide

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] Anthropic API key (from https://console.anthropic.com/)
- [ ] GitHub Personal Access Token (from https://github.com/settings/tokens)

## 5-Minute Setup

### Step 1: Clone and Navigate
```bash
git clone <your-repo-url>
cd ai-code-modernizer
```

### Step 2: Backend Setup (2 minutes)
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Step 3: MCP Setup (1 minute)
```bash
# Install MCP servers globally
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
```

### Step 4: Frontend Setup (2 minutes)
```bash
cd ../frontend
npm install
```

## Running the Application

### Terminal 1: Start Backend
```bash
cd backend
# Make sure venv is activated
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev
```

### Access
Open your browser to: **http://localhost:5173**

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Make sure your virtual environment is activated and dependencies are installed:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: MCP servers not found
**Solution:** Install them globally:
```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
```

### Issue: Docker errors
**Solution:**
1. Make sure Docker Desktop is running
2. Check Docker is accessible: `docker ps`
3. On Windows, ensure WSL2 is properly configured

### Issue: API key errors
**Solution:**
1. Check `backend/.env` exists (copy from `.env.example`)
2. Verify API keys are correctly set
3. Ensure no extra spaces or quotes around keys

### Issue: Port already in use
**Solution:**
- Backend (8000): `lsof -ti:8000 | xargs kill -9` (macOS/Linux) or use Task Manager (Windows)
- Frontend (5173): `lsof -ti:5173 | xargs kill -9` (macOS/Linux) or use Task Manager (Windows)

## Verification

### Test Backend
```bash
curl http://localhost:8000/api/health
# Should return: {"status": "healthy"}
```

### Test Frontend
Open http://localhost:5173 in your browser - you should see the dashboard.

### Test MCP Connection
```bash
cd backend
python -c "from tools.mcp_tools import MCPToolManager; print('MCP OK')"
```

## Development Tips

### Hot Reload
Both backend and frontend support hot reload:
- **Backend**: Save Python files → FastAPI auto-restarts
- **Frontend**: Save React files → Vite auto-refreshes browser

### Debugging
- **Backend logs**: Check terminal where `uvicorn` is running
- **Frontend logs**: Open browser DevTools console (F12)
- **API requests**: Use browser Network tab or http://localhost:8000/docs (FastAPI auto-docs)

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (when implemented)
cd frontend
npm test
```

## Next Steps

1. ✅ Setup complete? → Read the implementation plan in `ai-powered-code-moderizer-platform.md`
2. 📚 Understand the architecture? → Check `PROJECT_STRUCTURE.md`
3. 🚀 Ready to code? → Start with Day 1 tasks (Foundation & MCP Setup)

## Day 1 Quick Tasks

Once setup is complete, start with these:

1. **Test MCP Tools** (30 min)
   - Create `backend/tools/mcp_tools.py`
   - Test GitHub API access
   - Test filesystem access

2. **Create Base Agent** (1 hour)
   - Create `backend/agents/base.py`
   - Test LLM connection
   - Verify tool execution

3. **First Integration Test** (30 min)
   - Create simple test agent
   - Verify end-to-end flow
   - Debug any issues

## Useful Commands

```bash
# Backend
cd backend
source venv/bin/activate          # Activate environment
uvicorn api.main:app --reload     # Run server
pytest tests/ -v                  # Run tests
pip freeze > requirements.txt     # Update dependencies

# Frontend
cd frontend
npm run dev                       # Development server
npm run build                     # Production build
npm run preview                   # Preview production build

# Docker
docker ps                         # List running containers
docker logs <container_id>        # View container logs
docker system prune -a            # Clean up (careful!)

# Git
git status                        # Check status
git add .                         # Stage all changes
git commit -m "message"           # Commit
git push                          # Push to remote
```

## Getting Help

- 📖 **Full Documentation**: See `README.md`
- 🏗️ **Architecture**: See `PROJECT_STRUCTURE.md`
- 📋 **Implementation Plan**: See `ai-powered-code-moderizer-platform.md`
- 🐛 **Issues**: Check existing setup or create GitHub issue

---

Good luck with the hackathon! 🚀
