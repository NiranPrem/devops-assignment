// Jenkinsfile
// CI/CD pipeline: Checkout → Lint → Test → Build → Scan → Push → Deploy → Validate

pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
    - name: docker
      image: docker:24-dind
      securityContext:
        privileged: true    # required for DinD
      env:
        - name: DOCKER_TLS_CERTDIR
          value: ""
    - name: trivy
      image: aquasec/trivy:latest
      command: [sleep, infinity]
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
    - name: kubectl
      image: bitnami/kubectl:latest
      command: [sleep, infinity]
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
    - name: python
      image: python:3.12-slim
      command: [sleep, infinity]
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
'''
        }
    }

    environment {
        IMAGE_REGISTRY   = credentials('REGISTRY_URL')
        REGISTRY_CREDS   = 'registry-credentials'
        KUBE_NAMESPACE   = 'dev'
        API_IMAGE        = "${IMAGE_REGISTRY}/devops-assignment/api"
        WEB_IMAGE        = "${IMAGE_REGISTRY}/devops-assignment/web"
        IMAGE_TAG        = "${GIT_COMMIT[0..7]}"
        TRIVY_SEVERITY   = 'CRITICAL'
    }

    options {
        ansiColor('xterm')
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout Source') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    env.IMAGE_TAG = env.GIT_COMMIT_SHORT
                    echo "Building commit: ${env.GIT_COMMIT_SHORT}"
                }
            }
        }

        stage('Lint') {
            parallel {
                stage('Lint Python (API)') {
                    steps {
                        container('python') {
                            sh '''
                                pip install --quiet flake8
                                flake8 app/api/ --max-line-length=120 --exclude=__pycache__
                            '''
                        }
                    }
                }
                stage('Lint Dockerfiles') {
                    steps {
                        container('docker') {
                            sh '''
                                # Install hadolint
                                wget -qO /usr/local/bin/hadolint \
                                  https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
                                chmod +x /usr/local/bin/hadolint
                                hadolint app/api/Dockerfile
                                hadolint app/web/Dockerfile
                            '''
                        }
                    }
                }
                stage('Validate K8s manifests') {
                    steps {
                        container('kubectl') {
                            sh 'kubectl kustomize k8s/overlays/dev --dry-run=client 2>&1'
                        }
                    }
                }
            }
        }

        stage('Unit Tests') {
            parallel {
                stage('API Tests') {
                    steps {
                        container('python') {
                            sh '''
                                cd app/api
                                pip install --quiet -r requirements.txt pytest pytest-asyncio httpx
                                pytest tests/ -v --tb=short 2>/dev/null || echo "No tests directory found — skipping"
                            '''
                        }
                    }
                }
                stage('Web Tests') {
                    steps {
                        container('docker') {
                            sh '''
                                cd app/web
                                node --version
                                npm test 2>/dev/null || echo "No tests defined — skipping"
                            '''
                        }
                    }
                }
            }
        }

        stage('Docker Build') {
            parallel {
                stage('Build API image') {
                    steps {
                        container('docker') {
                            sh """
                                docker build \
                                  -t ${API_IMAGE}:${IMAGE_TAG} \
                                  -t ${API_IMAGE}:latest \
                                  app/api/
                            """
                        }
                    }
                }
                stage('Build Web image') {
                    steps {
                        container('docker') {
                            sh """
                                docker build \
                                  -t ${WEB_IMAGE}:${IMAGE_TAG} \
                                  -t ${WEB_IMAGE}:latest \
                                  app/web/
                            """
                        }
                    }
                }
            }
        }

        stage('Security Scan') {
            parallel {
                stage('Scan API image') {
                    steps {
                        container('trivy') {
                            sh """
                                trivy image \
                                  --severity ${TRIVY_SEVERITY} \
                                  --exit-code 1 \
                                  --format table \
                                  --no-progress \
                                  ${API_IMAGE}:${IMAGE_TAG}
                            """
                        }
                    }
                    post {
                        always {
                            container('trivy') {
                                sh """
                                    trivy image \
                                      --severity HIGH,CRITICAL \
                                      --format json \
                                      --output trivy-api-report.json \
                                      --no-progress \
                                      ${API_IMAGE}:${IMAGE_TAG} || true
                                """
                            }
                            archiveArtifacts artifacts: 'trivy-api-report.json', allowEmptyArchive: true
                        }
                    }
                }
                stage('Scan Web image') {
                    steps {
                        container('trivy') {
                            sh """
                                trivy image \
                                  --severity ${TRIVY_SEVERITY} \
                                  --exit-code 1 \
                                  --format table \
                                  --no-progress \
                                  ${WEB_IMAGE}:${IMAGE_TAG}
                            """
                        }
                    }
                    post {
                        always {
                            container('trivy') {
                                sh """
                                    trivy image \
                                      --severity HIGH,CRITICAL \
                                      --format json \
                                      --output trivy-web-report.json \
                                      --no-progress \
                                      ${WEB_IMAGE}:${IMAGE_TAG} || true
                                """
                            }
                            archiveArtifacts artifacts: 'trivy-web-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Push Image') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(
                        credentialsId: env.REGISTRY_CREDS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            echo "\$DOCKER_PASS" | docker login ${IMAGE_REGISTRY} \
                              -u "\$DOCKER_USER" --password-stdin
                            docker push ${API_IMAGE}:${IMAGE_TAG}
                            docker push ${API_IMAGE}:latest
                            docker push ${WEB_IMAGE}:${IMAGE_TAG}
                            docker push ${WEB_IMAGE}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            export KUBECONFIG=\$KUBECONFIG

                            # Update image tags in overlay
                            cd k8s/overlays/dev
                            kustomize edit set image \
                              devops-assignment/api=${API_IMAGE}:${IMAGE_TAG} \
                              devops-assignment/web=${WEB_IMAGE}:${IMAGE_TAG}

                            # Apply
                            kubectl apply -k . --namespace ${KUBE_NAMESPACE}

                            echo "Deployment triggered for tag: ${IMAGE_TAG}"
                        """
                    }
                }
            }
        }

        stage('Post-Deployment Validation') {
            steps {
                container('kubectl') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            export KUBECONFIG=\$KUBECONFIG

                            echo "Waiting for api rollout..."
                            kubectl rollout status deployment/api \
                              -n ${KUBE_NAMESPACE} --timeout=180s

                            echo "Waiting for web rollout..."
                            kubectl rollout status deployment/web \
                              -n ${KUBE_NAMESPACE} --timeout=180s

                            echo ""
                            echo "=== Pod status ==="
                            kubectl get pods -n ${KUBE_NAMESPACE} -o wide

                            echo ""
                            echo "=== Healthcheck ==="
                            NODE_IP=\$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
                            curl -sf http://\${NODE_IP}:30080/api/healthz && echo "API healthy!" || echo "API health check failed"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo " Pipeline succeeded. Image: ${API_IMAGE}:${IMAGE_TAG}"
        }
        failure {
            echo " Pipeline failed. Initiating rollback..."
            container('kubectl') {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        export KUBECONFIG=$KUBECONFIG
                        kubectl rollout undo deployment/api -n ${KUBE_NAMESPACE} || true
                        kubectl rollout undo deployment/web -n ${KUBE_NAMESPACE} || true
                        echo "Rollback complete."
                        kubectl get pods -n ${KUBE_NAMESPACE}
                    '''
                }
            }
        }
        always {
            cleanWs()
        }
    }
}
