import os
import   json
from google import  genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MY_GEMINI_MODEL = "gemini-2.5-flash-lite" 
def analyse_email(email_body):
    prompt=f"""
        Analyze the following customer email and return a STRICT JSON.
        Allowed intents:
        -refund
        -complain
        -delivery issue
        - cancellation
        -general inquiry
        --promotional
        Sentiment must be:
        - positive
        -neutral
        -negative
        Priority rules:
        -negative sentiment= high
        - neutral= medium
        -positive= low
        Return format for json:
        {{
            "intent":"...",
            "sentiment":"...",
            "priority":"...",
            "draft_reply":"..."
        }}
        Email:
        {email_body}
        """
    
    response = client.models.generate_content(model=MY_GEMINI_MODEL, contents=prompt)
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