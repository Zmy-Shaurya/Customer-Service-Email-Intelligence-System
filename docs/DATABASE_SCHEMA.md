# Database Schema

The MailIQ application utilizes SQLAlchemy as an Object Relational Mapper (ORM), allowing seamless switching between SQLite (for local development) and PostgreSQL (for production on Render).

## Relational Design Overview

The database is built around a standard **One-to-Many** architecture to support conversation threading. 

Instead of treating every incoming email as an isolated incident, the system groups back-and-forth emails between a customer and the support team into a single "Ticket" container.

---

## 1. `EmailTicket` Model
This model acts as the parent container for a specific customer issue. It holds metadata, AI classifications, and the overall status of the problem.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (Primary Key) | Unique identifier for the ticket. |
| `gmail_id` | String | The Gmail ID of the initial email that created this ticket. |
| `gmail_thread_id` | String | The Gmail Thread ID. Critical for grouping future replies. |
| `customer_email` | String | The email address of the customer. |
| `subject` | String | The subject line of the email thread. |
| `status` | String | Current state (New, In Progress, Pending Customer, Resolved). Default: "New". |
| `sentiment` | String | AI-generated sentiment (positive, neutral, negative). |
| `priority` | String | AI-generated priority (high, medium, low). |
| `intent` | String | AI-generated category (Refund, Technical Support, etc). |
| `ai_draft_reply` | Text | AI-generated suggested response for the agent. |
| `created_at` | DateTime | Timestamp of when the ticket was first opened. |

---

## 2. `TicketMessage` Model
This model represents individual emails (messages) inside a ticket. It is linked to `EmailTicket` via a foreign key.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (Primary Key) | Unique identifier for the message. |
| `ticket_id` | Integer (Foreign Key) | Links to `EmailTicket.id`. |
| `sender` | String | Indicates who sent the message (either "customer" or "agent"). |
| `body` | Text | The actual text content of the email. |
| `created_at` | DateTime | Timestamp of when the message was sent/received. |

**Relationship Properties:**
The `EmailTicket` model defines a `messages` relationship to `TicketMessage` with `lazy='joined'` and an `order_by="TicketMessage.created_at"`. This ensures that whenever a ticket is loaded from the database, its entire chat history is automatically fetched and sorted chronologically.

---

## 3. `User` Model
This model represents the internal Support Agents who log into the dashboard. It hooks directly into Flask-Login.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (Primary Key) | Unique identifier for the agent. |
| `username` | String (Unique) | The agent's login username. |
| `password_hash` | String | Bcrypt-hashed password. |
