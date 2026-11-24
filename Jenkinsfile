pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(name: 'DEPLOY_STRATEGY', choices: ['rolling', 'blue-green', 'canary', 'shadow', 'ab'],
               description: 'Kubernetes demonstration strategy')
        choice(name: 'DEPLOY_ACTION', choices: ['deploy', 'rollback'],
               description: 'Deploy a release or roll back the active Deployment')
    }

    environment {
        SONAR_SERVER = 'SonarQube'
        SONAR_TOKEN = credentials('sonarqube-token')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        KUBECONFIG_CREDENTIAL = 'kubeconfig'
        APP_NAME = 'aceest-fitness-app'
        APP_VERSION = "2.0.${BUILD_NUMBER}"
        RELEASE_TAG = "v2.0.${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git --no-pager status --short'
            }
        }

        stage('Build and Lint') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    python3 -m pip install -r requirements.txt
                    python3 -m py_compile app.py test_app.py
                    python3 -m flake8 app.py test_app.py \
                        --count --max-complexity=10 --max-line-length=100 --statistics
                '''
            }
        }

        stage('Unit Tests and Coverage') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                sh 'python3 -m pytest -v --junitxml=test-results.xml --cov=app --cov-report=term-missing --cov-report=xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                withSonarQubeEnv("${SONAR_SERVER}") {
                    sh '''
                        sonar-scanner \
                          -Dsonar.projectKey=aceest-fitness \
                          -Dsonar.projectVersion=${APP_VERSION} \
                          -Dsonar.login=${SONAR_TOKEN}
                    '''
                }
            }
        }

        stage('SonarQube Quality Gate') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Container') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                script {
                    env.DOCKERHUB_USERNAME = sh(
                        script: 'echo "${DOCKERHUB_CREDENTIALS_USR}"',
                        returnStdout: true
                    ).trim()
                    env.LOCAL_IMAGE = "${APP_NAME}:${APP_VERSION}"
                    env.REMOTE_IMAGE = "${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}"
                }
                sh '''
                    docker build \
                      --build-arg APP_VERSION=${APP_VERSION} \
                      -t ${LOCAL_IMAGE} \
                      -t ${REMOTE_IMAGE} \
                      -t ${DOCKERHUB_USERNAME}/${APP_NAME}:${RELEASE_TAG} \
                      -t ${DOCKERHUB_USERNAME}/${APP_NAME}:latest \
                      .
                '''
            }
        }

        stage('Container Tests') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                sh '''
                    docker run --rm ${LOCAL_IMAGE} python -m pytest -v
                    docker run -d --name aceest-smoke-${BUILD_NUMBER} -p 5099:5000 \
                      -e APP_VERSION=${APP_VERSION} -e DEPLOY_VARIANT=jenkins-smoke \
                      ${LOCAL_IMAGE}
                    SMOKE_OK=false
                    for i in $(seq 1 15); do
                        if curl -fsS http://127.0.0.1:5099/health; then
                            curl -fsS http://127.0.0.1:5099/version
                            SMOKE_OK=true
                            break
                        fi
                        sleep 2
                    done
                    test "$SMOKE_OK" = "true"
                '''
            }
            post {
                always {
                    sh 'docker rm -f aceest-smoke-${BUILD_NUMBER} || true'
                }
            }
        }

        stage('Publish Docker Image') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                sh 'echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin'
                sh '''
                    docker push ${REMOTE_IMAGE}
                    docker push ${DOCKERHUB_USERNAME}/${APP_NAME}:${RELEASE_TAG}
                    docker push ${DOCKERHUB_USERNAME}/${APP_NAME}:latest
                '''
            }
            post {
                always {
                    sh 'docker logout || true'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/stable.yaml
                        kubectl -n aceest set image deployment/aceest-fitness-stable \
                          app=${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}
                        kubectl -n aceest apply -f k8s/${DEPLOY_STRATEGY}.yaml
                        kubectl -n aceest rollout status deployment/aceest-fitness-stable --timeout=180s
                        if [ "${DEPLOY_STRATEGY}" = "blue-green" ]; then
                            kubectl -n aceest set image deployment/aceest-fitness-green \
                              app=${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}
                            kubectl -n aceest rollout status deployment/aceest-fitness-green --timeout=180s
                            kubectl -n aceest patch service aceest-fitness \
                              -p '{"spec":{"selector":{"app":"aceest-fitness","track":"green"}}}'
                        elif [ "${DEPLOY_STRATEGY}" = "canary" ]; then
                            kubectl -n aceest set image deployment/aceest-fitness-canary \
                              app=${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}
                            kubectl -n aceest rollout status deployment/aceest-fitness-canary --timeout=180s
                            kubectl -n aceest patch service aceest-fitness \
                              -p '{"spec":{"selector":{"app":"aceest-fitness"}}}'
                        elif [ "${DEPLOY_STRATEGY}" = "shadow" ]; then
                            kubectl -n aceest set image deployment/aceest-fitness-shadow \
                              app=${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}
                            kubectl -n aceest rollout status deployment/aceest-fitness-shadow --timeout=180s
                        elif [ "${DEPLOY_STRATEGY}" = "ab" ]; then
                            kubectl -n aceest set image deployment/aceest-fitness-version-b \
                              app=${DOCKERHUB_USERNAME}/${APP_NAME}:${APP_VERSION}
                            kubectl -n aceest rollout status deployment/aceest-fitness-version-b --timeout=180s
                        fi
                    '''
                }
            }
        }

        stage('Kubernetes Smoke Test') {
            when { expression { params.DEPLOY_ACTION == 'deploy' } }
            steps {
                withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl -n aceest get deployments,pods,services
                        kubectl -n aceest rollout history deployment/aceest-fitness-stable
                        kubectl -n aceest port-forward service/aceest-fitness 5010:80 >/tmp/aceest-port-forward.log 2>&1 &
                        PF_PID=$!
                        trap 'kill $PF_PID 2>/dev/null || true' EXIT
                        sleep 5
                        curl -fsS http://127.0.0.1:5010/health
                        curl -fsS http://127.0.0.1:5010/version
                        kill $PF_PID 2>/dev/null || true
                        trap - EXIT
                    '''
                }
            }
        }

        stage('Rollback') {
            when { expression { params.DEPLOY_ACTION == 'rollback' } }
            steps {
                withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl -n aceest rollout undo deployment/aceest-fitness-stable
                        kubectl -n aceest rollout status deployment/aceest-fitness-stable --timeout=180s
                        kubectl -n aceest get pods
                    '''
                }
            }
        }
    }

    post {
        failure {
            withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG')]) {
                sh '''
                    kubectl -n aceest rollout undo deployment/aceest-fitness-stable >/dev/null 2>&1 || true
                '''
            }
        }
        always {
            sh 'docker rmi ${LOCAL_IMAGE} ${REMOTE_IMAGE} ${DOCKERHUB_USERNAME}/${APP_NAME}:${RELEASE_TAG} ${DOCKERHUB_USERNAME}/${APP_NAME}:latest 2>/dev/null || true'
        }
    }
}
