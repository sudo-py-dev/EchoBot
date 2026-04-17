# EchoBot Railway Deployment Guide

This guide will help you deploy EchoBot to [Railway.app](https://railway.app) using the prepared configuration.

## 1. Create a New Project
1. Go to [Railway Dashboard](https://railway.app/dashboard).
2. Click **New Project** -> **Deploy from GitHub Repo**.
3. Select your `EchoBot` repository.

## 2. Add PostgreSQL Database
1. In your Railway project canvas, click **New** -> **Database** -> **Add PostgreSQL**.
2. Wait for it to initialize. Railway automatically creates a `DATABASE_URL` variable for the project.

## 3. Configure the Bot Service
1. Click on your bot service (created from the GitHub repo).
2. Go to the **Variables** tab and add the following variables:
   *   `API_ID`: Your Telegram API ID.
   *   `API_HASH`: Your Telegram API Hash.
   *   `BOT_TOKEN`: Your Telegram Bot Token.
   *   `OWNER_IDS`: Comma-separated list of owner IDs.
   *   `DATABASE_URL`: Set this to `${{Postgres.DATABASE_URL}}` (Railway will automatically link it).
   *   `LOG_LEVEL`: `INFO` (optional).

## 4. Setup Persistent Sessions (CRITICAL)
Railway's filesystem is reset on every deploy. To avoid logging in repeatedly:
1. Go to your bot service -> **Settings**.
2. Scroll down to **Volumes** -> **Add Volume**.
3. Set the **Mount Path** to `/app/sessions`.
4. This ensures your `.session` files survive updates.

## 5. Deployment
1. Railway will automatically trigger a build once you set the variables.
2. Check the **Deployments** tab to see the progress.
3. Once the status is **Active**, check the **Logs** tab to verify the `🚀 Bot started!` message appears.

---

### Troubleshooting
- **Database Connection**: Ensure `DATABASE_URL` uses the `${{Postgres.DATABASE_URL}}` reference so it stays updated.
- **Session Lost**: If you are prompted to log in again after a restart, double-check that the Volume is correctly mounted to `/app/sessions`.
