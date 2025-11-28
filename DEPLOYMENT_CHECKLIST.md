# 🚀 Deployment Checklist - Cairo Genizah Search

Follow these steps in order. Check off each item as you complete it!

---

## 📋 Pre-Deployment (Already Done ✅)

- [x] Project code complete
- [x] All tests passing (61/61)
- [x] Git repository initialized
- [x] Code committed to git
- [x] Deployment files created (Procfile, render.yaml, etc.)
- [x] Large files excluded from git

---

## 🌐 Step 1: Create GitHub Account (if needed)

- [ ] Go to [github.com](https://github.com)
- [ ] Sign up for a free account (or login if you have one)
- [ ] Verify your email address

---

## 📦 Step 2: Create GitHub Repository

- [ ] Click the **"+"** button (top right) → **"New repository"**
- [ ] Repository name: `cairo-genizah-search`
- [ ] Description: `Search tool for Cairo Genizah transcriptions`
- [ ] Visibility: **Public** (or Private if you prefer)
- [ ] **DO NOT** check "Add a README" (you already have one)
- [ ] Click **"Create repository"**

---

## 💻 Step 3: Push Code to GitHub

Open your terminal/command prompt in the project directory and run:

**Windows (Command Prompt or PowerShell):**
```cmd
cd C:\Users\Yanir\Dropbox\Projects\cairo_genizah_search
```

**Then run these commands (replace YOUR-USERNAME with your actual GitHub username):**

```bash
git remote add origin https://github.com/YOUR-USERNAME/cairo-genizah-search.git
git branch -M main
git push -u origin main
```

**Checkpoint:** ✅ Verify your code is on GitHub by visiting:
`https://github.com/YOUR-USERNAME/cairo-genizah-search`

---

## 🎨 Step 4: Sign Up for Render.com

- [ ] Go to [render.com](https://render.com)
- [ ] Click **"Get Started"** or **"Sign Up"**
- [ ] Choose **"Sign up with GitHub"** (easiest option)
- [ ] Authorize Render to access your GitHub account
- [ ] Complete any profile setup

---

## 🚀 Step 5: Deploy on Render

### 5.1 Create New Web Service

- [ ] In Render dashboard, click **"New +"** button (top right)
- [ ] Select **"Web Service"**

### 5.2 Connect Repository

- [ ] Click **"Connect a repository"**
- [ ] If you don't see your repo, click **"Configure GitHub account"** and grant access
- [ ] Find `cairo-genizah-search` in the list
- [ ] Click **"Connect"**

### 5.3 Configure Service

Render will auto-fill most settings. Verify these:

- [ ] **Name:** `genizah-search` (or your preferred name)
- [ ] **Region:** Choose closest to your users (e.g., Oregon, Frankfurt)
- [ ] **Branch:** `main`
- [ ] **Runtime:** `Python 3`

**Build & Start Commands:**
Render will detect your `render.yaml` file automatically. If not, set:

- [ ] **Build Command:**
  ```
  pip install -r requirements-prod.txt
  ```

- [ ] **Start Command:**
  ```
  gunicorn -w 4 -b 0.0.0.0:$PORT genizah_search.app:app --timeout 120
  ```

### 5.4 Choose Plan

**Option A: Free Tier** (for testing)
- [ ] Select **"Free"** plan
- [ ] ⚠️ Note: App sleeps after 15 min of inactivity (takes ~30 sec to wake up)

**Option B: Paid Tier** (for production) - **RECOMMENDED**
- [ ] Select **"Starter"** plan ($7/month)
- [ ] ✅ Always on, 1GB RAM, perfect for this app

### 5.5 Advanced Settings (Optional)

- [ ] Scroll to **"Advanced"** section
- [ ] Add environment variable:
  - **Key:** `INDEX_PATH`
  - **Value:** `index/`

### 5.6 Create Service

- [ ] Click **"Create Web Service"** button at the bottom
- [ ] Wait for initial deployment (~2-3 minutes)
- [ ] Watch the deploy logs - it will install dependencies

**Checkpoint:** ✅ You should see "Deploy succeeded" or "Live" status

---

## 📁 Step 6: Upload Data File

Since the data file is too large for GitHub, you need to upload it separately:

### 6.1 Access Shell

- [ ] In your Render service dashboard, find the **"Shell"** tab (top menu)
- [ ] Click **"Shell"** - a terminal will open in your browser

### 6.2 Upload File (Choose One Method)

**Method A: Using curl (if file is hosted online)**
```bash
curl -O https://your-file-host.com/GenizaTranscriptions.txt
```

**Method B: Using Render's file upload feature**
- [ ] Look for an **"Upload File"** button in the Shell interface
- [ ] Browse to `GenizaTranscriptions.txt` on your computer
- [ ] Upload (this may take several minutes - 390 MB file)

**Method C: Using scp from your computer** (advanced)
- [ ] In Render dashboard, go to **"Connect"** tab
- [ ] Copy the SSH command
- [ ] From your computer, run:
  ```bash
  scp GenizaTranscriptions.txt <ssh-command-from-render>:~/
  ```

### 6.3 Verify Upload

In the Render Shell, run:
```bash
ls -lh GenizaTranscriptions.txt
```

- [ ] Confirm file exists and is ~390 MB

---

## 🔨 Step 7: Build the Search Index

In the Render Shell (still open from Step 6):

```bash
python -m genizah_search.indexer --input GenizaTranscriptions.txt --output index/
```

**What happens:**
- [ ] Script starts indexing 162,198 documents
- [ ] You'll see progress: "Indexed 100/162198 documents..."
- [ ] ⏰ **Wait time: 10-15 minutes** (grab a coffee!)
- [ ] Final message: "Successfully indexed 162198 documents!"
- [ ] Index size will be shown (~1.2 GB)

**Checkpoint:** ✅ Verify index was created:
```bash
ls -lh index/
```

You should see files like `MAIN_*.seg`, `*.toc`, etc.

---

## 🎉 Step 8: Test Your Deployed App!

### 8.1 Get Your App URL

- [ ] In Render dashboard, find your app URL (something like):
  `https://genizah-search.onrender.com`
- [ ] Copy this URL

### 8.2 Test the Homepage

- [ ] Open your app URL in a browser
- [ ] ✅ Verify you see the search page with "Cairo Genizah Search" title

### 8.3 Test Search Functionality

- [ ] Enter a Hebrew search term: `שבת`
- [ ] Click **"Search"**
- [ ] ✅ Verify you get results

### 8.4 Test Other Features

- [ ] Click **"Statistics"** in the nav menu
- [ ] ✅ Verify you see: "Total Documents: 162,198"

- [ ] Search for a document ID: `IE104549337`
- [ ] Change search type to **"Document ID"**
- [ ] ✅ Verify you get matching documents

### 8.5 Test API Endpoints

Open in browser or use curl:

```bash
https://your-app.onrender.com/api/stats
```

- [ ] ✅ Verify you get JSON response with statistics

```bash
https://your-app.onrender.com/api/search?q=test&type=fulltext
```

- [ ] ✅ Verify you get JSON search results

---

## 🔧 Step 9: Performance Optimization (Optional)

If your app is slow:

### 9.1 Upgrade Plan
- [ ] Upgrade to Starter plan if on Free tier

### 9.2 Increase Workers
In Render dashboard:
- [ ] Go to **"Environment"** tab
- [ ] Edit **"Start Command"** and change `-w 4` to `-w 6`:
  ```
  gunicorn -w 6 -b 0.0.0.0:$PORT genizah_search.app:app --timeout 120
  ```
- [ ] Save and redeploy

---

## 📱 Step 10: Share Your App!

Your app is now live! Share the URL:

- [ ] Add the URL to your GitHub README
- [ ] Share with colleagues/researchers
- [ ] Bookmark for easy access

**Your Live URLs:**
- **Homepage:** `https://your-app.onrender.com/`
- **Search:** `https://your-app.onrender.com/search?q=שבת`
- **Stats:** `https://your-app.onrender.com/stats`
- **API:** `https://your-app.onrender.com/api/search?q=test`

---

## 🔄 Step 11: How to Update Your App Later

When you make code changes:

```bash
# Make your changes, then:
git add .
git commit -m "Description of changes"
git push
```

- [ ] Render will **automatically redeploy** your app
- [ ] Check the **"Events"** tab to see deployment progress

**Note:** The index and data file remain on the server - no need to re-upload!

---

## ❗ Troubleshooting

### Problem: App shows "Application failed to respond"

**Solution:**
- [ ] Check deploy logs in Render dashboard
- [ ] Verify index was built successfully
- [ ] Check that `INDEX_PATH` environment variable is set
- [ ] Try restarting the service (Manual Deploy → Deploy Latest Commit)

### Problem: Search returns no results

**Solution:**
- [ ] Verify index exists: Run `ls -lh index/` in Shell
- [ ] Rebuild index if needed (Step 7)
- [ ] Check that data file was uploaded correctly

### Problem: App is very slow (Free tier)

**Solution:**
- [ ] First request after sleep takes ~30 seconds (normal for free tier)
- [ ] Upgrade to Starter plan for always-on service

### Problem: "Index not found" error

**Solution:**
- [ ] Set environment variable `INDEX_PATH=index/` in Render settings
- [ ] Redeploy the app

---

## 🎯 Success Checklist

Your deployment is successful when:

- [x] App loads at your Render URL
- [x] Can search for Hebrew text and get results
- [x] Statistics page shows 162,198 documents
- [x] Document viewer works
- [x] API endpoints return JSON data
- [x] No error messages in logs

---

## 📞 Need Help?

- **Render Documentation:** [render.com/docs](https://render.com/docs)
- **Render Community:** [community.render.com](https://community.render.com)
- **GitHub Issues:** Create an issue in your repository

---

## 🎉 Congratulations!

You've successfully deployed the Cairo Genizah Search Tool!

**What you've built:**
- ✅ Full-stack web application
- ✅ 162,198 searchable documents
- ✅ Hebrew/Arabic text support
- ✅ RESTful API
- ✅ Live on the internet!

**Next steps:**
- Use it for research
- Share with colleagues
- Add new features
- Customize the design

---

**Estimated Total Time:** 30-45 minutes
- Setup accounts: 5 min
- Push to GitHub: 5 min
- Deploy on Render: 5 min
- Upload data file: 5-10 min
- Build index: 10-15 min
- Testing: 5 min

**Total Cost:** $0 (free tier) or $7/month (recommended)

---

*Last updated: 2024-11-27*
*Created with ❤️ for Cairo Genizah research*
