# Deployment Guide: Exoplanet Detection Web Applications

This guide describes how to deploy the static presentation website and the Streamlit computational dashboard to the web for free.

---

## 1. Deploying the Static Web Portal (web/ folder)

The presentation website (`web/index.html`, `web/styles.css`, `web/app.js`) is static and can be deployed instantly for free on multiple platforms.

### Option A: GitHub Pages via GitHub Actions (Recommended)
GitHub Pages defaults to the root `/` or `/docs` directories. To deploy the `/web` subdirectory automatically, we have added a GitHub Actions workflow in `.github/workflows/static.yml`.

1. Push your repository to GitHub.
2. In your GitHub repository, go to **Settings** > **Pages**.
3. Under **Build and deployment** > **Source**, select **GitHub Actions** (instead of "Deploy from a branch").
4. The workflow will trigger automatically and build your site from the `./web` folder.
5. Access your page at `https://your-username.github.io/your-repo-name/`.

### Option B: GitHub Pages via Git Subtree (Alternative)
If you prefer not to use GitHub Actions, you can push the `/web` folder directly to a separate `gh-pages` branch:
1. Run this command in your project terminal:
   ```bash
   git subtree push --prefix web origin gh-pages
   ```
2. In GitHub **Settings** > **Pages**, set **Source** to "Deploy from a branch", choose `gh-pages` and `/` (root), then click **Save**.

### Option C: Netlify
1. Go to [Netlify](https://www.netlify.com/) and log in.
2. Drag and drop the `web/` folder directly into the Netlify import box.
3. Netlify will deploy it instantly and provide a public URL (which you can customize).

---

## 2. Deploying the Streamlit Computational Dashboard (app.py)

Since the Streamlit application requires a Python backend to execute Astropy, PyTorch, and machine learning models, it must be hosted on a cloud provider with a Python runner.

### Option A: Streamlit Community Cloud (Recommended)
1. Push your complete project repository to GitHub (ensure `requirements.txt` and the `models/` folder containing your pre-trained models are included).
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with your GitHub account.
3. Click **New app**.
4. Select your repository, branch (`main`), and set the main file path to `app.py`.
5. Click **Deploy**. Streamlit will install the requirements from `requirements.txt` and launch your dashboard on a public `*.streamlit.app` URL.

### Option B: Hugging Face Spaces
1. Go to [Hugging Face](https://huggingface.co/) and click **New Space**.
2. Name your space, select **Streamlit** as the SDK, and choose the free **CPU Basic** hardware tier.
3. Clone the space repository locally or upload your files directly through the Hugging Face web interface:
   - Upload `app.py`
   - Upload `requirements.txt`
   - Upload the `src/` folder
   - Upload the `models/` folder
4. Hugging Face will build the container and deploy the app automatically.
