# Complete Render Deployment Guide

This guide walks you through deploying the Customer Service Email Intelligence System onto **Render**, a professional cloud hosting platform.

Our application has been upgraded to automatically read environment variables and build necessary system files (like your Gmail tokens) on the fly, making it 100% compatible with Render's ephemeral storage system.

---

## Prerequisites

1.  **A GitHub Account:** Your code needs to be pushed to a repository on GitHub.
2.  **A Render Account:** Sign up for free at [render.com](https://render.com).
3.  **Local Configuration Files:** You should have your `token.json` and `credentials.json` files on your local computer from when you authenticated Gmail locally.

⚠️ **WARNING:** Never push `.env`, `credentials.json`, `token.json`, or the `instance/` folder to GitHub. Ensure your `.gitignore` is set up properly.

---

## Step 1: Push Code to GitHub

1.  Open your terminal in the project folder.
2.  Initialize git, add your files, and push them to a new GitHub repository:
    ```bash
    git init
    git add .
    git commit -m "Ready for Render deployment"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    git push -u origin main
    ```

---

## Step 2: Create a PostgreSQL Database on Render

To ensure your tickets and messages are never deleted, we will use a separate, permanent database server.

1.  Log into the Render Dashboard.
2.  Click **New +** and select **PostgreSQL**.
3.  Fill out the details:
    *   **Name:** `email-intelligence-db`
    *   **Region:** Choose the one closest to you.
    *   **PostgreSQL Version:** Default is fine.
    *   **Instance Type:** Free Tier.
4.  Click **Create Database**.
5.  Wait a moment for the database to provision. Once it says "Available", scroll down to the **Connections** section and copy the **Internal Database URL** (it should look something like `postgres://username:password@hostname/dbname`). Save this somewhere temporarily.

---

## Step 3: Create the Web Service

Now we will deploy the actual Flask application.

1.  Go back to the Render Dashboard, click **New +**, and select **Web Service**.
2.  Connect your GitHub account and select your project repository.
3.  Fill out the deployment settings:
    *   **Name:** `customer-service-ai`
    *   **Region:** Must be the exact same region as your database.
    *   **Branch:** `main`
    *   **Runtime:** Python 3
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `gunicorn app:app`
    *   **Instance Type:** Free Tier.

---

## Step 4: Configure Environment Variables (The Secret Sauce)

Before clicking "Create Web Service", scroll down and click **Advanced** -> **Add Environment Variable**. This is where we inject all your secrets so the app can build your Gmail tokens on the fly.

Add the following variables:

1.  **Key:** `DATABASE_URL`
    *   **Value:** Paste the Internal Database URL you copied in Step 2.
2.  **Key:** `SECRET_KEY`
    *   **Value:** Generate a random string of letters and numbers (e.g., `s8f9as7df98as7df987a`).
3.  **Key:** `GEMINI_API_KEY`
    *   **Value:** Paste your Google Gemini API Key.
4.  **Key:** `GMAIL_TOKEN_JSON`
    *   **Value:** Open your local `token.json` file in a text editor. Copy the *entire contents* (the whole JSON block) and paste it here.
5.  **Key:** `GMAIL_CREDENTIALS_JSON`
    *   **Value:** Open your local `credentials.json` file in a text editor. Copy the *entire contents* and paste it here.

---

## Step 5: Deploy & Initialize Database

1.  Click **Create Web Service** at the very bottom.
2.  Render will now download your code, run the Build Command to install packages (including the new `psycopg2-binary` required for Postgres), and then run the Start Command.
3.  Watch the deployment logs. You should see "Build Successful" followed by Gunicorn starting your workers.

### Important Final Step: Migrating the Database
Since your Postgres database is brand new and completely empty, it doesn't have the tables for `EmailTicket`, `TicketMessage`, or `User` yet. 

Render requires you to run commands using the **Shell** tab:
1.  On your Web Service page, click the **Shell** tab at the top.
2.  Once the terminal connects, run Python interactively to create the tables:
    ```bash
    python
    ```
    ```python
    from app import app, db
    with app.app_context():
        db.create_all()
    exit()
    ```
3.  *(Optional)* If you want to migrate your old SQLite data into this new database, you will need to manually write a migration script or just start fresh with the new database. Starting fresh is usually easier for projects.

---

## Step 6: Test Your Live App

Go back to the **Events** or **Logs** tab and click the blue link at the top left of your screen (e.g., `https://customer-service-ai.onrender.com`).

Your system is now live, permanently backed by PostgreSQL, and will automatically reconnect to your Gmail account on every restart!
