terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables for easy configuration
variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "us-central1"
}
variable "service_name" {
  type    = string
  default = "gkeep-sync"
}

# Create an Artifact Registry repository if you don't already have one
resource "google_artifact_registry_repository" "repo" {
  project  = var.project_id
  location = var.region
  repository_id = "my-docker-repo"
  format   = "DOCKER"
}

# Create Cloud Run service - placeholders to show the general approach
resource "google_cloud_run_service" "gkeep_sync" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/gkeep-sync:latest"
        env {
          name  = "GOOGLE_KEEP_USERNAME"
          value = "TODO" # Typically set via GitHub Actions in this example
        }
        # Add more env vars as needed
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated access so Cloud Scheduler can call it (or add IAM integration)
resource "google_cloud_run_service_iam_member" "noauth" {
  location        = var.region
  project         = var.project_id
  service         = google_cloud_run_service.gkeep_sync.name
  role            = "roles/run.invoker"
  member          = "allUsers"
}

# Optional Cloud Scheduler to call once a day
resource "google_scheduler_job" "daily_sync" {
  name             = "daily-gkeep-sync"
  description      = "Calls the Cloud Run service daily"
  schedule         = "0 6 * * *"  # runs every day at 06:00
  time_zone        = "UTC"

  http_target {
    http_method = "GET"
    uri         = "https://${google_cloud_run_service.gkeep_sync.status[0].url}/sync"
  }
}
