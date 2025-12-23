# Disable Email Verification in Supabase

To disable email verification so users can login immediately after signup, you need to configure this in the Supabase Dashboard.

## Step-by-Step Instructions

### 1. Go to Supabase Dashboard
- Navigate to: https://supabase.com/dashboard/project/skfizxuvxenrltqdwkha
- Make sure you're logged in

### 2. Disable Email Confirmation
- Click **"Authentication"** in the left sidebar
- Click **"Providers"** tab
- Find **"Email"** provider section
- Look for **"Confirm email"** toggle/checkbox
- **Turn it OFF** (disable it)

### 3. Allow Unverified Email Sign In
- Still in **Authentication** → **Settings** (or **Configuration**)
- Find **"Allow unverified email sign in"** option
- **Enable it** (turn it ON)
- This allows users to login even if email is not verified

### 4. Save Changes
- Click **"Save"** button at the bottom

## What This Does

- ✅ Users can sign up and login immediately
- ✅ No email verification required
- ✅ No blocking of login for unverified emails
- ✅ Accounts work right away
- ✅ No verification emails sent

## After Making Changes

1. Changes take effect **immediately**
2. **Existing accounts** can login without verification
3. **New accounts** can login immediately after signup
4. No need to restart the app

## Alternative: Using Supabase CLI (if you have it)

If you have Supabase CLI installed, you can also update the config:

```bash
supabase auth settings update --enable-signup=true --enable-email-confirmations=false
```

But the dashboard method is the easiest and most reliable.

