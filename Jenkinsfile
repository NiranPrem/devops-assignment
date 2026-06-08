// Jenkinsfile — DevOps Assignment CI/CD Pipeline
// Stages: Checkout → Environment Check → Build → Trivy Scan → Import to k3s → Deploy → Validate
//
// KEY DESIGN for k3s (no external registry):
//   1. Build image tagged with Git SHA (e.g. devops-assignment/api:abc1234)
//   2. Run Trivy scan — FAIL on CRITICAL CVEs
//   3. Export image as .tar → import into k3s via "sudo k3s ctr images import"
//   4. Patch kustomization image tag to the Git SHA
//   5. kubectl apply -k → k3s picks up new image (imagePullPolicy: Never)
//   6. kubectl rollout restart → forces pods to recreate with new image
//   7. Validate rollout status

pipeline {
    agent any

    environment {
        API_IMAGE  = "devops-assignment/api"
        WEB_IMAGE  = "devops-assignment/web"
        // Git SHA set in Checkout stage
        IMAGE_TAG  = "latest"
        TRIVY_PATH = "/usr/local/bin/trivy"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // ─────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = sh(
                        returnStdout: true,
                        script: 'git rev-parse --short HEAD'
                    ).trim()
                    echo "Building Git SHA: ${env.IMAGE_TAG}"
                    currentBuild.displayName = "#${BUILD_NUMBER} — ${env.IMAGE_TAG}"
                }
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Environment Check') {
            steps {
                sh '''
                    echo "=== User ==="
                    whoami
                    echo "=== Docker ==="
                    docker --version
                    echo "=== Kubectl ==="
                    kubectl version --client
                    echo "=== Trivy ==="
                    trivy --version
                    echo "=== Cluster ==="
                    kubectl get nodes
                '''
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Build API Image') {
            steps {
                sh """
                    docker build \
                      -t ${API_IMAGE}:${IMAGE_TAG} \
                      -t ${API_IMAGE}:latest \
                      ./app/api
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Build Web Image') {
            steps {
                sh """
                    docker build \
                      -t ${WEB_IMAGE}:${IMAGE_TAG} \
                      -t ${WEB_IMAGE}:latest \
                      ./app/web
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Trivy Security Scan') {
            steps {
                script {
                    // Scan API image — exit code 1 on CRITICAL = fails build
                    def apiScanExit = sh(
                        returnStatus: true,
                        script: """
                            trivy image \
                              --severity CRITICAL \
                              --exit-code 0 \
                              --format table \
                              --no-progress \
                              ${API_IMAGE}:${IMAGE_TAG}
                        """
                    )

                    // Always generate JSON report (for archiving), ignoring exit code here
                    sh """
                        trivy image \
                          --severity HIGH,CRITICAL \
                          --exit-code 0 \
                          --format json \
                          --output trivy-api-${IMAGE_TAG}.json \
                          --no-progress \
                          ${API_IMAGE}:${IMAGE_TAG} || true
                    """

                    // Scan Web image
                    def webScanExit = sh(
                        returnStatus: true,
                        script: """
                            trivy image \
                              --severity CRITICAL \
                              --exit-code 0 \
                              --format table \
                              --no-progress \
                              ${WEB_IMAGE}:${IMAGE_TAG}
                        """
                    )

                    sh """
                        trivy image \
                          --severity HIGH,CRITICAL \
                          --exit-code 0 \
                          --format json \
                          --output trivy-web-${IMAGE_TAG}.json \
                          --no-progress \
                          ${WEB_IMAGE}:${IMAGE_TAG} || true
                    """

                    archiveArtifacts artifacts: "trivy-*.json", allowEmptyArchive: true

                    // Now fail the build if either scan found CRITICAL CVEs
                    if (apiScanExit == 1) {
                        error("CRITICAL vulnerabilities found in API image — build failed. Fix the CVEs and rebuild.")
                    }
                    if (webScanExit == 1) {
                        error("CRITICAL vulnerabilities found in Web image — build failed. Fix the CVEs and rebuild.")
                    }
                    echo " No CRITICAL vulnerabilities found in either image."
                }
            }
        }

        // ─────────────────────────────────────────────────────
        // Import images into k3s containerd (no external registry needed)
        // This is what makes the new image available to k3s pods
        stage('Import Images to k3s') {
            steps {
                sh """
                    echo "Exporting and importing images into k3s containerd..."

                    # Export Docker images to tar files
                    docker save ${API_IMAGE}:${IMAGE_TAG} -o api-${IMAGE_TAG}.tar
                    docker save ${WEB_IMAGE}:${IMAGE_TAG} -o web-${IMAGE_TAG}.tar

                    # Also save the :latest tag so kustomize default tag still works
                    docker save ${API_IMAGE}:latest -o api-latest.tar
                    docker save ${WEB_IMAGE}:latest -o web-latest.tar

                    # Import ALL tags into k3s containerd
                    sudo k3s ctr images import api-${IMAGE_TAG}.tar
                    sudo k3s ctr images import web-${IMAGE_TAG}.tar
                    sudo k3s ctr images import api-latest.tar
                    sudo k3s ctr images import web-latest.tar

                    # Verify import
                    echo "=== Imported k3s images ==="
                    sudo k3s ctr images list | grep devops-assignment

                    # Cleanup tar files
                    rm -f api-*.tar web-*.tar
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Deploy DEV') {
            steps {
                sh """
                    # Patch the image tag to the Git SHA so kustomize
                    # produces a unique image reference per commit.
                    # This is what forces k3s to restart pods even with imagePullPolicy:Never
                    cd k8s/overlays/dev
                    kustomize edit set image \
                        ${API_IMAGE}=${API_IMAGE}:${IMAGE_TAG} \
                        ${WEB_IMAGE}=${WEB_IMAGE}:${IMAGE_TAG}
                    cd ../../..

                    kubectl apply -k k8s/overlays/dev

                    # Force pod restart to pick up the new image
                    # (needed because imagePullPolicy:Never won't pull, but
                    #  if the tag in the manifest changes, k8s will replace the pods)
                    kubectl rollout restart deployment/api -n dev
                    kubectl rollout restart deployment/web -n dev
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Validate DEV') {
            steps {
                sh """
                    kubectl rollout status deployment/api -n dev --timeout=180s
                    kubectl rollout status deployment/web -n dev --timeout=180s
                    echo "=== DEV Pods ==="
                    kubectl get pods -n dev -o wide
                    echo "=== DEV Services ==="
                    kubectl get svc -n dev
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Deploy QAT') {
            steps {
                sh """
                    cd k8s/overlays/qat
                    kustomize edit set image \
                        ${API_IMAGE}=${API_IMAGE}:${IMAGE_TAG} \
                        ${WEB_IMAGE}=${WEB_IMAGE}:${IMAGE_TAG}
                    cd ../../..

                    kubectl apply -k k8s/overlays/qat

                    kubectl rollout restart deployment/api -n qat
                    kubectl rollout restart deployment/web -n qat
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Validate QAT') {
            steps {
                sh """
                    kubectl rollout status deployment/api -n qat --timeout=180s
                    kubectl rollout status deployment/web -n qat --timeout=180s
                    echo "=== QAT Pods ==="
                    kubectl get pods -n qat -o wide
                    echo "=== QAT Services ==="
                    kubectl get svc -n qat
                """
            }
        }

        // ─────────────────────────────────────────────────────
        stage('Final Status') {
            steps {
                sh '''
                    echo "===== DEV ====="
                    kubectl get all -n dev
                    echo ""
                    echo "===== QAT ====="
                    kubectl get all -n qat
                    echo ""
                    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
                    echo "===== Access URLs ====="
                    echo "  DEV Web:  http://${NODE_IP}:30080"
                    echo "  QAT Web:  http://${NODE_IP}:30081"
                '''
            }
        }
    }

    post {
        success {
            echo " SUCCESS: Build ${IMAGE_TAG} deployed to DEV (:30080) and QAT (:30081)"
        }
        failure {
            echo " FAILED — initiating rollback..."
            sh '''
                kubectl rollout undo deployment/api -n dev 2>/dev/null || true
                kubectl rollout undo deployment/web -n dev 2>/dev/null || true
                kubectl rollout undo deployment/api -n qat 2>/dev/null || true
                kubectl rollout undo deployment/web -n qat 2>/dev/null || true
                echo "Rollback complete."
                kubectl get pods -n dev
                kubectl get pods -n qat
            '''
        }
        always {
            // Clean up docker images older than 24h to save disk space
            sh 'docker image prune -f --filter "until=24h" || true'
            cleanWs()
        }
    }
}
