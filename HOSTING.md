# BBO 2026 Judging Schedule - Hosting Instructions

## Quick Setup for GitHub Pages (Recommended)

### 1. Create a GitHub Repository

1. Go to https://github.com/new
2. Name your repository (e.g., `bbo-2026-judging`)
3. Set it to **Public** (required for free GitHub Pages)
4. Don't initialize with README (you already have files)
5. Click "Create repository"

### 2. Push Your Code to GitHub

Run these commands in your terminal:

```bash
cd "/Users/barryforrest/Documents/Judging BBO 2026"

# Add the GitHub remote (replace YOUR-USERNAME and YOUR-REPO with your details)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git

# Add and commit all files
git add .
git commit -m "Initial commit with judging schedule"

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Pages** in the left sidebar
4. Under "Build and deployment":
   - Source: Select **GitHub Actions**
5. The workflow will automatically deploy your site

### 4. Access Your Live Site

After the GitHub Action completes (~2 minutes), your site will be available at:

```
https://YOUR-USERNAME.github.io/YOUR-REPO/
```

## Alternative: Quick One-Time Hosting with Netlify Drop

If you want instant hosting without GitHub:

1. Go to https://app.netlify.com/drop
2. Drag and drop the `index.html` file
3. Get an instant shareable URL (e.g., `random-name-123.netlify.app`)

**Note:** This URL is temporary unless you create a free Netlify account.

## Updating the Schedule

### With GitHub Pages
After initial setup, just push changes and the site auto-updates:

```bash
# After updating data files and regenerating
python3 generate_schedule.py
cp judging_schedule.html index.html
git add .
git commit -m "Update schedule"
git push
```

The GitHub Action will automatically regenerate and deploy the updated schedule.

### With Netlify Drop
Re-drag the updated `index.html` file to get a new URL.

## Custom Domain (Optional)

Both GitHub Pages and Netlify support custom domains like `judging.yourdomain.com`:

- **GitHub Pages**: Settings → Pages → Custom domain
- **Netlify**: Site settings → Domain management → Add custom domain
