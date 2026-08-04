call venv\Scripts\activate
cd server
call python -m debugpy --listen 0.0.0.0:5678 -m uvicorn main:root --port 80
pause
