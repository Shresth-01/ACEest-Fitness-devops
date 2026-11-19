# ACEest Fitness & Gym — Automated CI/CD Pipeline

A containerized Flask REST API for **ACEest Fitness & Gym** member, workout, nutrition, and progress management, backed by automated testing (`Pytest`), containerization (`Docker`), a `Jenkins` BUILD quality gate, and a `GitHub Actions` CI/CD workflow.

## Project Structure

```text
├── .github/workflows/main.yml   # GitHub Actions CI/CD workflow (Build/Lint, Docker, Pytest)
├── .dockerignore                # Excludes cache, git, and local DB files from Docker context
├── Dockerfile                   # Slim, non-root production container definition
├── Jenkinsfile                  # Declarative Jenkins pipeline for BUILD & quality gating
├── app.py                       # Core Flask application & SQLite persistence
├── test_app.py                  # Pytest unit & API integration test suite
├── requirements.txt             # Python dependencies
└── README.md                    # Project setup and CI/CD documentation