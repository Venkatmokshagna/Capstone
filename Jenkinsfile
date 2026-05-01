pipeline {
    agent any

    // ΓöÇΓöÇ Global environment variables ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    environment {
        // Fix Windows SChannel SSL issue with GitHub
        GIT_SSL_NO_VERIFY = 'true'

        // Full Python path ΓÇö required because Jenkins SYSTEM account lacks user PATH
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

        // Jenkins credential IDs (configure in Jenkins ΓåÆ Manage Credentials)
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

        // ΓöÇΓöÇ 1. CHECKOUT ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Checkout') {
            steps {
                // Declarative Pipeline auto-checks out ΓÇö just confirm what was checked out
                echo "≡ƒôÑ Source checked out ΓÇö Branch: ${env.GIT_BRANCH}, Commit: ${env.GIT_COMMIT?.take(7)}"
            }
        }

        // ΓöÇΓöÇ 2. INSTALL DEPENDENCIES ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Install Dependencies') {
            steps {
                echo '≡ƒôª Installing Python dependencies...'
                bat '''
                    "%PYTHON%" -m venv .venv
                    call .venv\\Scripts\\activate.bat
                    "%PYTHON%" -m pip install --upgrade pip
                    .venv\\Scripts\\pip install -r requirements.txt
                    .venv\\Scripts\\pip install pytest flake8
                '''
            }
        }

        // ΓöÇΓöÇ 3. CODE QUALITY (LINT) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Lint') {
            steps {
                echo '≡ƒöì Running flake8 lint checks (warnings only ΓÇö non-blocking)...'
                bat '''
                    .venv\\Scripts\\flake8 app.py --max-line-length=120 --exclude=.venv,venv,__pycache__ --count --statistics || exit /b 0
                '''
            }
        }

        // ΓöÇΓöÇ 4. UNIT TESTS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Test') {
            steps {
                echo '≡ƒº¬ Running unit tests...'
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

        // ΓöÇΓöÇ 5. DOCKER BUILD ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Docker Build') {
            steps {
                echo "≡ƒÉ│ Building Docker image: ${IMAGE_FULL}"
                bat "docker build -t ${IMAGE_FULL} -t ${IMAGE_LATEST} ."
            }
        }

        // ----------------------------------------------------------------------------------------------------
        stage('Push to ECR') {
            steps {
                echo "🚀 Pushing image to AWS ECR..."
                withCredentials([
                    usernamePassword(
                        credentialsId: "${AWS_CREDENTIALS}",
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    bat '''
                        set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID%
                        set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY%
                        aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
                        docker push %IMAGE_FULL%
                        docker push %IMAGE_LATEST%
                    '''
                }
            }
        }

        // ΓöÇΓöÇ 7. DEPLOY TO KUBERNETES (EKS) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Deploy to EKS') {
            steps {
                echo "Γÿ╕∩╕Å  Deploying to Kubernetes namespace: ${K8S_NAMESPACE}"
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

        // ΓöÇΓöÇ 8. SMOKE TEST ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Smoke Test') {
            steps {
                echo '≡ƒÆ¿ Running smoke test against the deployed service...'
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

        // ΓöÇΓöÇ 9. CLEANUP ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        stage('Cleanup') {
            steps {
                echo '≡ƒº╣ Removing local Docker images...'
                bat '''
                    docker rmi %IMAGE_FULL%   || exit /b 0
                    docker rmi %IMAGE_LATEST%  || exit /b 0
                    docker image prune -f      || exit /b 0
                '''
            }
        }
    }

    // ΓöÇΓöÇ POST ACTIONS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    post {
        success {
            echo "Γ£à BUILD & DEPLOY SUCCESSFUL ΓÇö Image: ${IMAGE_FULL} | Build: #${env.BUILD_NUMBER}"
        }
        failure {
            echo "Γ¥î PIPELINE FAILED ΓÇö Build: #${env.BUILD_NUMBER} ΓÇö Check console output for details."
        }
        always {
            echo '≡ƒôè Pipeline finished. Cleaning workspace...'
            cleanWs()
        }
    }
}
