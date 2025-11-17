Juliet - Complete (lightweight) ready for Render deployment.

Quick start (local):
  python3 -m venv .venv
  source .venv/bin/activate   (Windows: .\.venv\Scripts\activate)
  pip install -r requirements.txt
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

Deploy (Render):
  - Push this repo to GitHub with files at repo root.
  - In Render create a "Web Service" connected to this repo.
  - Build command: pip install -r requirements.txt
  - Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
  - Leave environment variables empty for now.
