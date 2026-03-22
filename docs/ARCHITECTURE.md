# System Architecture

Flow:

Gmail API → Fetch Emails  
→ Flask Backend → Store in DB  
→ Background Thread → AI Processing  
→ Dashboard UI  

Key Components:
- Flask routes handle requests
- SQLAlchemy manages database
- Gemini API processes email content
- Threads ensure async execution
