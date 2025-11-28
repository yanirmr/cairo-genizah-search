# ⚡ QUICK START - Deploy in 30 Minutes

**TL;DR:** Get your Cairo Genizah Search app live on the internet in 30 minutes!

---

## 🎯 What You'll Do

1. Push code to GitHub (5 min)
2. Deploy on Render.com (5 min)
3. Upload data & build index (20 min)
4. Your app is live! 🎉

---

## 📝 Before You Start

**You need:**
- ✅ GitHub account (sign up at [github.com](https://github.com))
- ✅ 30 minutes of time
- ✅ Credit card for Render (free tier available, but paid tier recommended at $7/month)

**Already done:**
- ✅ Code is ready in: `C:\Users\Yanir\Dropbox\Projects\cairo_genizah_search`
- ✅ Git repository initialized
- ✅ All files committed

---

## 🚀 Step 1: Push to GitHub (5 minutes)

### 1.1 Create Repository

- Go to [github.com](https://github.com)
- Click **"+"** → **"New repository"**
- Name: `cairo-genizah-search`
- Click **"Create repository"**

### 1.2 Push Code

Open terminal in your project folder:

```bash
cd C:\Users\Yanir\Dropbox\Projects\cairo_genizah_search

# Replace YOUR-USERNAME with your GitHub username
git remote add origin https://github.com/YOUR-USERNAME/cairo-genizah-search.git
git branch -M main
git push -u origin main
```

✅ **Done!** Your code is on GitHub.

---

## 🌐 Step 2: Deploy on Render (5 minutes)

### 2.1 Sign Up

- Go to [render.com](https://render.com)
- Click **"Sign up with GitHub"**
- Authorize Render

### 2.2 Create Web Service

- Click **"New +"** → **"Web Service"**
- Connect `cairo-genizah-search` repository
- Render auto-detects everything!

### 2.3 Choose Plan

**Recommended:** Select **"Starter"** ($7/month)
- Always on
- 1 GB RAM
- Perfect for this app

**Or:** Select **"Free"** (for testing)
- Sleeps after 15 min
- Takes 30 sec to wake up

### 2.4 Deploy

- Click **"Create Web Service"**
- Wait 2-3 minutes
- ✅ App is deployed (but index not built yet)

---

## 📁 Step 3: Upload Data File (5 minutes)

### 3.1 Open Shell

- In Render dashboard, click **"Shell"** tab
- Browser terminal opens

### 3.2 Upload File

**If you can host the file online:**
```bash
curl -O https://your-url/GenizaTranscriptions.txt
```

**Otherwise:**
- Use Render's file upload feature in Shell
- Upload `GenizaTranscriptions.txt` (takes ~5 min)

### 3.3 Verify

```bash
ls -lh GenizaTranscriptions.txt
```

✅ Should show ~390 MB file

---

## 🔨 Step 4: Build Index (15 minutes)

In the Render Shell:

```bash
python -m genizah_search.indexer --input GenizaTranscriptions.txt --output index/
```

**Wait 10-15 minutes** while it indexes 162,198 documents.

You'll see progress updates:
```
Indexed 100/162198 documents...
Indexed 200/162198 documents...
...
Successfully indexed 162198 documents!
```

✅ **Done!** Index is built.

---

## ✅ Step 5: Test Your App! (2 minutes)

Your app URL (from Render dashboard):
`https://genizah-search.onrender.com`

**Test these:**

1. **Homepage:** Open your app URL
   - ✅ Should see search page

2. **Search:** Enter `שבת` and search
   - ✅ Should get results

3. **Stats:** Click "Statistics" in menu
   - ✅ Should show "Total Documents: 162,198"

4. **API:** Visit `/api/stats`
   - ✅ Should return JSON

---

## 🎉 SUCCESS!

**Your app is live at:**
`https://your-app.onrender.com`

**Share it with:**
- Colleagues
- Researchers
- Anyone interested in Cairo Genizah

---

## 🔄 To Update Later

Make changes, then:

```bash
git add .
git commit -m "Your changes"
git push
```

Render automatically redeploys! 🚀

---

## ⚡ Super Quick Reference

**Timeline:**
- ⏱️ 5 min: GitHub
- ⏱️ 5 min: Deploy
- ⏱️ 5 min: Upload
- ⏱️ 15 min: Index
- ⏱️ 2 min: Test
- **Total: 32 minutes**

**Cost:**
- 💰 Free tier: $0
- 💰 Starter tier: $7/month (recommended)

**What you get:**
- 🌐 Live web app
- 🔍 162,198 searchable documents
- 📱 Works on any device
- 🔌 RESTful API
- 🇮🇱 Hebrew/Arabic support

---

## 📞 Stuck?

Check **DEPLOYMENT_CHECKLIST.md** for detailed troubleshooting!

---

*Deploy now and start searching the Cairo Genizah!* 📚✨
