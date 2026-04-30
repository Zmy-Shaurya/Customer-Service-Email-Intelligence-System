# Installation & Setup Guide

This guide covers how to set up MailIQ on your local machine for development and testing.

## Prerequisites
*   Python 3.10 or higher.
*   A Google Cloud Console account.

## 1. Google Cloud Setup (OAuth & Gmail)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Gmail API**.
4. Configure the **OAuth Consent Screen** (set it to internal or add your test email as a test user).
5. Go to **Credentials** -> **Create Credentials** -> **OAuth client ID** (Application type: Desktop App).
6. Download the JSON file and rename it to `credentials.json`. Place it in the root folder of this project.

## 2. Gemini API Setup
1. Go to Google AI Studio ([aistudio.google.com](https://aistudio.google.com/)).
2. Generate an API Key. Keep this ready for the `.env` file.

## 3. Local Project Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Customer-Service-Email-Intelligence-System.git
   cd Customer-Service-Email-Intelligence-System
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the Virtual Environment:**
   * **Windows:** `.venv\Scripts\activate`
   * **Mac/Linux:** `source .venv/bin/activate`

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables:**
   Create a `.env` file in the root folder and add the following:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=super-secret-key-change-in-production
   ```

## 4. Running the Application

Start the Flask development server:
```bash
python app.py
```

The first time you run the application or trigger Gmail Sync, a browser window will pop up asking you to log into your Google Account to authorize the app. Once authorized, a `token.json` file will be generated locally.

Open your browser and navigate to `http://127.0.0.1:5000` to access the dashboard.

## Cloud Deployment
If you are looking to push this application to production on Render, please consult the `DEPLOYMENT_GUIDE.md` file.
