# Google Keep Sync & Enrichment Service

This project polls Google Keep for notes labeled "Ready to Export," enriches them with OpenAI GPT-4, and syncs them to a private Git repo as Markdown files. It runs on Google Cloud Run with daily triggers from Cloud Scheduler.

## Features
- Automated daily sync.
- LLM-based enrichment of notes.
- Push to private Git repository.
- Minimal cost to operate.

## Architecture
1. **GitHub** hosts source code and secrets.
2. **GitHub Actions** builds and deploys the container to **Cloud Run**.
3. **Cloud Scheduler** invokes the container daily at `/sync`.

## Local Development

### Prerequisites
- Docker installed on your system.
- Git configured for accessing your private repository.
- Secrets for the following:
  - `GOOGLE_KEEP_USERNAME`
  - `GOOGLE_KEEP_MASTER_TOKEN`
  - `OPENAI_API_KEY`
  - `GIT_SSH_KEY` (SSH private key for your Git repository).

### Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Set Up Environment Variables**
   ```bash
   export GOOGLE_KEEP_USERNAME="your-email@gmail.com"
   export GOOGLE_KEEP_MASTER_TOKEN="your-keep-master-token"
   export OPENAI_API_KEY="your-openai-api-key"
   export GIT_SSH_KEY="$(cat /path/to/your/ssh-private-key)"
   ```

3. **Build the Docker Image**
   ```bash
   docker build -t gkeep-sync:local .
   ```

4. **Run the Service Locally**
   ```bash
   docker run -p 8080:8080 \
       -e GOOGLE_KEEP_USERNAME="$GOOGLE_KEEP_USERNAME" \
       -e GOOGLE_KEEP_MASTER_TOKEN="$GOOGLE_KEEP_MASTER_TOKEN" \
       -e OPENAI_API_KEY="$OPENAI_API_KEY" \
       -e GIT_SSH_KEY="$GIT_SSH_KEY" \
       gkeep-sync:local
   ```

5. **Test Locally**
   - Visit [http://localhost:8080/](http://localhost:8080/) to check the health of the service.
   - Trigger the sync process by sending a GET request to `/sync`:
     ```bash
     curl http://localhost:8080/sync
     ```

## Deployment

### Prerequisites
1. Set up a Google Cloud Platform (GCP) project.
   - Enable **Cloud Run**, **Cloud Scheduler**, and **Artifact Registry** APIs.
2. Set up GitHub Secrets:
   - `GCP_SA_KEY`: Service account key for GCP.
   - `GIT_DEPLOY_KEY`: SSH private key for accessing your private Git repository.
   - `GOOGLE_KEEP_USERNAME`: Your Google account username.
   - `GOOGLE_KEEP_MASTER_TOKEN`: Master token for Google Keep authentication.
   - `OPENAI_API_KEY`: OpenAI API key.

### Steps
1. **Push to GitHub**
   - Push your changes to the main branch (or the branch you configured in `.github/workflows/deploy.yaml`).

2. **GitHub Actions Workflow**
   - The `deploy.yaml` workflow will:
     - Build the Docker container.
     - Push it to Google Artifact Registry.
     - Deploy it to Google Cloud Run.

3. **Set Up Cloud Scheduler**
   - Use Terraform (provided in `infra/main.tf`) or the GCP Console to configure a daily trigger for your Cloud Run service.

## Testing
- Run tests using `pytest`:
  ```bash
  pip install pytest
  pytest tests/
  ```

## Cost Considerations
- **Cloud Run**: Free for minimal usage (1 GiB memory, 0.08 vCPU). Pay only for requests.
- **Cloud Scheduler**: \$0.10/month for one job.
- **Artifact Registry**: Minimal cost for storage and image pulls.

## Architecture Overview

```
+------------------+         +-------------------+
|   GitHub Repo    |         |   GitHub Secrets  |
|  (Source Code)   |         | (SSH Key, Tokens) |
+------------------+         +-------------------+
          |                          ^
          |  (push)                  |
          |                          |
          v                          |
+----------------------------------------+
|     GitHub Actions (deploy.yaml)      |
| - Docker Build & Push                 |
| - Cloud Run Deploy (gcloud)           |
+----------------------------------------+
         |
         | (Docker Image)
         v
+---------------------------+
|     Cloud Run Service     | <-- accessible via HTTPS
| (Flask-based "sync" API) |
+------------+--------------+
             |
   (HTTP GET /sync triggered by Cloud Scheduler)
             v
   +--------------------+
   |    Sync Logic      |
   |  - Auth to Keep    |
   |  - Call OpenAI     |
   |  - Git Sync (SSH)  |
   +--------------------+

```

## License
[MIT](LICENSE)