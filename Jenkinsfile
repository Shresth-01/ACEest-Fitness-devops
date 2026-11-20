pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-fitness-app"
        IMAGE_TAG  = "build-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                checkout scm
            }
        }

        stage('Build & Lint') {
            steps {
                sh '''
                    python3 -m pip install -r requirements.txt
                    python3 -m py_compile app.py test_app.py
                    python3 -m flake8 app.py test_app.py --count --max-line-length=100 --statistics
                '''
            }
        }

        stage('Unit Testing (Pytest)') {
            steps {
                sh 'python3 -m pytest -v'
            }
        }

        stage('Docker Image Build') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker images ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Containerized Test & Smoke Check') {
            steps {
                sh '''
                    docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} python -m pytest -v
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true'
        }
        success {
            echo 'ACEest Fitness BUILD & Quality Gate PASSED successfully.'
        }
    }
}