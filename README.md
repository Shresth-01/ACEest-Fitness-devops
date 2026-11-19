# ACEest Fitness & Gym

A Flask REST API for managing fitness clients, programs, workouts, and progress. The project demonstrates automated code checks and Docker-based testing with GitHub Actions, plus a separate Jenkins BUILD pipeline.

> **Pipeline scope:** GitHub Actions and Jenkins build and test the application. This repository does not currently publish the Docker image or deploy the service.

## Features

- List fitness programs and their workout/diet guidance.
- Create and list clients, with calorie estimates.
- Calculate a client's BMI.
- Record and list workouts.
- Record weekly progress and validate adherence values.
- Persist application data in SQLite.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Flask API and SQLite data access |
| `test_app.py` | Pytest unit and API tests |
| `requirements.txt` | Python dependencies, including Flake8 |
| `Dockerfile` | Builds the application/test image |
| `.github/workflows/main.yml` | GitHub Actions build, lint, Docker, and test workflow |
| `Jenkinsfile` | Jenkins BUILD and quality-gate pipeline |

## Requirements

- Python 3.11
- Git
- Docker, if you want to build and run the container locally

## Set up and run locally

Clone the repository, then create and activate a virtual environment.

**Windows PowerShell**

```powershell
git clone https://github.com/Shresth-01/ACEest-Fitness-devops.git
Set-Location ACEest-Fitness-devops
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux or macOS**

```bash
git clone https://github.com/Shresth-01/ACEest-Fitness-devops.git
cd ACEest-Fitness-devops
python3.11 -m venv .venv
source .venv/bin/activate
```

Install the dependencies and start the API:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

The API listens on `http://127.0.0.1:5000`. It creates its SQLite database in the working directory by default. Set `DB_NAME` to use a different database path.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service information |
| `GET` | `/health` | Health check |
| `GET` | `/programs` | Available fitness programs |
| `GET`, `POST` | `/clients` | List or save clients |
| `GET` | `/clients/<name>/bmi` | Calculate a saved client's BMI |
| `GET`, `POST` | `/workouts` | List or record workouts |
| `POST` | `/progress` | Record weekly progress |

For example, with the server running, use another PowerShell window:

```powershell
curl.exe http://127.0.0.1:5000/health
curl.exe http://127.0.0.1:5000/programs
curl.exe -X POST http://127.0.0.1:5000/clients -H "Content-Type: application/json" -d '{"name":"Sam","age":25,"height":175,"weight":70,"program":"Fat Loss (FL)"}'
curl.exe http://127.0.0.1:5000/clients
curl.exe http://127.0.0.1:5000/clients/Sam/bmi
```

## Run checks locally

```bash
python -m py_compile app.py test_app.py
flake8 app.py test_app.py --count --max-complexity=10 --max-line-length=100 --statistics
pytest -v
```

The tests use a temporary SQLite database, so test data is kept separate from the application's local database.

## Build and test with Docker

Build the image:

```bash
docker build -t aceest-fitness-app:local .
```

Run the test suite inside the image:

```bash
docker run --rm aceest-fitness-app:local pytest -v
```

To run the API in a container instead, publish its port:

```bash
docker run --rm -p 5000:5000 aceest-fitness-app:local
```

Then check `http://127.0.0.1:5000/health` from the host.

## Pipeline overview

The two pipelines are separate ways to build and check the same repository:

```text
Developer push or pull request
              |
       GitHub repository
       /              \
GitHub Actions       Jenkins job
(GitHub runner)      (configured agent)
       |                  |
Checkout, lint,      Checkout, lint,
Docker build, tests  Docker build, tests
       |                  |
Actions result       Jenkins result
```

GitHub provides the temporary runner for Actions. Jenkins uses an agent selected by the Jenkins installation. Docker runs containers on those machines; it does not provision either machine.

## GitHub Actions workflow

The workflow in `.github/workflows/main.yml` runs for every push and pull request. GitHub provides a temporary Ubuntu runner for each workflow run. The job checks out the code, sets up Python 3.11, installs dependencies, compiles and lints the Python files, builds a Docker image, and runs Pytest inside a container.

A successful run means those checks passed. The Docker image remains on the temporary runner; the workflow does not push it to a registry or deploy the application. Requiring a passing check before merging is a separate repository branch-protection setting.

## Jenkins BUILD pipeline

The `Jenkinsfile` defines a pipeline that checks out the repository, installs dependencies, runs linting and tests, builds a Docker image, and runs the tests inside that image. Jenkins is separate from GitHub Actions; one pipeline does not start the other.

To use this Jenkinsfile:

1. Create a Jenkins **Pipeline** job.
2. Select **Pipeline script from SCM**, choose Git, and enter the repository URL.
3. Set the branch to `*/main` and the script path to `Jenkinsfile`.
4. Ensure the Jenkins agent is a Linux machine with Python 3.11, pip, Docker, and permission to use the Docker daemon.
5. Run the job manually, or configure a GitHub webhook/polling trigger in Jenkins separately.

The Jenkinsfile uses `agent any` and Linux shell steps (`sh`); it does not provision a VM. The Jenkins controller, agent, job configuration, and any trigger are provided/configured separately. Jenkins also removes the locally built image after the job. This pipeline is a BUILD and quality gate; it does not publish an image or deploy the service.
