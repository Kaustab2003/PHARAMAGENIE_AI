# 🔒 Security Setup Guide

## ⚠️ CRITICAL: API Key Leak Response

Your OpenAI API key was leaked to GitHub. Follow these steps immediately:

## 1. Get New API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Delete the compromised key (if not already disabled)
3. Create a new API key
4. Copy it immediately (you won't see it again)

### Patent API Key (if needed)
Your patent API key was also exposed. Get a new one if you're using it.

### Gmail App Password (if needed)
Your Gmail app password was exposed. Generate a new one:
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new app password
3. Use this in your `.env` file

## 2. Update Your Local `.env` File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your NEW keys
# NEVER commit this file to Git!
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-proj-YOUR-NEW-KEY-HERE
CLINICAL_TRIALS_API_KEY=your_key_here
PATENT_API_KEY=your_new_patent_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_new_app_password_here
DEBUG=True
```

## 3. Remove `.env` from Git (Already Done)

The `.env` file has been removed from Git tracking. Now commit and push:

```powershell
# Check status
git status

# Add the updated .env.example
git add .env.example

# Commit changes
git commit -m "Update-env-example-remove-secrets"

# Push to GitHub
git push origin main
```

## 4. Deploy to Render

### Option A: Environment Variables (RECOMMENDED)

1. Go to your Render dashboard: https://dashboard.render.com/
2. Select your service
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Add each variable:
   - `OPENAI_API_KEY` = your new key
   - `CLINICAL_TRIALS_API_KEY` = your key
   - `PATENT_API_KEY` = your key
   - `SMTP_SERVER` = smtp.gmail.com
   - `SMTP_PORT` = 587
   - `SENDER_EMAIL` = your email
   - `SENDER_PASSWORD` = your app password
   - `DEBUG` = True
6. Click **Save Changes**
7. Render will automatically redeploy

### Option B: Secret Files

1. In Render dashboard → **Environment** → **Secret Files**
2. Click **Add Secret File**
3. Filename: `.env`
4. Contents: Paste your environment variables
5. Save

## 5. Verify Security

### Check `.gitignore` is working:
```powershell
# This should show .env is ignored
git status

# This should return nothing (file not tracked)
git ls-files .env
```

### Before every commit:
```powershell
# Always check what you're committing
git status
git diff

# Make sure no sensitive files are included
```

## 6. Best Practices Going Forward

✅ **DO:**
- Keep `.env` in `.gitignore`
- Use `.env.example` with placeholder values
- Use environment variables in production (Render)
- Rotate API keys regularly
- Use different keys for development and production

❌ **DON'T:**
- Never commit `.env` files
- Never hardcode API keys in code
- Never share API keys in chat/email
- Never push secrets to public repositories

## 7. Monitor Your API Usage

### OpenAI
- Check usage: https://platform.openai.com/usage
- Set spending limits: https://platform.openai.com/account/billing/limits

### Enable Alerts
Set up usage alerts to detect unauthorized usage quickly.

## 8. If Keys Are Leaked Again

1. **Immediately** disable the key in the provider's dashboard
2. Generate a new key
3. Update all environments (local, Render, etc.)
4. Review Git history to ensure no keys are committed
5. Consider using `git filter-branch` to remove keys from history if needed

## Need Help?

- OpenAI Support: https://help.openai.com/
- Render Support: https://render.com/docs
- GitHub Security: https://docs.github.com/en/code-security

---

**Remember:** Security is not a one-time setup. Always be vigilant about what you commit to Git!
