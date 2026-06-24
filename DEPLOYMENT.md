# Deployment & Review Guide: Financial Planner

This guide contains step-by-step instructions on preparing this application for a review in **Google AI Studio** and deploying it to **Google Cloud Run**.

---

## 1. Preparing for Google AI Studio Review

Google AI Studio allows you to upload files (such as codebases) to ask questions, review architecture, or refactor code.

To make this easy, a packaging script is included in the project:
1. Run the following command from the root directory:
   ```bash
   python scripts/pack_codebase.py
   ```
2. This generates a clean ZIP file named `financial_planner_codebase.zip` in your project root.
   - It automatically excludes heavy folders like `.git/`, `node_modules/`, `venv/`, and `scratch/`.
3. Upload `financial_planner_codebase.zip` directly into **Google AI Studio** to begin your prompt-based codebase review.

---

## 2. Containerized Architecture for Cloud Run

To make deployment simple and cost-efficient, the application is designed to run in a **single-port container**:
- The React frontend is compiled into static assets (`npm run build`).
- The FastAPI backend hosts these static assets from its root route (`/`) and serves the calculation APIs from `/api`.
- Both frontend and backend run on a single port (default: `8080`), avoiding CORS issues and minimizing Cloud Run resource overhead.

---

## 3. Deploying to Google Cloud Run

To deploy this application to Google Cloud Run, follow these steps:

### Prerequisites
1. Install the [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install).
2. Authenticate and select your Google Cloud project:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. Enable the required Google Cloud APIs:
   ```bash
   gcloud services enable run.googleapis.com artifactregistry.googleapis.com
   ```

### Step-by-Step Deployment

#### Step 3.1: Build and Deploy using Google Cloud Build
Google Cloud Run can build the Docker container directly in the cloud and deploy it without requiring a local Docker installation:

Run the following command from the root folder:
```bash
gcloud run deploy financial-planner \
  --source . \
  --port 8080 \
  --allow-unauthenticated \
  --region us-central1
```

#### What this command does:
1. Uploads the codebase to Google Cloud Build.
2. Uses the root `Dockerfile` to compile the frontend and set up the Python FastAPI environment.
3. Deploys the container to Cloud Run.
4. Returns a secure HTTPS URL (e.g., `https://financial-planner-xxx-uc.a.run.app`) where your app is live.

---

## 4. Local Container Testing

If you want to test the Docker build locally before deploying to the cloud, use the following commands:

1. **Build the container:**
   ```bash
   docker build -t financial-planner .
   ```
2. **Run the container:**
   ```bash
   docker run -p 8080:8080 -e PORT=8080 financial-planner
   ```
3. Open [http://localhost:8080](http://localhost:8080) in your browser.
