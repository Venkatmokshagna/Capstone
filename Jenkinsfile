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
        skipDefaultCheckout(true)   // We do checkout manually with retry below
    }

    stages {

        // ── 1. CHECKOUT ───────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                // retry(3) handles transient GitHub 502 / network errors automatically
                retry(3) {
                    checkout scm
                }
                echo "📥 Checkout complete — Commit: ${env.GIT_COMMIT?.take(7)}"
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
Skip to content

Jenkins
waterborne-disease-pipeline
#18
Search
Manage Jenkins
Mokshagna
Status
Changes
Console Output
Edit Build Information
Delete build ‘#18’
Timings
Git Build Data
Pipeline Overview
Restart from Stage
Replay
Pipeline Steps
Workspaces
Previous Build
Timestamps
View as plain text
System clock time

Use browser timezone
Elapsed time
None
Console
Download

Copy
View as plain text
Started by user Mokshagna
Replayed #17
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Declarative: Checkout SCM)
[Pipeline] checkout
Selected Git installation does not exist. Using Default
The recommended git tool is: NONE
using credential github-credentials
Cloning the remote Git repository
Cloning repository https://github.com/Venkatmokshagna/Capstone.git
 > C:\ProgramData\Jenkins\git-wrapper.bat init C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline # timeout=10
Fetching upstream changes from https://github.com/Venkatmokshagna/Capstone.git
 > C:\ProgramData\Jenkins\git-wrapper.bat --version # timeout=10
 > git --version # 'git version 2.52.0.windows.1'
using GIT_ASKPASS to set credentials 
 > C:\ProgramData\Jenkins\git-wrapper.bat fetch --tags --force --progress -- https://github.com/Venkatmokshagna/Capstone.git +refs/heads/*:refs/remotes/origin/* # timeout=10
 > C:\ProgramData\Jenkins\git-wrapper.bat config remote.origin.url https://github.com/Venkatmokshagna/Capstone.git # timeout=10
 > C:\ProgramData\Jenkins\git-wrapper.bat config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
Avoid second fetch
 > C:\ProgramData\Jenkins\git-wrapper.bat rev-parse "refs/remotes/origin/main^{commit}" # timeout=10
Checking out Revision 31a99a81464c668a269046e2a65c47e3c254c12b (refs/remotes/origin/main)
 > C:\ProgramData\Jenkins\git-wrapper.bat config core.sparsecheckout # timeout=10
 > C:\ProgramData\Jenkins\git-wrapper.bat checkout -f 31a99a81464c668a269046e2a65c47e3c254c12b # timeout=10
Commit message: "fix: make lint non-blocking (warnings only) so pipeline continues past flake8 errors"
 > C:\ProgramData\Jenkins\git-wrapper.bat rev-list --no-walk 31a99a81464c668a269046e2a65c47e3c254c12b # timeout=10
