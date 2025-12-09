# 📧 Email Troubleshooting Guide

## ❌ Error: "535, 5.7.8 Username and Password not accepted"

This error means Gmail is rejecting your credentials. **You CANNOT use your regular Gmail password** - you must use an App Password.

## ✅ Solution: Generate Gmail App Password

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Complete the 2FA setup

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Sign in to your Google Account
3. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or select "Other" and name it "PharmaGenie")
4. Click **Generate**
5. Google will show you a 16-character password like: `abcd efgh ijkl mnop`

### Step 3: Update Your .env File
1. Open `.env` file in your project root
2. Copy the 16-character App Password (remove spaces)
3. Update the `SENDER_PASSWORD` line:
   ```
   SENDER_PASSWORD=abcdefghijklmnop
   ```
4. Save the file

### Step 4: Restart the Application
1. Stop your Streamlit app (Ctrl+C in terminal)
2. Restart it:
   ```powershell
   streamlit run app.py
   ```

## 🔍 Verify It Works

1. Go to **Email Reports** page in the app
2. Click **Test Email Connection**
3. You should see: ✅ "Successfully connected to SMTP server and authenticated"

## ⚠️ Common Mistakes

| Problem | Solution |
|---------|----------|
| Using regular Gmail password | Must use App Password from Google |
| Spaces in App Password | Remove all spaces: `abcd efgh` → `abcdefgh` |
| 2FA not enabled | Enable 2-Factor Authentication first |
| Old/expired App Password | Generate a new one |
| .env file not saved | Save the file and restart app |

## 🔐 Security Notes

- **NEVER** commit your `.env` file to Git
- App Passwords are safer than your main password
- You can revoke App Passwords anytime at [App Passwords](https://myaccount.google.com/apppasswords)
- Each app should have its own App Password

## 📱 Alternative: Use a Different Email Provider

If you don't want to use Gmail, you can use other providers:

### Outlook/Hotmail
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=your_email@outlook.com
SENDER_PASSWORD=your_outlook_password
```

### Yahoo Mail
```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SENDER_EMAIL=your_email@yahoo.com
SENDER_PASSWORD=your_yahoo_app_password
```

## 🆘 Still Having Issues?

1. **Check your internet connection**
2. **Verify the email address is correct** in `SENDER_EMAIL`
3. **Try generating a new App Password**
4. **Check if Gmail is blocking the connection**:
   - Go to [Recent Security Activity](https://myaccount.google.com/notifications)
   - Look for blocked sign-in attempts
5. **Ensure port 587 is not blocked** by your firewall

## 📞 Need More Help?

- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [App Passwords Help](https://support.google.com/accounts/answer/185833)
- Check the error message in the app for specific guidance
