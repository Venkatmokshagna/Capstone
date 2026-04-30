pipeline {
    agent any

    // ── Global environment variables ─────────────────────────────────────────
    environment {
        // AWS & ECR
        AWS_REGION        = 'eu-north-1'
        ECR_REGISTRY      = '870676149845.dkr.ecr.eu-north-1.amazonaws.com'
        ECR_REPO          = 'waterborne-app'
        IMAGE_TAG         = "${env.BUILD_NUMBER}"
        IMAGE_FULL        = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
        IMAGE_LATEST      = "${ECR_REGISTRY}/${ECR_REPO}:latest"

        // Kubernetes
        K8S_DEPLOYMENT    = 'waterborne-app'
        K8S_NAMESPACE     = 'default'

        // Jenkins credential IDs (configure these in Jenkins → Manage Credentials)
        AWS_CREDENTIALS   = 'aws-credentials'   // AWS Access Key + Secret
        KUBECONFIG_CRED   = 'kubeconfig'         // kubeconfig file secret
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        // ── 1. CHECKOUT ───────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
            }
        }

        // ── 2. INSTALL DEPENDENCIES ───────────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo '📦 Installing Python dependencies...'
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest flake8
                '''
            }
        }

        // ── 3. CODE QUALITY (LINT) ────────────────────────────────────────────
        stage('Lint') {
            steps {
                echo '🔍 Running flake8 lint checks...'
                sh '''
                    . .venv/bin/activate
                    flake8 app.py \
                        --max-line-length=120 \
                        --exclude=.venv,venv,__pycache__ \
                        --count --statistics
                '''
            }
        }

        // ── 4. UNIT TESTS ─────────────────────────────────────────────────────
        stage('Test') {
            steps {
                echo '🧪 Running unit tests...'
                sh '''
                    . .venv/bin/activate
                    # Run tests if tests/ directory exists, else skip gracefully
                    if [ -d "tests" ]; then
                        pytest tests/ -v --tb=short --junitxml=test-results.xml
                    else
                        echo "No tests/ directory found — skipping tests."
                    fi
                '''
            }
            post {
                always {
                    script {
                        if (fileExists('test-results.xml')) {
                            junit 'test-results.xml'
                        }
                    }
                }
            }
        }

        // ── 5. DOCKER BUILD ───────────────────────────────────────────────────
        stage('Docker Build') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_FULL}"
                sh "docker build -t ${IMAGE_FULL} -t ${IMAGE_LATEST} ."
            }
        }

        // ── 6. PUSH TO AWS ECR ────────────────────────────────────────────────
        stage('Push to ECR') {
            steps {
                echo "🚀 Pushing image to AWS ECR..."
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: "${AWS_CREDENTIALS}",
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh '''
                        aws ecr get-login-password --region ${AWS_REGION} \
                            | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker push ${IMAGE_FULL}
                        docker push ${IMAGE_LATEST}
                    '''
                }
            }
        }

        // ── 7. DEPLOY TO KUBERNETES (EKS) ─────────────────────────────────────
        stage('Deploy to EKS') {
            steps {
                echo "☸️  Deploying to Kubernetes namespace: ${K8S_NAMESPACE}"
                withCredentials([file(credentialsId: "${KUBECONFIG_CRED}", variable: 'KUBECONFIG')]) {
                    sh '''
                        # Apply latest k8s manifests
                        kubectl apply -f k8s/secret.yaml      --namespace=${K8S_NAMESPACE}
                        kubectl apply -f k8s/deployment.yaml  --namespace=${K8S_NAMESPACE}
                        kubectl apply -f k8s/service.yaml     --namespace=${K8S_NAMESPACE}

                        # Rolling update: set the new image tag
                        kubectl set image deployment/${K8S_DEPLOYMENT} \
                            ${K8S_DEPLOYMENT}=${IMAGE_FULL} \
                            --namespace=${K8S_NAMESPACE}

                        # Wait for rollout to complete (timeout 5 min)
                        kubectl rollout status deployment/${K8S_DEPLOYMENT} \
                            --namespace=${K8S_NAMESPACE} \
                            --timeout=300s
                    '''
                }
            }
        }

        // ── 8. SMOKE TEST ─────────────────────────────────────────────────────
        stage('Smoke Test') {
            steps {
                echo '💨 Running smoke test against the deployed service...'
                withCredentials([file(credentialsId: "${KUBECONFIG_CRED}", variable: 'KUBECONFIG')]) {
                    sh '''
                        # Get the LoadBalancer external IP / hostname
                        LB_HOST=$(kubectl get svc ${K8S_DEPLOYMENT} \
                            --namespace=${K8S_NAMESPACE} \
                            -o jsonpath="{.status.loadBalancer.ingress[0].hostname}")

                        if [ -z "$LB_HOST" ]; then
                            LB_HOST=$(kubectl get svc ${K8S_DEPLOYMENT} \
                                --namespace=${K8S_NAMESPACE} \
                                -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
                        fi

                        echo "Testing endpoint: http://${LB_HOST}"
                        # Retry up to 5 times with 10s delay
                        for i in 1 2 3 4 5; do
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${LB_HOST}/ || echo "000")
                            if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
                                echo "✅ Smoke test passed (HTTP ${HTTP_CODE})"
                                exit 0
                            fi
                            echo "Attempt $i failed (HTTP ${HTTP_CODE}), retrying in 10s..."
                            sleep 10
                        done
                        echo "❌ Smoke test failed after 5 attempts"
                        exit 1
                    '''
                }
            }
        }

        // ── 9. CLEANUP LOCAL DOCKER IMAGES ────────────────────────────────────
        stage('Cleanup') {
            steps {
                echo '🧹 Removing local Docker images to free disk space...'
                sh '''
                    docker rmi ${IMAGE_FULL}  || true
                    docker rmi ${IMAGE_LATEST} || true
                    docker image prune -f      || true
                '''
            }
        }
    }

    // ── POST ACTIONS ──────────────────────────────────────────────────────────
    post {
        success {
            echo """
            ╔══════════════════════════════════════════════╗
            ║  ✅  BUILD & DEPLOY SUCCESSFUL               ║
            ║  Image : ${IMAGE_FULL}
            ║  Build : #${env.BUILD_NUMBER}               ║
            ╚══════════════════════════════════════════════╝
            """
        }
        failure {
            echo """
            ╔══════════════════════════════════════════════╗
            ║  ❌  PIPELINE FAILED                         ║
            ║  Build : #${env.BUILD_NUMBER}               ║
            ║  Check console output for details.           ║
            ╚══════════════════════════════════════════════╝
            """
        }
        always {
            echo '📊 Pipeline finished. Cleaning workspace...'
            cleanWs()
        }
    }
}