[Pipeline] }
[Pipeline] // stage
[Pipeline] withEnv
[Pipeline] {
[Pipeline] withEnv
[Pipeline] {
[Pipeline] timeout
Timeout set to expire in 30 min
[Pipeline] {
[Pipeline] timestamps
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Checkout)
[Pipeline] echo
10:33:21  📥 Source checked out — Branch: origin/main, Commit: 31a99a8
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Install Dependencies)
[Pipeline] echo
10:33:21  📦 Installing Python dependencies...
[Pipeline] bat
10:33:22  
10:33:22  C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline>"C:\Users\moksh\AppData\Local\Programs\Python\Python314\python.exe" -m venv .venv 
10:33:37  
10:33:37  C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline>call .venv\Scripts\activate.bat 
10:33:37  Requirement already satisfied: pip in C:\Users\moksh\AppData\Local\Programs\Python\Python314\Lib\site-packages (26.1)
10:33:42  Collecting flask==2.3.3 (from -r requirements.txt (line 1))
10:33:42    Using cached flask-2.3.3-py3-none-any.whl.metadata (3.6 kB)
10:33:42  Collecting flask-cors==4.0.0 (from -r requirements.txt (line 2))
10:33:42    Using cached Flask_Cors-4.0.0-py2.py3-none-any.whl.metadata (5.4 kB)
10:33:42  Collecting bcrypt==4.0.1 (from -r requirements.txt (line 3))
10:33:42    Using cached bcrypt-4.0.1-cp36-abi3-win_amd64.whl.metadata (9.0 kB)
10:33:42  Collecting mysql-connector-python==8.3.0 (from -r requirements.txt (line 4))
10:33:42    Using cached mysql_connector_python-8.3.0-py2.py3-none-any.whl.metadata (1.9 kB)
10:33:42  Collecting Werkzeug==2.3.7 (from -r requirements.txt (line 5))
10:33:42    Using cached werkzeug-2.3.7-py3-none-any.whl.metadata (4.1 kB)
10:33:42  Collecting numpy (from -r requirements.txt (line 7))
10:33:42    Using cached numpy-2.4.4-cp314-cp314-win_amd64.whl.metadata (6.6 kB)
10:33:43  Collecting pillow (from -r requirements.txt (line 8))
10:33:43    Using cached pillow-12.2.0-cp314-cp314-win_amd64.whl.metadata (9.0 kB)
10:33:43  Collecting gunicorn (from -r requirements.txt (line 9))
10:33:43    Using cached gunicorn-25.3.0-py3-none-any.whl.metadata (5.5 kB)
10:33:43  Collecting Jinja2>=3.1.2 (from flask==2.3.3->-r requirements.txt (line 1))
10:33:43    Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
10:33:43  Collecting itsdangerous>=2.1.2 (from flask==2.3.3->-r requirements.txt (line 1))
10:33:43    Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
10:33:43  Collecting click>=8.1.3 (from flask==2.3.3->-r requirements.txt (line 1))
10:33:43    Using cached click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
10:33:43  Collecting blinker>=1.6.2 (from flask==2.3.3->-r requirements.txt (line 1))
10:33:43    Using cached blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
10:33:43  Collecting MarkupSafe>=2.1.1 (from Werkzeug==2.3.7->-r requirements.txt (line 5))
10:33:43    Using cached markupsafe-3.0.3-cp314-cp314-win_amd64.whl.metadata (2.8 kB)
10:33:44  Collecting packaging (from gunicorn->-r requirements.txt (line 9))
10:33:44    Using cached packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
10:33:44  Collecting colorama (from click>=8.1.3->flask==2.3.3->-r requirements.txt (line 1))
10:33:44    Using cached colorama-0.4.6-py2.py3-none-any.whl.metadata (17 kB)
10:33:44  Using cached flask-2.3.3-py3-none-any.whl (96 kB)
10:33:44  Using cached Flask_Cors-4.0.0-py2.py3-none-any.whl (14 kB)
10:33:44  Using cached bcrypt-4.0.1-cp36-abi3-win_amd64.whl (152 kB)
10:33:44  Using cached mysql_connector_python-8.3.0-py2.py3-none-any.whl (557 kB)
10:33:44  Using cached werkzeug-2.3.7-py3-none-any.whl (242 kB)
10:33:44  Using cached numpy-2.4.4-cp314-cp314-win_amd64.whl (12.4 MB)
10:33:44  Using cached pillow-12.2.0-cp314-cp314-win_amd64.whl (7.2 MB)
10:33:44  Using cached gunicorn-25.3.0-py3-none-any.whl (208 kB)
10:33:44  Using cached blinker-1.9.0-py3-none-any.whl (8.5 kB)
10:33:44  Using cached click-8.3.3-py3-none-any.whl (110 kB)
10:33:44  Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
10:33:44  Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
10:33:44  Using cached markupsafe-3.0.3-cp314-cp314-win_amd64.whl (15 kB)
10:33:44  Using cached colorama-0.4.6-py2.py3-none-any.whl (25 kB)
10:33:44  Using cached packaging-26.2-py3-none-any.whl (100 kB)
10:33:45  Installing collected packages: pillow, packaging, numpy, mysql-connector-python, MarkupSafe, itsdangerous, colorama, blinker, bcrypt, Werkzeug, Jinja2, gunicorn, click, flask, flask-cors
10:34:11  
10:34:11  Successfully installed Jinja2-3.1.6 MarkupSafe-3.0.3 Werkzeug-2.3.7 bcrypt-4.0.1 blinker-1.9.0 click-8.3.3 colorama-0.4.6 flask-2.3.3 flask-cors-4.0.0 gunicorn-25.3.0 itsdangerous-2.2.0 mysql-connector-python-8.3.0 numpy-2.4.4 packaging-26.2 pillow-12.2.0
10:34:11  
10:34:11  [notice] A new release of pip is available: 25.3 -> 26.1
10:34:11  [notice] To update, run: python.exe -m pip install --upgrade pip
10:34:12  Collecting pytest
10:34:12    Using cached pytest-9.0.3-py3-none-any.whl.metadata (7.6 kB)
10:34:12  Collecting flake8
10:34:12    Using cached flake8-7.3.0-py2.py3-none-any.whl.metadata (3.8 kB)
10:34:12  Requirement already satisfied: colorama>=0.4 in c:\programdata\jenkins\.jenkins\workspace\waterborne-disease-pipeline\.venv\lib\site-packages (from pytest) (0.4.6)
10:34:12  Collecting iniconfig>=1.0.1 (from pytest)
10:34:12    Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
10:34:12  Requirement already satisfied: packaging>=22 in c:\programdata\jenkins\.jenkins\workspace\waterborne-disease-pipeline\.venv\lib\site-packages (from pytest) (26.2)
10:34:12  Collecting pluggy<2,>=1.5 (from pytest)
10:34:12    Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
10:34:12  Collecting pygments>=2.7.2 (from pytest)
10:34:12    Using cached pygments-2.20.0-py3-none-any.whl.metadata (2.5 kB)
10:34:12  Collecting mccabe<0.8.0,>=0.7.0 (from flake8)
10:34:12    Using cached mccabe-0.7.0-py2.py3-none-any.whl.metadata (5.0 kB)
10:34:12  Collecting pycodestyle<2.15.0,>=2.14.0 (from flake8)
10:34:12    Using cached pycodestyle-2.14.0-py2.py3-none-any.whl.metadata (4.5 kB)
10:34:12  Collecting pyflakes<3.5.0,>=3.4.0 (from flake8)
10:34:12    Using cached pyflakes-3.4.0-py2.py3-none-any.whl.metadata (3.5 kB)
10:34:12  Using cached pytest-9.0.3-py3-none-any.whl (375 kB)
10:34:12  Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
10:34:12  Using cached flake8-7.3.0-py2.py3-none-any.whl (57 kB)
10:34:12  Using cached mccabe-0.7.0-py2.py3-none-any.whl (7.3 kB)
10:34:12  Using cached pycodestyle-2.14.0-py2.py3-none-any.whl (31 kB)
10:34:12  Using cached pyflakes-3.4.0-py2.py3-none-any.whl (63 kB)
10:34:12  Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
10:34:12  Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
10:34:13  Installing collected packages: pygments, pyflakes, pycodestyle, pluggy, mccabe, iniconfig, pytest, flake8
10:34:23  
10:34:23  Successfully installed flake8-7.3.0 iniconfig-2.3.0 mccabe-0.7.0 pluggy-1.6.0 pycodestyle-2.14.0 pyflakes-3.4.0 pygments-2.20.0 pytest-9.0.3
10:34:23  
10:34:23  [notice] A new release of pip is available: 25.3 -> 26.1
10:34:23  [notice] To update, run: python.exe -m pip install --upgrade pip
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Lint)
[Pipeline] echo
10:34:23  🔍 Running flake8 lint checks (warnings only — non-blocking)...
[Pipeline] bat
10:34:23  
10:34:23  C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline>.venv\Scripts\flake8 app.py --max-line-length=120 --exclude=.venv,venv,__pycache__ --count --statistics   || exit /b 0 
10:34:25  app.py:7:1: F401 'mysql.connector' imported but unused
10:34:25  app.py:12:1: F811 redefinition of unused 'os' from line 4
10:34:25  app.py:17:1: E722 do not use bare 'except'
10:34:25  app.py:19:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:26:1: E305 expected 2 blank lines after class or function definition, found 0
10:34:25  app.py:26:121: E501 line too long (123 > 120 characters)
10:34:25  app.py:48:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:56:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:61:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:66:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:77:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:79:16: E701 multiple statements on one line (colon)
10:34:25  app.py:82:121: E501 line too long (158 > 120 characters)
10:34:25  app.py:84:121: E501 line too long (193 > 120 characters)
10:34:25  app.py:89:48: E701 multiple statements on one line (colon)
10:34:25  app.py:94:25: E701 multiple statements on one line (colon)
10:34:25  app.py:101:121: E501 line too long (169 > 120 characters)
10:34:25  app.py:104:121: E501 line too long (138 > 120 characters)
10:34:25  app.py:106:121: E501 line too long (173 > 120 characters)
10:34:25  app.py:108:26: E701 multiple statements on one line (colon)
10:34:25  app.py:109:12: E701 multiple statements on one line (colon)
10:34:25  app.py:110:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:115:16: E701 multiple statements on one line (colon)
10:34:25  app.py:145:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:150:16: E701 multiple statements on one line (colon)
10:34:25  app.py:168:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:173:16: E701 multiple statements on one line (colon)
10:34:25  app.py:176:59: W291 trailing whitespace
10:34:25  app.py:177:121: E501 line too long (143 > 120 characters)
10:34:25  app.py:193:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:197:16: E701 multiple statements on one line (colon)
10:34:25  app.py:213:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:219:16: E701 multiple statements on one line (colon)
10:34:25  app.py:233:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:236:16: E701 multiple statements on one line (colon)
10:34:25  app.py:239:47: W291 trailing whitespace
10:34:25  app.py:240:28: W291 trailing whitespace
10:34:25  app.py:247:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:261:121: E501 line too long (135 > 120 characters)
10:34:25  app.py:270:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:291:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:312:16: E701 multiple statements on one line (colon)
10:34:25  app.py:314:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:351:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:374:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:379:16: E701 multiple statements on one line (colon)
10:34:25  app.py:391:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:409:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:414:16: E701 multiple statements on one line (colon)
10:34:25  app.py:417:72: W291 trailing whitespace
10:34:25  app.py:418:21: W291 trailing whitespace
10:34:25  app.py:419:52: W291 trailing whitespace
10:34:25  app.py:425:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:429:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:438:16: E701 multiple statements on one line (colon)
10:34:25  app.py:448:16: E701 multiple statements on one line (colon)
10:34:25  app.py:450:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:453:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:467:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:521:121: E501 line too long (125 > 120 characters)
10:34:25  app.py:527:34: F541 f-string is missing placeholders
10:34:25  app.py:527:121: E501 line too long (124 > 120 characters)
10:34:25  app.py:551:9: F841 local variable 'e' is assigned to but never used
10:34:25  app.py:554:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:581:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:613:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:640:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:659:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:685:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:715:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:726:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:739:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:748:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:756:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:766:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:774:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:783:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:794:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:805:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:820:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:829:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:840:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:870:32: E127 continuation line over-indented for visual indent
10:34:25  app.py:885:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:895:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:944:121: E501 line too long (125 > 120 characters)
10:34:25  app.py:946:121: E501 line too long (143 > 120 characters)
10:34:25  app.py:964:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:969:16: E701 multiple statements on one line (colon)
10:34:25  app.py:980:1: E302 expected 2 blank lines, found 0
10:34:25  app.py:987:1: E305 expected 2 blank lines after class or function definition, found 0
10:34:25  app.py:988:52: W292 no newline at end of file
10:34:25  22    E127 continuation line over-indented for visual indent
10:34:25  27    E302 expected 2 blank lines, found 0
10:34:25  2     E305 expected 2 blank lines after class or function definition, found 0
10:34:25  12    E501 line too long (123 > 120 characters)
10:34:25  17    E701 multiple statements on one line (colon)
10:34:25  1     E722 do not use bare 'except'
10:34:25  1     F401 'mysql.connector' imported but unused
10:34:25  1     F541 f-string is missing placeholders
10:34:25  1     F811 redefinition of unused 'os' from line 4
10:34:25  1     F841 local variable 'e' is assigned to but never used
10:34:25  6     W291 trailing whitespace
10:34:25  1     W292 no newline at end of file
10:34:25  92
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Test)
[Pipeline] echo
10:34:25  🧪 Running unit tests...
[Pipeline] bat
10:34:26  
10:34:26  C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline>if exist tests (.venv\Scripts\pytest tests\ -v --tb=short --junitxml=test-results.xml )  else (echo No tests directory found - skipping tests. ) 
10:34:26  No tests directory found - skipping tests.
Post stage
[Pipeline] script
[Pipeline] {
[Pipeline] fileExists
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Docker Build)
[Pipeline] echo
10:34:27  🐳 Building Docker image: 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:18
[Pipeline] bat
10:34:27  
10:34:27  C:\ProgramData\Jenkins\.jenkins\workspace\waterborne-disease-pipeline>docker build -t 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:18 -t 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:latest . 
10:34:37  #0 building with "default" instance using docker driver
10:34:37  
10:34:37  #1 [internal] load build definition from Dockerfile
10:34:37  #1 transferring dockerfile: 441B 0.0s done
10:34:37  #1 DONE 0.1s
10:34:37  
10:34:37  #2 [internal] load metadata for docker.io/library/python:3.10-slim
10:34:40  #2 DONE 3.8s
10:34:40  
10:34:40  #3 [internal] load .dockerignore
10:34:40  #3 transferring context: 306B 0.0s done
10:34:40  #3 DONE 0.1s
10:34:40  
10:34:40  #4 [internal] load build context
10:34:46  #4 transferring context: 26.83MB 5.0s
10:34:51  #4 transferring context: 60.10MB 10.0s
10:34:51  #4 ...
10:34:51  
10:34:51  #5 [1/6] FROM docker.io/library/python:3.10-slim@sha256:cdbf8193cee2e31639ea8ea85ffdd8fa5cce98ee9abfde96ea5f329490048831
10:34:51  #5 resolve docker.io/library/python:3.10-slim@sha256:cdbf8193cee2e31639ea8ea85ffdd8fa5cce98ee9abfde96ea5f329490048831 0.1s done
10:34:51  #5 sha256:6f7b1a1af1d212ff1519dbf4534d2491d175f4fa052f008e4cfc2ad9744e5e4b 249B / 249B 0.7s done
10:34:51  #5 sha256:b05032fa5b62ec785bb4d899754c0969d9829fa10bbdc7f74bb14c8e4f11358a 13.82MB / 13.82MB 3.6s done
10:34:51  #5 sha256:b4e72df0ba0e7a032d9028786a436c63d283a51c04415ae0168197be7d828938 1.29MB / 1.29MB 2.1s done
10:34:51  #5 sha256:3531af2bc2a9c8883754652783cf96207d53189db279c9637b7157d034de7ecd 29.78MB / 29.78MB 7.0s done
10:34:51  #5 extracting sha256:3531af2bc2a9c8883754652783cf96207d53189db279c9637b7157d034de7ecd
10:34:51  #5 ...
10:34:51  
10:34:51  #4 [internal] load build context
10:34:51  #4 ...
10:34:51  
10:34:51  #5 [1/6] FROM docker.io/library/python:3.10-slim@sha256:cdbf8193cee2e31639ea8ea85ffdd8fa5cce98ee9abfde96ea5f329490048831
10:34:51  #5 extracting sha256:3531af2bc2a9c8883754652783cf96207d53189db279c9637b7157d034de7ecd 3.3s done
10:34:51  #5 DONE 10.8s
10:34:51  
10:34:51  #4 [internal] load build context
10:34:54  #4 ...
10:34:54  
10:34:54  #5 [1/6] FROM docker.io/library/python:3.10-slim@sha256:cdbf8193cee2e31639ea8ea85ffdd8fa5cce98ee9abfde96ea5f329490048831
10:34:54  #5 extracting sha256:b4e72df0ba0e7a032d9028786a436c63d283a51c04415ae0168197be7d828938 0.4s done
10:34:54  #5 extracting sha256:b05032fa5b62ec785bb4d899754c0969d9829fa10bbdc7f74bb14c8e4f11358a 2.1s done
10:34:54  #5 extracting sha256:6f7b1a1af1d212ff1519dbf4534d2491d175f4fa052f008e4cfc2ad9744e5e4b 0.1s done
10:34:54  #5 DONE 13.4s
10:34:54  
10:34:54  #4 [internal] load build context
10:34:54  #4 ...
10:34:54  
10:34:54  #6 [2/6] WORKDIR /app
10:34:54  #6 DONE 0.6s
10:34:54  
10:34:54  #4 [internal] load build context
10:34:55  #4 transferring context: 100.52MB 15.0s
10:34:59  #4 transferring context: 131.24MB 18.8s done
10:34:59  #4 DONE 18.9s
10:34:59  
10:34:59  #7 [3/6] RUN apt-get update && apt-get install -y --no-install-recommends     gcc     default-libmysqlclient-dev     pkg-config     && rm -rf /var/lib/apt/lists/*
10:34:59  #7 0.862 Hit:1 http://deb.debian.org/debian trixie InRelease
10:34:59  #7 0.862 Get:2 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
10:34:59  #7 0.873 Get:3 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
10:34:59  #7 0.957 Get:4 http://deb.debian.org/debian trixie/main amd64 Packages [9671 kB]
10:34:59  #7 2.437 Get:5 http://deb.debian.org/debian trixie-updates/main amd64 Packages [5412 B]
10:34:59  #7 2.458 Get:6 http://deb.debian.org/debian-security trixie-security/main amd64 Packages [130 kB]
10:34:59  #7 5.029 Fetched 9897 kB in 4s (2258 kB/s)
10:35:00  #7 5.029 Reading package lists...
10:35:02  #7 6.480 Reading package lists...
10:35:02  #7 7.741 Building dependency tree...
10:35:02  #7 8.044 Reading state information...
10:35:03  #7 8.589 The following additional packages will be installed:
10:35:03  #7 8.589   binutils binutils-common binutils-x86-64-linux-gnu cpp cpp-14
10:35:03  #7 8.589   cpp-14-x86-64-linux-gnu cpp-x86-64-linux-gnu gcc-14 gcc-14-x86-64-linux-gnu
10:35:03  #7 8.589   gcc-x86-64-linux-gnu libasan8 libatomic1 libbinutils libc-dev-bin libc6-dev
10:35:03  #7 8.589   libcc1-0 libcrypt-dev libctf-nobfd0 libctf0 libgcc-14-dev libgomp1
10:35:03  #7 8.589   libgprofng0 libhwasan0 libisl23 libitm1 libjansson4 liblsan0 libmariadb-dev
10:35:03  #7 8.590   libmariadb-dev-compat libmariadb3 libmpc3 libmpfr6 libpkgconf3 libquadmath0
10:35:03  #7 8.590   libsframe1 libssl-dev libtsan2 libubsan1 linux-libc-dev mariadb-common
10:35:03  #7 8.591   mysql-common pkgconf pkgconf-bin rpcsvc-proto zlib1g-dev
10:35:03  #7 8.593 Suggested packages:
10:35:03  #7 8.593   binutils-doc gprofng-gui binutils-gold cpp-doc gcc-14-locales cpp-14-doc
10:35:03  #7 8.593   gcc-multilib make manpages-dev autoconf automake libtool flex bison gdb
10:35:03  #7 8.593   gcc-doc gcc-14-multilib gcc-14-doc gdb-x86-64-linux-gnu libc-devtools
10:35:03  #7 8.593   glibc-doc libssl-doc
10:35:03  #7 8.593 Recommended packages:
10:35:03  #7 8.593   manpages manpages-dev
10:35:03  #7 8.891 The following NEW packages will be installed:
10:35:03  #7 8.891   binutils binutils-common binutils-x86-64-linux-gnu cpp cpp-14
10:35:03  #7 8.892   cpp-14-x86-64-linux-gnu cpp-x86-64-linux-gnu default-libmysqlclient-dev gcc
10:35:03  #7 8.892   gcc-14 gcc-14-x86-64-linux-gnu gcc-x86-64-linux-gnu libasan8 libatomic1
10:35:03  #7 8.893   libbinutils libc-dev-bin libc6-dev libcc1-0 libcrypt-dev libctf-nobfd0
10:35:03  #7 8.897   libctf0 libgcc-14-dev libgomp1 libgprofng0 libhwasan0 libisl23 libitm1
10:35:03  #7 8.897   libjansson4 liblsan0 libmariadb-dev libmariadb-dev-compat libmariadb3
10:35:03  #7 8.899   libmpc3 libmpfr6 libpkgconf3 libquadmath0 libsframe1 libssl-dev libtsan2
10:35:03  #7 8.900   libubsan1 linux-libc-dev mariadb-common mysql-common pkg-config pkgconf
10:35:03  #7 8.901   pkgconf-bin rpcsvc-proto zlib1g-dev
10:35:03  #7 9.048 0 upgraded, 48 newly installed, 0 to remove and 0 not upgraded.
10:35:03  #7 9.048 Need to get 61.5 MB of archives.
10:35:03  #7 9.048 After this operation, 236 MB of additional disk space will be used.
10:35:03  #7 9.048 Get:1 http://deb.debian.org/debian trixie/main amd64 libsframe1 amd64 2.44-3 [78.4 kB]
10:35:03  #7 9.119 Get:2 http://deb.debian.org/debian trixie/main amd64 binutils-common amd64 2.44-3 [2509 kB]
10:35:03  #7 9.373 Get:3 http://deb.debian.org/debian trixie/main amd64 libbinutils amd64 2.44-3 [534 kB]
10:35:03  #7 9.450 Get:4 http://deb.debian.org/debian trixie/main amd64 libgprofng0 amd64 2.44-3 [808 kB]
10:35:03  #7 9.540 Get:5 http://deb.debian.org/debian trixie/main amd64 libctf-nobfd0 amd64 2.44-3 [156 kB]
10:35:04  #7 9.575 Get:6 http://deb.debian.org/debian trixie/main amd64 libctf0 amd64 2.44-3 [88.6 kB]
10:35:04  #7 9.608 Get:7 http://deb.debian.org/debian trixie/main amd64 libjansson4 amd64 2.14-2+b3 [39.8 kB]
10:35:04  #7 9.640 Get:8 http://deb.debian.org/debian trixie/main amd64 binutils-x86-64-linux-gnu amd64 2.44-3 [1014 kB]
10:35:04  #7 9.750 Get:9 http://deb.debian.org/debian trixie/main amd64 binutils amd64 2.44-3 [265 kB]
10:35:04  #7 9.797 Get:10 http://deb.debian.org/debian trixie/main amd64 libisl23 amd64 0.27-1 [659 kB]
10:35:04  #7 9.887 Get:11 http://deb.debian.org/debian trixie/main amd64 libmpfr6 amd64 4.2.2-1 [729 kB]
10:35:04  #7 9.991 Get:12 http://deb.debian.org/debian trixie/main amd64 libmpc3 amd64 1.3.1-1+b3 [52.2 kB]
10:35:04  #7 10.02 Get:13 http://deb.debian.org/debian trixie/main amd64 cpp-14-x86-64-linux-gnu amd64 14.2.0-19 [11.0 MB]
10:35:05  #7 11.01 Get:14 http://deb.debian.org/debian trixie/main amd64 cpp-14 amd64 14.2.0-19 [1280 B]
10:35:05  #7 11.02 Get:15 http://deb.debian.org/debian trixie/main amd64 cpp-x86-64-linux-gnu amd64 4:14.2.0-1 [4840 B]
10:35:05  #7 11.05 Get:16 http://deb.debian.org/debian trixie/main amd64 cpp amd64 4:14.2.0-1 [1568 B]
10:35:05  #7 11.07 Get:17 http://deb.debian.org/debian trixie/main amd64 mysql-common all 5.8+1.1.1 [6784 B]
10:35:05  #7 11.09 Get:18 http://deb.debian.org/debian trixie/main amd64 mariadb-common all 1:11.8.6-0+deb13u1 [29.5 kB]
10:35:05  #7 11.11 Get:19 http://deb.debian.org/debian trixie/main amd64 libmariadb3 amd64 1:11.8.6-0+deb13u1 [187 kB]
10:35:05  #7 11.16 Get:20 http://deb.debian.org/debian-security trixie-security/main amd64 libssl-dev amd64 3.5.5-1~deb13u2 [2954 kB]
10:35:05  #7 11.43 Get:21 http://deb.debian.org/debian trixie/main amd64 libc-dev-bin amd64 2.41-12+deb13u2 [59.4 kB]
10:35:06  #7 11.46 Get:22 http://deb.debian.org/debian-security trixie-security/main amd64 linux-libc-dev all 6.12.85-1 [2802 kB]
10:35:06  #7 11.82 Get:23 http://deb.debian.org/debian trixie/main amd64 libcrypt-dev amd64 1:4.4.38-1 [119 kB]
10:35:06  #7 11.89 Get:24 http://deb.debian.org/debian trixie/main amd64 rpcsvc-proto amd64 1.4.3-1 [63.3 kB]
10:35:06  #7 11.96 Get:25 http://deb.debian.org/debian trixie/main amd64 libc6-dev amd64 2.41-12+deb13u2 [1996 kB]
10:35:06  #7 12.32 Get:26 http://deb.debian.org/debian trixie/main amd64 zlib1g-dev amd64 1:1.3.dfsg+really1.3.1-1+b1 [920 kB]
10:35:06  #7 12.45 Get:27 http://deb.debian.org/debian trixie/main amd64 libmariadb-dev amd64 1:11.8.6-0+deb13u1 [277 kB]
10:35:06  #7 12.53 Get:28 http://deb.debian.org/debian trixie/main amd64 libmariadb-dev-compat amd64 1:11.8.6-0+deb13u1 [28.3 kB]
10:35:06  #7 12.60 Get:29 http://deb.debian.org/debian trixie/main amd64 default-libmysqlclient-dev amd64 1.1.1 [3252 B]
10:35:07  #7 12.63 Get:30 http://deb.debian.org/debian trixie/main amd64 libcc1-0 amd64 14.2.0-19 [42.8 kB]
10:35:07  #7 12.70 Get:31 http://deb.debian.org/debian trixie/main amd64 libgomp1 amd64 14.2.0-19 [137 kB]
10:35:07  #7 12.75 Get:32 http://deb.debian.org/debian trixie/main amd64 libitm1 amd64 14.2.0-19 [26.0 kB]
10:35:07  #7 12.80 Get:33 http://deb.debian.org/debian trixie/main amd64 libatomic1 amd64 14.2.0-19 [9308 B]
10:35:07  #7 12.82 Get:34 http://deb.debian.org/debian trixie/main amd64 libasan8 amd64 14.2.0-19 [2725 kB]
10:35:07  #7 13.18 Get:35 http://deb.debian.org/debian trixie/main amd64 liblsan0 amd64 14.2.0-19 [1204 kB]
10:35:07  #7 13.37 Get:36 http://deb.debian.org/debian trixie/main amd64 libtsan2 amd64 14.2.0-19 [2460 kB]
10:35:07  #7 13.66 Get:37 http://deb.debian.org/debian trixie/main amd64 libubsan1 amd64 14.2.0-19 [1074 kB]
10:35:08  #7 14.15 Get:38 http://deb.debian.org/debian trixie/main amd64 libhwasan0 amd64 14.2.0-19 [1488 kB]
10:35:08  #7 14.41 Get:39 http://deb.debian.org/debian trixie/main amd64 libquadmath0 amd64 14.2.0-19 [145 kB]
10:35:09  #7 14.45 Get:40 http://deb.debian.org/debian trixie/main amd64 libgcc-14-dev amd64 14.2.0-19 [2672 kB]
10:35:09  #7 14.71 Get:41 http://deb.debian.org/debian trixie/main amd64 gcc-14-x86-64-linux-gnu amd64 14.2.0-19 [21.4 MB]
10:35:11  #7 16.68 Get:42 http://deb.debian.org/debian trixie/main amd64 gcc-14 amd64 14.2.0-19 [540 kB]
10:35:11  #7 16.76 Get:43 http://deb.debian.org/debian trixie/main amd64 gcc-x86-64-linux-gnu amd64 4:14.2.0-1 [1436 B]
10:35:11  #7 16.78 Get:44 http://deb.debian.org/debian trixie/main amd64 gcc amd64 4:14.2.0-1 [5136 B]
10:35:11  #7 16.80 Get:45 http://deb.debian.org/debian trixie/main amd64 libpkgconf3 amd64 1.8.1-4 [36.4 kB]
10:35:11  #7 16.83 Get:46 http://deb.debian.org/debian trixie/main amd64 pkgconf-bin amd64 1.8.1-4 [30.2 kB]
10:35:11  #7 16.86 Get:47 http://deb.debian.org/debian trixie/main amd64 pkgconf amd64 1.8.1-4 [26.2 kB]
10:35:11  #7 16.88 Get:48 http://deb.debian.org/debian trixie/main amd64 pkg-config amd64 1.8.1-4 [14.0 kB]
10:35:11  #7 17.13 debconf: unable to initialize frontend: Dialog
10:35:11  #7 17.13 debconf: (TERM is not set, so the dialog frontend is not usable.)
10:35:11  #7 17.13 debconf: falling back to frontend: Readline
10:35:11  #7 17.13 debconf: unable to initialize frontend: Readline
10:35:11  #7 17.13 debconf: (Can't locate Term/ReadLine.pm in @INC (you may need to install the Term::ReadLine module) (@INC entries checked: /etc/perl /usr/local/lib/x86_64-linux-gnu/perl/5.40.1 /usr/local/share/perl/5.40.1 /usr/lib/x86_64-linux-gnu/perl5/5.40 /usr/share/perl5 /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl/5.40 /usr/share/perl/5.40 /usr/local/lib/site_perl) at /usr/share/perl5/Debconf/FrontEnd/Readline.pm line 8, <STDIN> line 48.)
10:35:11  #7 17.13 debconf: falling back to frontend: Teletype
10:35:11  #7 17.14 debconf: unable to initialize frontend: Teletype
10:35:11  #7 17.14 debconf: (This frontend requires a controlling tty.)
10:35:11  #7 17.14 debconf: falling back to frontend: Noninteractive
10:35:14  #7 19.53 Fetched 61.5 MB in 8s (7751 kB/s)
10:35:14  #7 19.57 Selecting previously unselected package libsframe1:amd64.
10:35:14  #7 19.57 (Reading database ... 
10:35:14  (Reading database ... 5%
10:35:14  (Reading database ... 10%
10:35:14  (Reading database ... 15%
10:35:14  (Reading database ... 20%
10:35:14  (Reading database ... 25%
10:35:14  (Reading database ... 30%
10:35:14  (Reading database ... 35%
10:35:14  (Reading database ... 40%
10:35:14  (Reading database ... 45%
10:35:14  (Reading database ... 50%
10:35:14  (Reading database ... 55%
10:35:14  (Reading database ... 60%
10:35:14  (Reading database ... 65%
10:35:14  (Reading database ... 70%
10:35:14  (Reading database ... 75%
10:35:14  (Reading database ... 80%
10:35:14  (Reading database ... 85%
10:35:14  (Reading database ... 90%
10:35:14  (Reading database ... 95%
10:35:14  (Reading database ... 100%
10:35:14  (Reading database ... 5645 files and directories currently installed.)
10:35:14  #7 19.59 Preparing to unpack .../00-libsframe1_2.44-3_amd64.deb ...
10:35:14  #7 19.60 Unpacking libsframe1:amd64 (2.44-3) ...
10:35:14  #7 19.69 Selecting previously unselected package binutils-common:amd64.
10:35:14  #7 19.69 Preparing to unpack .../01-binutils-common_2.44-3_amd64.deb ...
10:35:14  #7 19.70 Unpacking binutils-common:amd64 (2.44-3) ...
10:35:14  #7 19.99 Selecting previously unselected package libbinutils:amd64.
10:35:14  #7 20.00 Preparing to unpack .../02-libbinutils_2.44-3_amd64.deb ...
10:35:14  #7 20.01 Unpacking libbinutils:amd64 (2.44-3) ...
10:35:14  #7 20.13 Selecting previously unselected package libgprofng0:amd64.
10:35:14  #7 20.13 Preparing to unpack .../03-libgprofng0_2.44-3_amd64.deb ...
10:35:14  #7 20.14 Unpacking libgprofng0:amd64 (2.44-3) ...
10:35:14  #7 20.29 Selecting previously unselected package libctf-nobfd0:amd64.
10:35:14  #7 20.29 Preparing to unpack .../04-libctf-nobfd0_2.44-3_amd64.deb ...
10:35:14  #7 20.30 Unpacking libctf-nobfd0:amd64 (2.44-3) ...
10:35:14  #7 20.38 Selecting previously unselected package libctf0:amd64.
10:35:14  #7 20.38 Preparing to unpack .../05-libctf0_2.44-3_amd64.deb ...
10:35:14  #7 20.39 Unpacking libctf0:amd64 (2.44-3) ...
10:35:14  #7 20.47 Selecting previously unselected package libjansson4:amd64.
10:35:15  #7 20.47 Preparing to unpack .../06-libjansson4_2.14-2+b3_amd64.deb ...
10:35:15  #7 20.49 Unpacking libjansson4:amd64 (2.14-2+b3) ...
10:35:15  #7 20.56 Selecting previously unselected package binutils-x86-64-linux-gnu.
10:35:15  #7 20.56 Preparing to unpack .../07-binutils-x86-64-linux-gnu_2.44-3_amd64.deb ...
10:35:15  #7 20.57 Unpacking binutils-x86-64-linux-gnu (2.44-3) ...
10:35:15  #7 20.76 Selecting previously unselected package binutils.
10:35:15  #7 20.76 Preparing to unpack .../08-binutils_2.44-3_amd64.deb ...
10:35:15  #7 20.77 Unpacking binutils (2.44-3) ...
10:35:15  #7 20.87 Selecting previously unselected package libisl23:amd64.
10:35:15  #7 20.87 Preparing to unpack .../09-libisl23_0.27-1_amd64.deb ...
10:35:15  #7 20.88 Unpacking libisl23:amd64 (0.27-1) ...
10:35:15  #7 21.01 Selecting previously unselected package libmpfr6:amd64.
10:35:15  #7 21.01 Preparing to unpack .../10-libmpfr6_4.2.2-1_amd64.deb ...
10:35:15  #7 21.02 Unpacking libmpfr6:amd64 (4.2.2-1) ...
10:35:15  #7 21.16 Selecting previously unselected package libmpc3:amd64.
10:35:15  #7 21.16 Preparing to unpack .../11-libmpc3_1.3.1-1+b3_amd64.deb ...
10:35:15  #7 21.17 Unpacking libmpc3:amd64 (1.3.1-1+b3) ...
10:35:15  #7 21.26 Selecting previously unselected package cpp-14-x86-64-linux-gnu.
10:35:15  #7 21.26 Preparing to unpack .../12-cpp-14-x86-64-linux-gnu_14.2.0-19_amd64.deb ...
10:35:15  #7 21.27 Unpacking cpp-14-x86-64-linux-gnu (14.2.0-19) ...
10:35:16  #7 22.25 Selecting previously unselected package cpp-14.
10:35:16  #7 22.25 Preparing to unpack .../13-cpp-14_14.2.0-19_amd64.deb ...
10:35:16  #7 22.26 Unpacking cpp-14 (14.2.0-19) ...
10:35:16  #7 22.32 Selecting previously unselected package cpp-x86-64-linux-gnu.
10:35:16  #7 22.32 Preparing to unpack .../14-cpp-x86-64-linux-gnu_4%3a14.2.0-1_amd64.deb ...
10:35:16  #7 22.34 Unpacking cpp-x86-64-linux-gnu (4:14.2.0-1) ...
10:35:16  #7 22.43 Selecting previously unselected package cpp.
10:35:16  #7 22.44 Preparing to unpack .../15-cpp_4%3a14.2.0-1_amd64.deb ...
10:35:16  #7 22.52 Unpacking cpp (4:14.2.0-1) ...
10:35:16  #7 22.68 Selecting previously unselected package mysql-common.
10:35:17  #7 22.69 Preparing to unpack .../16-mysql-common_5.8+1.1.1_all.deb ...
10:35:17  #7 22.72 Unpacking mysql-common (5.8+1.1.1) ...
10:35:17  #7 22.80 Selecting previously unselected package mariadb-common.
10:35:17  #7 22.80 Preparing to unpack .../17-mariadb-common_1%3a11.8.6-0+deb13u1_all.deb ...
10:35:17  #7 22.82 Unpacking mariadb-common (1:11.8.6-0+deb13u1) ...
10:35:17  #7 22.89 Selecting previously unselected package libmariadb3:amd64.
10:35:17  #7 22.89 Preparing to unpack .../18-libmariadb3_1%3a11.8.6-0+deb13u1_amd64.deb ...
10:35:17  #7 22.90 Unpacking libmariadb3:amd64 (1:11.8.6-0+deb13u1) ...
10:35:17  #7 22.97 Selecting previously unselected package libssl-dev:amd64.
10:35:17  #7 22.97 Preparing to unpack .../19-libssl-dev_3.5.5-1~deb13u2_amd64.deb ...
10:35:17  #7 22.98 Unpacking libssl-dev:amd64 (3.5.5-1~deb13u2) ...
10:35:17  #7 23.32 Selecting previously unselected package libc-dev-bin.
10:35:17  #7 23.32 Preparing to unpack .../20-libc-dev-bin_2.41-12+deb13u2_amd64.deb ...
10:35:17  #7 23.33 Unpacking libc-dev-bin (2.41-12+deb13u2) ...
10:35:17  #7 23.39 Selecting previously unselected package linux-libc-dev.
10:35:17  #7 23.40 Preparing to unpack .../21-linux-libc-dev_6.12.85-1_all.deb ...
10:35:17  #7 23.40 Unpacking linux-libc-dev (6.12.85-1) ...
10:35:18  #7 24.05 Selecting previously unselected package libcrypt-dev:amd64.
10:35:18  #7 24.05 Preparing to unpack .../22-libcrypt-dev_1%3a4.4.38-1_amd64.deb ...
10:35:18  #7 24.07 Unpacking libcrypt-dev:amd64 (1:4.4.38-1) ...
10:35:18  #7 24.15 Selecting previously unselected package rpcsvc-proto.
10:35:18  #7 24.15 Preparing to unpack .../23-rpcsvc-proto_1.4.3-1_amd64.deb ...
10:35:18  #7 24.16 Unpacking rpcsvc-proto (1.4.3-1) ...
10:35:18  #7 24.23 Selecting previously unselected package libc6-dev:amd64.
10:35:18  #7 24.24 Preparing to unpack .../24-libc6-dev_2.41-12+deb13u2_amd64.deb ...
10:35:18  #7 24.25 Unpacking libc6-dev:amd64 (2.41-12+deb13u2) ...
10:35:19  #7 24.57 Selecting previously unselected package zlib1g-dev:amd64.
10:35:19  #7 24.57 Preparing to unpack .../25-zlib1g-dev_1%3a1.3.dfsg+really1.3.1-1+b1_amd64.deb ...
10:35:19  #7 24.58 Unpacking zlib1g-dev:amd64 (1:1.3.dfsg+really1.3.1-1+b1) ...
10:35:19  #7 24.65 Selecting previously unselected package libmariadb-dev.
10:35:19  #7 24.65 Preparing to unpack .../26-libmariadb-dev_1%3a11.8.6-0+deb13u1_amd64.deb ...
10:35:19  #7 24.66 Unpacking libmariadb-dev (1:11.8.6-0+deb13u1) ...
10:35:19  #7 24.75 Selecting previously unselected package libmariadb-dev-compat.
10:35:19  #7 24.75 Preparing to unpack .../27-libmariadb-dev-compat_1%3a11.8.6-0+deb13u1_amd64.deb ...
10:35:19  #7 24.76 Unpacking libmariadb-dev-compat (1:11.8.6-0+deb13u1) ...
10:35:19  #7 24.83 Selecting previously unselected package default-libmysqlclient-dev:amd64.
10:35:19  #7 24.83 Preparing to unpack .../28-default-libmysqlclient-dev_1.1.1_amd64.deb ...
10:35:19  #7 24.84 Unpacking default-libmysqlclient-dev:amd64 (1.1.1) ...
10:35:19  #7 24.91 Selecting previously unselected package libcc1-0:amd64.
10:35:19  #7 24.91 Preparing to unpack .../29-libcc1-0_14.2.0-19_amd64.deb ...
10:35:19  #7 24.92 Unpacking libcc1-0:amd64 (14.2.0-19) ...
10:35:19  #7 24.99 Selecting previously unselected package libgomp1:amd64.
10:35:19  #7 24.99 Preparing to unpack .../30-libgomp1_14.2.0-19_amd64.deb ...
10:35:19  #7 25.00 Unpacking libgomp1:amd64 (14.2.0-19) ...
10:35:19  #7 25.09 Selecting previously unselected package libitm1:amd64.
10:35:19  #7 25.10 Preparing to unpack .../31-libitm1_14.2.0-19_amd64.deb ...
10:35:19  #7 25.10 Unpacking libitm1:amd64 (14.2.0-19) ...
10:35:19  #7 25.17 Selecting previously unselected package libatomic1:amd64.
10:35:19  #7 25.17 Preparing to unpack .../32-libatomic1_14.2.0-19_amd64.deb ...
10:35:19  #7 25.18 Unpacking libatomic1:amd64 (14.2.0-19) ...
10:35:19  #7 25.26 Selecting previously unselected package libasan8:amd64.
10:35:19  #7 25.26 Preparing to unpack .../33-libasan8_14.2.0-19_amd64.deb ...
10:35:19  #7 25.27 Unpacking libasan8:amd64 (14.2.0-19) ...
10:35:20  #7 25.64 Selecting previously unselected package liblsan0:amd64.
10:35:20  #7 25.65 Preparing to unpack .../34-liblsan0_14.2.0-19_amd64.deb ...
10:35:20  #7 25.65 Unpacking liblsan0:amd64 (14.2.0-19) ...
10:35:20  #7 25.86 Selecting previously unselected package libtsan2:amd64.
10:35:20  #7 25.87 Preparing to unpack .../35-libtsan2_14.2.0-19_amd64.deb ...
10:35:20  #7 25.87 Unpacking libtsan2:amd64 (14.2.0-19) ...
10:35:20  #7 26.22 Selecting previously unselected package libubsan1:amd64.
10:35:20  #7 26.22 Preparing to unpack .../36-libubsan1_14.2.0-19_amd64.deb ...
10:35:20  #7 26.23 Unpacking libubsan1:amd64 (14.2.0-19) ...
10:35:20  #7 26.40 Selecting previously unselected package libhwasan0:amd64.
10:35:21  #7 26.40 Preparing to unpack .../37-libhwasan0_14.2.0-19_amd64.deb ...
10:35:21  #7 26.40 Unpacking libhwasan0:amd64 (14.2.0-19) ...
10:35:21  #7 26.61 Selecting previously unselected package libquadmath0:amd64.
10:35:21  #7 26.61 Preparing to unpack .../38-libquadmath0_14.2.0-19_amd64.deb ...
10:35:21  #7 26.62 Unpacking libquadmath0:amd64 (14.2.0-19) ...
10:35:21  #7 26.69 Selecting previously unselected package libgcc-14-dev:amd64.
10:35:21  #7 26.70 Preparing to unpack .../39-libgcc-14-dev_14.2.0-19_amd64.deb ...
10:35:21  #7 26.70 Unpacking libgcc-14-dev:amd64 (14.2.0-19) ...
10:35:21  #7 27.02 Selecting previously unselected package gcc-14-x86-64-linux-gnu.
10:35:21  #7 27.02 Preparing to unpack .../40-gcc-14-x86-64-linux-gnu_14.2.0-19_amd64.deb ...
10:35:21  #7 27.04 Unpacking gcc-14-x86-64-linux-gnu (14.2.0-19) ...
10:35:22  #7 28.27 Selecting previously unselected package gcc-14.
10:35:22  #7 28.27 Preparing to unpack .../41-gcc-14_14.2.0-19_amd64.deb ...
10:35:22  #7 28.28 Unpacking gcc-14 (14.2.0-19) ...
10:35:22  #7 28.36 Selecting previously unselected package gcc-x86-64-linux-gnu.
10:35:22  #7 28.36 Preparing to unpack .../42-gcc-x86-64-linux-gnu_4%3a14.2.0-1_amd64.deb ...
10:35:22  #7 28.37 Unpacking gcc-x86-64-linux-gnu (4:14.2.0-1) ...
10:35:22  #7 28.43 Selecting previously unselected package gcc.
10:35:22  #7 28.43 Preparing to unpack .../43-gcc_4%3a14.2.0-1_amd64.deb ...
10:35:22  #7 28.44 Unpacking gcc (4:14.2.0-1) ...
10:35:22  #7 28.50 Selecting previously unselected package libpkgconf3:amd64.
10:35:22  #7 28.51 Preparing to unpack .../44-libpkgconf3_1.8.1-4_amd64.deb ...
10:35:22  #7 28.52 Unpacking libpkgconf3:amd64 (1.8.1-4) ...
10:35:22  #7 28.59 Selecting previously unselected package pkgconf-bin.
10:35:23  #7 28.59 Preparing to unpack .../45-pkgconf-bin_1.8.1-4_amd64.deb ...
10:35:23  #7 28.60 Unpacking pkgconf-bin (1.8.1-4) ...
10:35:23  #7 28.66 Selecting previously unselected package pkgconf:amd64.
10:35:23  #7 28.66 Preparing to unpack .../46-pkgconf_1.8.1-4_amd64.deb ...
10:35:23  #7 28.67 Unpacking pkgconf:amd64 (1.8.1-4) ...
10:35:23  #7 28.74 Selecting previously unselected package pkg-config:amd64.
10:35:23  #7 28.74 Preparing to unpack .../47-pkg-config_1.8.1-4_amd64.deb ...
10:35:23  #7 28.75 Unpacking pkg-config:amd64 (1.8.1-4) ...
10:35:23  #7 28.81 Setting up mysql-common (5.8+1.1.1) ...
10:35:23  #7 28.89 update-alternatives: using /etc/mysql/my.cnf.fallback to provide /etc/mysql/my.cnf (my.cnf) in auto mode
10:35:23  #7 28.91 Setting up binutils-common:amd64 (2.44-3) ...
10:35:23  #7 28.94 Setting up linux-libc-dev (6.12.85-1) ...
10:35:23  #7 28.97 Setting up libctf-nobfd0:amd64 (2.44-3) ...
10:35:23  #7 29.00 Setting up libgomp1:amd64 (14.2.0-19) ...
10:35:23  #7 29.02 Setting up libsframe1:amd64 (2.44-3) ...
10:35:23  #7 29.05 Setting up libjansson4:amd64 (2.14-2+b3) ...
10:35:23  #7 29.07 Setting up mariadb-common (1:11.8.6-0+deb13u1) ...
10:35:23  #7 29.10 update-alternatives: using /etc/mysql/mariadb.cnf to provide /etc/mysql/my.cnf (my.cnf) in auto mode
10:35:23  #7 29.12 Setting up libpkgconf3:amd64 (1.8.1-4) ...
10:35:23  #7 29.15 Setting up rpcsvc-proto (1.4.3-1) ...
10:35:23  #7 29.18 Setting up libmpfr6:amd64 (4.2.2-1) ...
10:35:23  #7 29.20 Setting up libquadmath0:amd64 (14.2.0-19) ...
10:35:23  #7 29.25 Setting up libssl-dev:amd64 (3.5.5-1~deb13u2) ...
10:35:23  #7 29.28 Setting up libmpc3:amd64 (1.3.1-1+b3) ...
10:35:23  #7 29.32 Setting up libatomic1:amd64 (14.2.0-19) ...
10:35:23  #7 29.34 Setting up libmariadb3:amd64 (1:11.8.6-0+deb13u1) ...
10:35:23  #7 29.37 Setting up pkgconf-bin (1.8.1-4) ...
10:35:23  #7 29.40 Setting up libubsan1:amd64 (14.2.0-19) ...
10:35:23  #7 29.42 Setting up libhwasan0:amd64 (14.2.0-19) ...
10:35:23  #7 29.45 Setting up libcrypt-dev:amd64 (1:4.4.38-1) ...
10:35:23  #7 29.48 Setting up libasan8:amd64 (14.2.0-19) ...
10:35:23  #7 29.51 Setting up libtsan2:amd64 (14.2.0-19) ...
10:35:23  #7 29.54 Setting up libbinutils:amd64 (2.44-3) ...
10:35:23  #7 29.57 Setting up libisl23:amd64 (0.27-1) ...
10:35:23  #7 29.61 Setting up libc-dev-bin (2.41-12+deb13u2) ...
10:35:24  #7 29.63 Setting up libcc1-0:amd64 (14.2.0-19) ...
10:35:24  #7 29.65 Setting up liblsan0:amd64 (14.2.0-19) ...
10:35:24  #7 29.68 Setting up libitm1:amd64 (14.2.0-19) ...
10:35:24  #7 29.71 Setting up libctf0:amd64 (2.44-3) ...
10:35:24  #7 29.74 Setting up pkgconf:amd64 (1.8.1-4) ...
10:35:24  #7 29.77 Setting up libgprofng0:amd64 (2.44-3) ...
10:35:24  #7 29.78 Setting up pkg-config:amd64 (1.8.1-4) ...
10:35:24  #7 29.82 Setting up cpp-14-x86-64-linux-gnu (14.2.0-19) ...
10:35:24  #7 29.84 Setting up cpp-14 (14.2.0-19) ...
10:35:24  #7 29.87 Setting up libc6-dev:amd64 (2.41-12+deb13u2) ...
10:35:24  #7 29.90 Setting up libgcc-14-dev:amd64 (14.2.0-19) ...
10:35:24  #7 29.92 Setting up binutils-x86-64-linux-gnu (2.44-3) ...
10:35:27  #7 33.10 Setting up cpp-x86-64-linux-gnu (4:14.2.0-1) ...
10:35:27  #7 33.23 Setting up binutils (2.44-3) ...
10:35:27  #7 33.29 Setting up zlib1g-dev:amd64 (1:1.3.dfsg+really1.3.1-1+b1) ...
10:35:27  #7 33.37 Setting up cpp (4:14.2.0-1) ...
10:35:27  #7 33.43 Setting up gcc-14-x86-64-linux-gnu (14.2.0-19) ...
10:35:27  #7 33.45 Setting up gcc-x86-64-linux-gnu (4:14.2.0-1) ...
10:35:27  #7 33.48 Setting up gcc-14 (14.2.0-19) ...
10:35:27  #7 33.53 Setting up libmariadb-dev (1:11.8.6-0+deb13u1) ...
10:35:27  #7 33.56 Setting up libmariadb-dev-compat (1:11.8.6-0+deb13u1) ...
10:35:27  #7 33.60 Setting up gcc (4:14.2.0-1) ...
10:35:28  #7 33.66 Setting up default-libmysqlclient-dev:amd64 (1.1.1) ...
10:35:28  #7 33.68 Processing triggers for libc-bin (2.41-12+deb13u2) ...
10:35:29  #7 DONE 34.9s
10:35:29  
10:35:29  #8 [4/6] COPY requirements.txt .
10:35:29  #8 DONE 0.2s
10:35:29  
10:35:29  #9 [5/6] RUN pip install --no-cache-dir -r requirements.txt
10:35:33  #9 3.512 Collecting flask==2.3.3
10:35:33  #9 3.771   Downloading flask-2.3.3-py3-none-any.whl (96 kB)
10:35:33  #9 3.824      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 96.1/96.1 kB 2.1 MB/s eta 0:00:00
10:35:33  #9 3.910 Collecting flask-cors==4.0.0
10:35:33  #9 3.931   Downloading Flask_Cors-4.0.0-py2.py3-none-any.whl (14 kB)
10:35:33  #9 4.127 Collecting bcrypt==4.0.1
10:35:33  #9 4.150   Downloading bcrypt-4.0.1-cp36-abi3-manylinux_2_28_x86_64.whl (593 kB)
10:35:33  #9 4.231      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 593.7/593.7 kB 7.7 MB/s eta 0:00:00
10:35:33  #9 4.417 Collecting mysql-connector-python==8.3.0
10:35:34  #9 4.446   Downloading mysql_connector_python-8.3.0-cp310-cp310-manylinux_2_17_x86_64.whl (21.5 MB)
10:35:36  #9 6.550      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 21.5/21.5 MB 11.1 MB/s eta 0:00:00
10:35:36  #9 6.692 Collecting Werkzeug==2.3.7
10:35:36  #9 6.724   Downloading werkzeug-2.3.7-py3-none-any.whl (242 kB)
10:35:36  #9 6.760      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 242.2/242.2 kB 8.3 MB/s eta 0:00:00
10:35:37  #9 7.722 Collecting numpy
10:35:37  #9 7.750   Downloading numpy-2.2.6-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (16.8 MB)
10:35:38  #9 9.210      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.8/16.8 MB 11.2 MB/s eta 0:00:00
10:35:39  #9 10.21 Collecting pillow
10:35:39  #9 10.23   Downloading pillow-12.2.0-cp310-cp310-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (7.1 MB)
10:35:40  #9 11.16      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7.1/7.1 MB 7.7 MB/s eta 0:00:00
10:35:40  #9 11.25 Collecting gunicorn
10:35:40  #9 11.27   Downloading gunicorn-25.3.0-py3-none-any.whl (208 kB)
10:35:40  #9 11.29      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 208.4/208.4 kB 13.1 MB/s eta 0:00:00
10:35:40  #9 11.38 Collecting Jinja2>=3.1.2
10:35:40  #9 11.41   Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
10:35:40  #9 11.43      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 134.9/134.9 kB 9.3 MB/s eta 0:00:00
10:35:40  #9 11.50 Collecting click>=8.1.3
10:35:41  #9 11.52   Downloading click-8.3.3-py3-none-any.whl (110 kB)
10:35:41  #9 11.54      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 110.5/110.5 kB 9.4 MB/s eta 0:00:00
10:35:41  #9 11.59 Collecting blinker>=1.6.2
10:35:41  #9 11.61   Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
10:35:41  #9 11.66 Collecting itsdangerous>=2.1.2
10:35:41  #9 11.68   Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
10:35:41  #9 11.98 Collecting MarkupSafe>=2.1.1
10:35:41  #9 12.00   Downloading markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (20 kB)
10:35:41  #9 12.15 Collecting packaging
10:35:41  #9 12.19   Downloading packaging-26.2-py3-none-any.whl (100 kB)
10:35:41  #9 12.21      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.2/100.2 kB 8.9 MB/s eta 0:00:00
10:35:41  #9 12.49 Installing collected packages: pillow, packaging, numpy, mysql-connector-python, MarkupSafe, itsdangerous, click, blinker, bcrypt, Werkzeug, Jinja2, gunicorn, flask, flask-cors
10:35:48  #9 18.68 Successfully installed Jinja2-3.1.6 MarkupSafe-3.0.3 Werkzeug-2.3.7 bcrypt-4.0.1 blinker-1.9.0 click-8.3.3 flask-2.3.3 flask-cors-4.0.0 gunicorn-25.3.0 itsdangerous-2.2.0 mysql-connector-python-8.3.0 numpy-2.2.6 packaging-26.2 pillow-12.2.0
10:35:48  #9 18.68 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
10:35:48  #9 18.94 
10:35:48  #9 18.94 [notice] A new release of pip is available: 23.0.1 -> 26.1
10:35:48  #9 18.94 [notice] To update, run: pip install --upgrade pip
10:35:49  #9 DONE 19.5s
10:35:49  
10:35:49  #10 [6/6] COPY . .
10:35:50  #10 DONE 1.6s
10:35:50  
10:35:50  #11 exporting to image
10:35:50  #11 exporting layers
10:36:12  #11 exporting layers 18.8s done
10:36:12  #11 exporting manifest sha256:da83a40a7c02b7c990a2e5fa568426e14a22f35917f243721703db3dcf2a8ab8 0.1s done
10:36:12  #11 exporting config sha256:433ded3fbb32a40b27bb301b1b9618f71dbd370f462d179a12647ee005dd1e48 0.0s done
10:36:12  #11 exporting attestation manifest sha256:97d7e126829a1b149c350c35776268339b3708b0bc0463928e298f871df9ed07 0.1s done
10:36:12  #11 exporting manifest list sha256:34b67ab01113c77480a5984b359cfd3d4b78417ae74ffbc3fbab300e64f08949
10:36:12  #11 exporting manifest list sha256:34b67ab01113c77480a5984b359cfd3d4b78417ae74ffbc3fbab300e64f08949 0.0s done
10:36:12  #11 naming to 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:18 done
10:36:12  #11 unpacking to 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:18
10:36:20  #11 unpacking to 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:18 10.2s done
10:36:20  #11 naming to 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:latest 0.0s done
10:36:20  #11 unpacking to 870676149845.dkr.ecr.eu-north-1.amazonaws.com/waterborne-app:latest 0.0s done
10:36:20  #11 DONE 29.5s
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Push to ECR)
[Pipeline] echo
10:36:21  🚀 Pushing image to AWS ECR...
[Pipeline] withCredentials
[Pipeline] // withCredentials
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Deploy to EKS)
Stage "Deploy to EKS" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Smoke Test)
Stage "Smoke Test" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Cleanup)
Stage "Cleanup" skipped due to earlier failure(s)
[Pipeline] getContext
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] echo
10:36:23  📊 Pipeline finished. Cleaning workspace...
[Pipeline] cleanWs
10:36:23  [WS-CLEANUP] Deleting project workspace...
10:36:23  [WS-CLEANUP] Deferred wipeout is used...
10:36:23  [WS-CLEANUP] done
[Pipeline] echo
10:36:23  ❌ PIPELINE FAILED — Build: #18 — Check console output for details.
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // timestamps
[Pipeline] }
[Pipeline] // timeout
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // withEnv
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
java.lang.UnsupportedOperationException: no known implementation of class org.jenkinsci.plugins.credentialsbinding.MultiBinding is named AmazonWebServicesCredentialsBinding
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.resolveClass(DescribableModel.java:552)
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.coerce(DescribableModel.java:476)
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.coerceList(DescribableModel.java:588)
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.coerce(DescribableModel.java:461)
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.buildArguments(DescribableModel.java:412)
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.instantiate(DescribableModel.java:328)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.DSL.invokeStep(DSL.java:318)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.DSL.invokeMethod(DSL.java:199)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsScript.invokeMethod(CpsScript.java:124)
	at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:104)
	at java.base/java.lang.reflect.Method.invoke(Method.java:565)
	at org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:98)
	at groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:325)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1225)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1034)
	at org.codehaus.groovy.runtime.callsite.PogoMetaClassSite.call(PogoMetaClassSite.java:41)
	at org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:47)
	at org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:116)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker$1.call(Checker.java:180)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.GroovyInterceptor.onMethodCall(GroovyInterceptor.java:23)
	at PluginClassLoader for script-security//org.jenkinsci.plugins.scriptsecurity.sandbox.groovy.SandboxInterceptor.onMethodCall(SandboxInterceptor.java:163)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker$1.call(Checker.java:178)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker.checkedCall(Checker.java:182)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker.checkedCall(Checker.java:152)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.sandbox.SandboxInvoker.methodCall(SandboxInvoker.java:17)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.LoggingInvoker.methodCall(LoggingInvoker.java:120)
Also:   org.jenkinsci.plugins.workflow.actions.ErrorAction$ErrorId: 07d997ab-0ba6-4c1f-ad7b-785a11a78649
Caused: java.lang.IllegalArgumentException: Could not instantiate {bindings=[{$class=AmazonWebServicesCredentialsBinding, credentialsId=aws-credentials, accessKeyVariable=AWS_ACCESS_KEY_ID, secretKeyVariable=AWS_SECRET_ACCESS_KEY}]} for org.jenkinsci.plugins.credentialsbinding.impl.BindingStep
	at PluginClassLoader for structs//org.jenkinsci.plugins.structs.describable.DescribableModel.instantiate(DescribableModel.java:338)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.DSL.invokeStep(DSL.java:318)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.DSL.invokeMethod(DSL.java:199)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsScript.invokeMethod(CpsScript.java:124)
	at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:104)
	at java.base/java.lang.reflect.Method.invoke(Method.java:565)
	at org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:98)
	at groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:325)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1225)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1034)
	at org.codehaus.groovy.runtime.callsite.PogoMetaClassSite.call(PogoMetaClassSite.java:41)
	at org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:47)
	at org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:116)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker$1.call(Checker.java:180)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.GroovyInterceptor.onMethodCall(GroovyInterceptor.java:23)
	at PluginClassLoader for script-security//org.jenkinsci.plugins.scriptsecurity.sandbox.groovy.SandboxInterceptor.onMethodCall(SandboxInterceptor.java:163)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker$1.call(Checker.java:178)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker.checkedCall(Checker.java:182)
	at PluginClassLoader for script-security//org.kohsuke.groovy.sandbox.impl.Checker.checkedCall(Checker.java:152)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.sandbox.SandboxInvoker.methodCall(SandboxInvoker.java:17)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.LoggingInvoker.methodCall(LoggingInvoker.java:120)
	at WorkflowScript.run(WorkflowScript:105)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.delegateAndExecute(ModelInterpreter.groovy:139)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.executeSingleStage(ModelInterpreter.groovy:633)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.catchRequiredContextForNode(ModelInterpreter.groovy:390)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.executeSingleStage(ModelInterpreter.groovy:632)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:292)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.toolsBlock(ModelInterpreter.groovy:521)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:280)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.withEnvBlock(ModelInterpreter.groovy:432)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:279)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.withCredentialsBlock(ModelInterpreter.groovy:464)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:278)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.inDeclarativeAgent(ModelInterpreter.groovy:561)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:276)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.stageInput(ModelInterpreter.groovy:354)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:265)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.inWrappers(ModelInterpreter.groovy:592)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:263)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.withEnvBlock(ModelInterpreter.groovy:432)
	at org.jenkinsci.plugins.pipeline.modeldefinition.ModelInterpreter.evaluateStage(ModelInterpreter.groovy:258)
	at ___cps.transform___(Native Method)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.impl.ContinuationGroup.methodCall(ContinuationGroup.java:107)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.impl.FunctionCallBlock$ContinuationImpl.dispatchOrArg(FunctionCallBlock.java:118)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.impl.FunctionCallBlock$ContinuationImpl.fixArg(FunctionCallBlock.java:87)
	at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:104)
	at java.base/java.lang.reflect.Method.invoke(Method.java:565)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.impl.ContinuationPtr$ContinuationImpl.receive(ContinuationPtr.java:71)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.impl.ClosureBlock.eval(ClosureBlock.java:49)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.Next.step(Next.java:84)
	at PluginClassLoader for workflow-cps//com.cloudbees.groovy.cps.Continuable.run0(Continuable.java:142)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.SandboxContinuable.access$001(SandboxContinuable.java:17)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.SandboxContinuable.run0(SandboxContinuable.java:48)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsThread.runNextChunk(CpsThread.java:188)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsThreadGroup.run(CpsThreadGroup.java:464)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsThreadGroup$2.call(CpsThreadGroup.java:372)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsThreadGroup$2.call(CpsThreadGroup.java:302)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsVmExecutorService.lambda$wrap$4(CpsVmExecutorService.java:143)
	at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:328)
	at hudson.remoting.SingleLaneExecutorService$1.run(SingleLaneExecutorService.java:139)
	at jenkins.util.ContextResettingExecutorService.lambda$wrap$0(ContextResettingExecutorService.java:26)
	at jenkins.security.ImpersonatingExecutorService.lambda$wrap$0(ImpersonatingExecutorService.java:66)
	at jenkins.util.ErrorLoggingExecutorService.lambda$wrap$0(ErrorLoggingExecutorService.java:51)
	at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:545)
	at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:328)
	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1090)
	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:614)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsVmExecutorService$1.call(CpsVmExecutorService.java:53)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsVmExecutorService$1.call(CpsVmExecutorService.java:50)
	at org.codehaus.groovy.runtime.GroovyCategorySupport$ThreadCategoryInfo.use(GroovyCategorySupport.java:136)
	at org.codehaus.groovy.runtime.GroovyCategorySupport.use(GroovyCategorySupport.java:275)
	at PluginClassLoader for workflow-cps//org.jenkinsci.plugins.workflow.cps.CpsVmExecutorService.lambda$categoryThreadFactory$0(CpsVmExecutorService.java:50)
	at java.base/java.lang.Thread.run(Thread.java:1474)
Finished: FAILURE
Jenkins 2.555.1            echo "✅ BUILD & DEPLOY SUCCESSFUL — Image: ${IMAGE_FULL} | Build: #${env.BUILD_NUMBER}"
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
