import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def analyse_email(email_body):
    prompt=f"""
        Analyze the following cutomer email and return a STRICT JSON.
        Allowerd intents:
        - refund
        - complain
        - delivery issue
        - cancellation
        - general inquiry
        Sentiment must be:
        - positive
        - neutral
        - negative
        Priority rules:
        - negative sentiment = high
        - neutral = medium
        - positive = low
        Return format for json:
        {{{
            "intent":"...",
            "sentiment":"...",
            "priority":"...",
            "draft_reply":"..."
        }}}
        Email:
        {email_body}
        """
    
    response = model.generate_content(prompt)
    content = response.text or ""

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "intent": "general inquiry",
            "sentiment": "neutral",
            "priority": "medium",
            "draft_reply": "Thank you for reaching out. Our support team will get back to you shortly."
        }