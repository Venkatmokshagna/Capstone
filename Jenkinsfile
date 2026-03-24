// ─────────────────────────────────────────────────────────────────
// Waterborne Disease Monitor — Jenkins CI/CD Pipeline
//
// Required Jenkins Credentials (Manage Jenkins → Credentials):
//   gcp-service-account-key  : Secret File  → your jenkins-key.json
//   github-credentials       : Username/Pwd → GitHub token
//
// Required Jenkins Plugins:
//   Docker Pipeline, Google Kubernetes Engine, Kubernetes CLI, Pipeline
//
// Environment Variables — update these before running:
//   GCP_PROJECT_ID : your Google Cloud Project ID
//   GCR_REGION     : GAR region (e.g. asia-south1)
//   GKE_CLUSTER    : your GKE cluster name
//   GKE_ZONE       : your GKE cluster zone/region
// ─────────────────────────────────────────────────────────────────

pipeline {
    agent any

    environment {
        // ── GCP / GKE Configuration ─────────────────────────────
        GCP_PROJECT_ID  = 'YOUR_PROJECT_ID'         // ← Replace this
        GCR_REGION      = 'asia-south1'              // ← Replace if different
        GKE_CLUSTER     = 'waterborne-cluster'
        GKE_ZONE        = 'asia-south1'
        K8S_NAMESPACE   = 'waterborne'

        // ── Image Configuration ─────────────────────────────────
        IMAGE_NAME      = "${GCR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/waterborne-repo/waterborne-app"
        IMAGE_TAG       = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'latest'}"
        FULL_IMAGE      = "${IMAGE_NAME}:${IMAGE_TAG}"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()            // Prevent parallel deploys
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // ── Stage 1: Checkout ────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "📥 Checking out source code..."
                checkout scm
                sh 'echo "Branch: ${GIT_BRANCH} | Commit: ${GIT_COMMIT}"'
            }
        }

        // ── Stage 2: Build Docker Image ──────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image: ${FULL_IMAGE}"
                sh """
                    docker build \
                        --tag ${FULL_IMAGE} \
                        --tag ${IMAGE_NAME}:latest \
                        --file Dockerfile \
                        .
                """
            }
        }

        // ── Stage 3: Push to Google Artifact Registry ────────────
        stage('Push to Google Artifact Registry') {
            steps {
                echo "⬆️  Pushing image to GAR..."
                withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                        # Authenticate with GCP
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT_ID}

                        # Configure Docker to use gcloud as credential helper
                        gcloud auth configure-docker ${GCR_REGION}-docker.pkg.dev --quiet

                        # Push both the versioned tag and latest
                        docker push ${FULL_IMAGE}
                        docker push ${IMAGE_NAME}:latest
                    """
                }
            }
        }

        // ── Stage 4: Update K8s Deployment Image Tag ─────────────
        stage('Update Deployment Manifest') {
            steps {
                echo "✏️  Updating Flask deployment image tag to ${IMAGE_TAG}..."
                sh """
                    sed -i 's|image: ${GCR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/waterborne-repo/waterborne-app:.*|image: ${FULL_IMAGE}|g' \\
                        k8s/flask-deployment.yaml
                    echo "Updated image in k8s/flask-deployment.yaml:"
                    grep 'image:' k8s/flask-deployment.yaml
                """
            }
        }

        // ── Stage 5: Deploy to GKE ───────────────────────────────
        stage('Deploy to GKE') {
            steps {
                echo "🚀 Deploying to GKE cluster: ${GKE_CLUSTER}..."
                withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                        # Authenticate and get cluster credentials
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT_ID}
                        gcloud container clusters get-credentials ${GKE_CLUSTER} \
                            --region ${GKE_ZONE} \
                            --project ${GCP_PROJECT_ID}

                        # Apply all manifests in order
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/mysql-secret.yaml
                        kubectl apply -f k8s/mysql-configmap.yaml
                        kubectl apply -f k8s/mysql-init-configmap.yaml
                        kubectl apply -f k8s/mysql-pvc.yaml
                        kubectl apply -f k8s/mysql-deployment.yaml
                        kubectl apply -f k8s/mysql-service.yaml
                        kubectl apply -f k8s/flask-deployment.yaml
                        kubectl apply -f k8s/flask-service.yaml

                        # Wait for Flask rollout to complete
                        kubectl rollout status deployment/flask-app \
                            --namespace=${K8S_NAMESPACE} \
                            --timeout=5m
                    """
                }
            }
        }

        // ── Stage 6: Smoke Test ──────────────────────────────────
        stage('Smoke Test') {
            steps {
                echo "🔍 Running post-deploy smoke test..."
                withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud container clusters get-credentials ${GKE_CLUSTER} \
                            --region ${GKE_ZONE} --project ${GCP_PROJECT_ID}

                        # Check all pods are Running
                        kubectl get pods --namespace=${K8S_NAMESPACE}

                        # Get the external IP of the Flask service
                        echo "Flask service external IP:"
                        kubectl get svc flask-service --namespace=${K8S_NAMESPACE}
                    """
                }
            }
        }
    }

    post {
        success {
            echo """
            ✅ Deployment Successful!
            Image: ${FULL_IMAGE}
            Cluster: ${GKE_CLUSTER}
            Namespace: ${K8S_NAMESPACE}

            Run this to get the public URL:
              kubectl get svc flask-service -n ${K8S_NAMESPACE}
            """
        }
        failure {
            echo "❌ Pipeline failed. Check logs above for details."
        }
        always {
            // Clean up local Docker images to save disk space
            sh "docker rmi ${FULL_IMAGE} ${IMAGE_NAME}:latest || true"
        }
    }
}
