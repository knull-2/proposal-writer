@echo off
cd /d "C:\Users\Ravi prakash\proposal-writer"
call venv\Scripts\activate
set GEMINI_API_KEY=AIzaSyYour-actual-key-here
echo Starting AI Proposal Writer...
start http://localhost:8000
uvicorn main:app --port 8000