import unittest
from unittest.mock import patch, MagicMock
from app import app, db, EmailTicket
from services.ai_service import analyse_email

class BasicTests(unittest.TestCase):
    
    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        
        # Setup application context and DB
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # --- 1. Validation Testing ---
    def test_home_post_missing_data(self):
        """Test validation: missing email body"""
        response = self.app.post('/', data={
            "customer_email": "test@test.com",
            "subject": "Missing body"
            # body is intentionally omitted
        }, follow_redirects=True)
        
        # Should cleanly redirect and not add a ticket
        ticket_count = EmailTicket.query.count()
        self.assertEqual(ticket_count, 0)

    def test_home_post_valid_data(self):
        """Test routing and database insertion for valid manual input"""
        response = self.app.post('/', data={
            "customer_email": "success@test.com",
            "subject": "Valid Subject",
            "body": "Valid body",
        }, follow_redirects=True)
        
        ticket = EmailTicket.query.filter_by(customer_email="success@test.com").first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.subject, "Valid Subject")
        self.assertEqual(ticket.body, "Valid body")

    # --- 2. Intent Mapping / AI Parsing Testing ---
    @patch("services.ai_service.client.models.generate_content")
    def test_analyse_email_valid_json(self, mock_generate):
        """Test intent mapping with a valid AI response including markdown syntax"""
        mock_response = MagicMock()
        mock_response.text = '''```json\n{"intent": "refund", "sentiment": "negative", "priority": "high", "draft_reply": "Here is your refund."}\n```'''
        mock_generate.return_value = mock_response
        
        result = analyse_email("I want a refund!")
        self.assertEqual(result["intent"], "refund")
        self.assertEqual(result["sentiment"], "negative")
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["draft_reply"], "Here is your refund.")

    @patch("services.ai_service.client.models.generate_content")
    def test_analyse_email_fallback(self, mock_generate):
        """Test fallback mapping when AI returns completely invalid JSON"""
        mock_response = MagicMock()
        mock_response.text = "Error, I couldn't understand that."
        mock_generate.return_value = mock_response
        
        result = analyse_email("Unknown text format")
        self.assertEqual(result["intent"], "general inquiry")
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["priority"], "medium")
        self.assertTrue("Thank you for reaching out" in result["draft_reply"])

    # --- 3. Database Routing (Dashboard & Filtering) ---
    def test_dashboard_renders(self):
        """Test that dashboard loads successfully with active url query filters"""
        ticket = EmailTicket(
            customer_email="filter@test.com",
            subject="Looking for priority",
            body="body test",
            priority="High"
        )
        db.session.add(ticket)
        db.session.commit()
        
        # 1. Generic load contains the new ticket
        response = self.app.get('/dashboard')
        self.assertIn(b"filter@test.com", response.data)
        
        # 2. Filter match logic works
        response = self.app.get('/dashboard?priority=High')
        self.assertIn(b"filter@test.com", response.data)
        
        # 3. Filter exclusion logic works
        response = self.app.get('/dashboard?priority=Low')
        self.assertNotIn(b"filter@test.com", response.data)

if __name__ == '__main__':
    unittest.main()
