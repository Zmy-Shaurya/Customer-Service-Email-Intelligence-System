# AI Processing Pipeline

Steps:

1. Email is received (manual or Gmail sync)
2. Stored in database
3. Background thread processes email
4. AI generates:
   - intent
   - sentiment
   - priority
   - draft reply
5. Ticket is updated

Failure Handling:
- Errors logged
- Ticket remains unchanged
