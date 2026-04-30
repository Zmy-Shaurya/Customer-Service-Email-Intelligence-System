# AI Pipeline

The AI Pipeline in MailIQ acts as the "brain" of the customer service system, reading incoming emails and extracting actionable intelligence using Google Gemini 2.5 Flash.

## 1. Triggering the Pipeline

The pipeline is triggered automatically via `app.process_ticket_ai(ticket_id)` under two conditions:
1. When a totally new ticket is created via the dashboard or synced via the Gmail API.
2. When an existing ticket is updated with a new message from the customer.

To prevent blocking the main web application thread, the AI pipeline is executed asynchronously using Python's `threading.Thread(target=process_ticket_ai, args=(ticket.id,), daemon=True).start()`.

## 2. Extraction & Prompt Construction

Inside `services/ai_service.py`, the system extracts the latest message body sent by the customer. 

The system then builds a strict prompt for the Gemini LLM. The prompt mandates that the LLM returns its response exclusively in a structured JSON format to ensure programmatic consistency.

**Strict Prompt Constraints:**
*   **Intent Constraint:** The LLM MUST choose one intent from a fixed list: `Refund`, `Technical Support`, `Delivery Issue`, `General Inquiry`.
*   **Sentiment Constraint:** The LLM MUST output either `positive`, `neutral`, or `negative`.
*   **Priority Constraint:** The LLM MUST output `high`, `medium`, or `low`.

## 3. Execution & Parsing

1.  **Call to Google Gemini:** The system sends the prompt to the `gemini-2.5-flash-lite` model.
2.  **String Cleanup:** Language models often prefix JSON strings with markdown code blocks (e.g., ` ```json `). The pipeline contains regex/string stripping logic to safely remove these markdown wrappers.
3.  **JSON Decoding:** The cleaned string is parsed into a Python dictionary. If Gemini fails to return valid JSON (a rare hallucination), the `try/except` block provides a safe fallback dictionary with a `general inquiry` intent.

## 4. Database Updates

Finally, the pipeline writes the AI-extracted fields directly to the `EmailTicket` row in the database:
*   `ticket.intent = result["intent"]`
*   `ticket.sentiment = result["sentiment"]`
*   `ticket.priority = result["priority"]`
*   `ticket.ai_draft_reply = result["draft_reply"]`

Once committed, these changes are immediately reflected on the user's dashboard.
