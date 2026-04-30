pipeline {
    agent any

    // ── Global environment variables ─────────────────────────────────────────
    environment {
        // Fix Windows SChannel SSL issue with GitHub
        GIT_SSL_NO_VERIFY = 'true'

        // Full Python path — required because Jenkins SYSTEM account lacks user PATH
        PYTHON            = 'C:\\Users\\moksh\\AppData\\Local\\Programs\\Python\\Python314\\python.exe'

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

        // Jenkins credential IDs (configure in Jenkins → Manage Credentials)
        AWS_CREDENTIALS   = 'aws-credentials'
        KUBECONFIG_CRED   = 'kubeconfig'
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
                // Declarative Pipeline auto-checks out — just confirm what was checked out
                echo "📥 Source checked out — Branch: ${env.GIT_BRANCH}, Commit: ${env.GIT_COMMIT?.take(7)}"
            }
        }

        // ── 2. INSTALL DEPENDENCIES ───────────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo '📦 Installing Python dependencies...'
                bat '''
                    "%PYTHON%" -m venv .venv
                    call .venv\\Scripts\\activate.bat
                    "%PYTHON%" -m pip install --upgrade pip
                    .venv\\Scripts\\pip install -r requirements.txt
                    .venv\\Scripts\\pip install pytest flake8
                '''
            }
        }

        // ── 3. CODE QUALITY (LINT) ────────────────────────────────────────────
        stage('Lint') {
            steps {
                echo '🔍 Running flake8 lint checks (warnings only — non-blocking)...'
                bat '''
                    .venv\\Scripts\\flake8 app.py --max-line-length=120 --exclude=.venv,venv,__pycache__ --count --statistics || exit /b 0
                '''
            }
        }

        // ── 4. UNIT TESTS ─────────────────────────────────────────────────────
        stage('Test') {
            steps {
                echo '🧪 Running unit tests...'
                bat '''
                    if exist tests (
                        .venv\\Scripts\\pytest tests\\ -v --tb=short --junitxml=test-results.xml
                    ) else (
                        echo No tests directory found - skipping tests.
                    )
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
                bat "docker build -t ${IMAGE_FULL} -t ${IMAGE_LATEST} ."
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
                    bat '''
                        aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                        docker push %IMAGE_FULL%
                        docker push %IMAGE_LATEST%
                    '''
                }
            }
        }

        // ── 7. DEPLOY TO KUBERNETES (EKS) ─────────────────────────────────────
        stage('Deploy to EKS') {
            steps {
                echo "☸️  Deploying to Kubernetes namespace: ${K8S_NAMESPACE}"
                withCredentials([file(credentialsId: "${KUBECONFIG_CRED}", variable: 'KUBECONFIG')]) {
                    bat '''
                        kubectl apply -f k8s\\secret.yaml      --namespace=%K8S_NAMESPACE%
                        kubectl apply -f k8s\\deployment.yaml  --namespace=%K8S_NAMESPACE%
                        kubectl apply -f k8s\\service.yaml     --namespace=%K8S_NAMESPACE%
                        kubectl set image deployment/%K8S_DEPLOYMENT% %K8S_DEPLOYMENT%=%IMAGE_FULL% --namespace=%K8S_NAMESPACE%
                        kubectl rollout status deployment/%K8S_DEPLOYMENT% --namespace=%K8S_NAMESPACE% --timeout=300s
                    '''
                }
            }
        }

        // ── 8. SMOKE TEST ─────────────────────────────────────────────────────
        stage('Smoke Test') {
            steps {
                echo '💨 Running smoke test against the deployed service...'
                withCredentials([file(credentialsId: "${KUBECONFIG_CRED}", variable: 'KUBECONFIG')]) {
                    bat '''
                        for /f "tokens=*" %%i in ('kubectl get svc %K8S_DEPLOYMENT% --namespace=%K8S_NAMESPACE% -o jsonpath="{.status.loadBalancer.ingress[0].hostname}"') do set LB_HOST=%%i
                        if "%LB_HOST%"=="" (
                            for /f "tokens=*" %%i in ('kubectl get svc %K8S_DEPLOYMENT% --namespace=%K8S_NAMESPACE% -o jsonpath="{.status.loadBalancer.ingress[0].ip}"') do set LB_HOST=%%i
                        )
                        echo Testing endpoint: http://%LB_HOST%
                        curl -f -s -o NUL -w "HTTP Status: %%{http_code}" http://%LB_HOST%/ || exit 1
                    '''
                }
            }
        }

        // ── 9. CLEANUP ────────────────────────────────────────────────────────
        stage('Cleanup') {
            steps {
                echo '🧹 Removing local Docker images...'
                bat '''
                    docker rmi %IMAGE_FULL%   || exit /b 0
                    docker rmi %IMAGE_LATEST%  || exit /b 0
                    docker image prune -f      || exit /b 0
                '''
            }
        }
    }

    // ── POST ACTIONS ──────────────────────────────────────────────────────────
    post {
        success {
            echo "✅ BUILD & DEPLOY SUCCESSFUL — Image: ${IMAGE_FULL} | Build: #${env.BUILD_NUMBER}"
        }
        failure {
            echo "❌ PIPELINE FAILED — Build: #${env.BUILD_NUMBER} — Check console output for details."
        }
        always {
            echo '📊 Pipeline finished. Cleaning workspace...'
            cleanWs()
        }
    }
}
