@echo off
cd /d "C:\Users\Ravi prakash\proposal-writer"
call venv\Scripts\activate
set GEMINI_API_KEY=AIzaSyBTS4S3-BJbwjhh-ojhRxhoowpJd7V2JAs
echo Starting AI Proposal Writer Pro...
start http://localhost:8000
uvicorn main:app --port 8000
pause