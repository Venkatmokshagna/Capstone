# Deploy Waterborne Disease App on AWS EKS

## Architecture

```
Internet (HTTP :80)
       ↓
AWS Load Balancer  ← auto-created by EKS LoadBalancer Service
       ↓
EKS Cluster (2 pods, Flask/Gunicorn :5000)
       ↓
AWS RDS MySQL (private VPC subnet, :3306)
```

---

## Prerequisites

Install these tools:

| Tool | Install |
|---|---|
| AWS CLI v2 | https://aws.amazon.com/cli/ |
| eksctl | https://eksctl.io/installation/ |
| kubectl | https://kubernetes.io/docs/tasks/tools/ |
| Docker Desktop | https://www.docker.com/products/docker-desktop/ |

```powershell
# Verify installs
aws --version
eksctl version
kubectl version --client
docker --version
```

---

## Step 1 — Configure AWS CLI

```powershell
aws configure
```
Enter:
- **AWS Access Key ID** → AWS Console → IAM → Users → your user → Security Credentials → Create Access Key
- **AWS Secret Access Key** → from the same screen
- **Default region** → `eu-north-1` (Stockholm, where you are) or your preferred region
- **Output format** → `json`

```powershell
# Verify your identity
aws sts get-caller-identity
# Expected: shows your Account ID, UserID, ARN
```
> Note your **Account ID** (12-digit number) — you'll need it for ECR.

---

## Step 2 — Create ECR Repository & Push Docker Image

```powershell
# Set your region and account ID as variables
$AWS_REGION = "eu-north-1"
$AWS_ACCOUNT_ID = "YOUR_12_DIGIT_ACCOUNT_ID"

# Create the ECR repository
aws ecr create-repository --repository-name waterborne-app --region $AWS_REGION

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | `
  docker login --username AWS --password-stdin `
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Build the Docker image
cd c:\Users\moksh\Downloads\waterbornedisease-main\waterbornedisease-main
docker build -t waterborne-app:latest .

# Tag for ECR
docker tag waterborne-app:latest `
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/waterborne-app:latest"

# Push to ECR
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/waterborne-app:latest"
```

---

## Step 3 — Create EKS Cluster

```powershell
# This takes ~15 minutes — creates the cluster + node group
eksctl create cluster `
  --name waterborne-cluster `
  --region $AWS_REGION `
  --nodegroup-name waterborne-nodes `
  --node-type t3.small `
  --nodes 2 `
  --nodes-min 1 `
  --nodes-max 3 `
  --managed

# Verify nodes are ready
kubectl get nodes
# Expected: 2 nodes in "Ready" state
```

> **Cost note:** `t3.small` = ~$0.02/hr per node (~$30/month for 2 nodes).  
> Use `t3.micro` to reduce cost, but Flask + MySQL may need more than 1 GB RAM.

---

## Step 4 — Attach ECR Access Policy to Node IAM Role

```powershell
# Get the node group IAM role name
eksctl get nodegroup `
  --cluster waterborne-cluster `
  --region $AWS_REGION `
  -o json | ConvertFrom-Json | Select-Object -ExpandProperty NodeGroups | `
  Select-Object -ExpandProperty NodeGroupName

# Attach ECR read policy to the node role
# Go to: AWS Console → IAM → Roles → eksctl-waterborne-cluster-nodegroup-... → Add Permissions
# Attach: AmazonEC2ContainerRegistryReadOnly
```

**Or via CLI:**
```powershell
# Find the role name
$ROLE_NAME = (aws iam list-roles --query "Roles[?contains(RoleName, 'NodeGroup')].RoleName" --output text)

# Attach the policy
aws iam attach-role-policy `
  --role-name $ROLE_NAME `
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

---

## Step 5 — Create RDS MySQL Database

```powershell
# Create a DB subnet group using your cluster's VPC subnets
# Easiest: use AWS Console:
```

1. **AWS Console → RDS → Create database**
2. Choose:
   - Engine: **MySQL 8.0**
   - Template: **Free tier** (or Production)
   - DB identifier: `waterborne-db`
   - Master username: `admin`
   - Master password: *(your strong password)*
   - Instance: `db.t3.micro` (Free Tier eligible)
   - VPC: **Select the same VPC as your EKS cluster** (check VPC ID in EKS Console)
   - Public access: **No** (private — EKS pods in same VPC will connect)
3. Click **Create Database** (~5 min)
4. After creation: open the DB → **Connectivity & security** → copy the **Endpoint**

---

## Step 6 — Allow EKS Nodes to Connect to RDS

1. **AWS Console → RDS → waterborne-db → Connectivity & security → VPC security groups**
2. Click the security group → **Inbound rules → Edit inbound rules**
3. Add rule:
   - Type: **MySQL/Aurora**
   - Port: **3306**
   - Source: **Custom** → use the **EKS node security group** (found in EC2 → Security Groups, look for `eksctl-waterborne-cluster-nodegroup`)

---

## Step 7 — Initialize the Database Schema

```powershell
# From your local machine (if RDS is temporarily public):
mysql -h YOUR_RDS_ENDPOINT.rds.amazonaws.com -u admin -p waterborne_db < init.sql

# Or from inside an EKS pod:
kubectl run mysql-client --image=mysql:8.0 -it --rm --restart=Never -- `
  mysql -h YOUR_RDS_ENDPOINT.rds.amazonaws.com -u admin -p waterborne_db
# Then paste the contents of init.sql
```

> If `waterborne_db` doesn't exist:
> ```sql
> CREATE DATABASE waterborne_db;
> ```

---

## Step 8 — Fill In Your Values

**Edit `k8s/deployment.yaml` line 22** — replace:
```
YOUR_AWS_ACCOUNT_ID  → your 12-digit AWS Account ID
YOUR_AWS_REGION      → e.g., eu-north-1
```

**Edit `k8s/secret.yaml`** — replace all placeholders:
- `YOUR_RDS_ENDPOINT.rds.amazonaws.com` → endpoint from Step 5
- `YOUR_RDS_PASSWORD` → password you set in Step 5
- `REPLACE_WITH_STRONG_RANDOM_SECRET` → run:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 9 — Deploy to EKS

```powershell
cd c:\Users\moksh\Downloads\waterbornedisease-main\waterbornedisease-main

# Apply manifests in order:
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Watch pods start up (takes ~60 seconds):
kubectl get pods -w
```

Expected:
```
NAME                             READY   STATUS    RESTARTS   AGE
waterborne-app-xxx-yyy           1/1     Running   0          60s
waterborne-app-xxx-zzz           1/1     Running   0          60s
```

---

## Step 10 — Get Your Public URL

```powershell
kubectl get svc waterborne-service
```

Wait ~2 minutes for `EXTERNAL-IP` to populate (AWS LB provisioning). Then open:

```
http://EXTERNAL-IP/
```

**Your app is live! 🎉**

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImagePullBackOff` | Re-run Step 4 to attach `AmazonEC2ContainerRegistryReadOnly` to node role |
| `CrashLoopBackOff` | Run `kubectl logs <pod-name>` — likely DB connection issue |
| DB connection refused | Check RDS security group allows port 3306 from EKS node SG (Step 6) |
| `EXTERNAL-IP` stuck at `<pending>` | Wait 3–5 min, AWS LB takes time to provision |
| Pods not scheduling | Check `kubectl describe pod <pod-name>` for resource constraint issues |

```powershell
# Useful debug commands
kubectl logs <pod-name>              # App logs
kubectl describe pod <pod-name>      # Detailed pod events
kubectl describe svc waterborne-service  # Service status
```

---

## Quick Reference — Values to Collect

| Value | Where to Find |
|---|---|
| `AWS_ACCOUNT_ID` | `aws sts get-caller-identity` → `Account` |
| `AWS_REGION` | Where you created the EKS cluster (e.g., `eu-north-1`) |
| `YOUR_RDS_ENDPOINT` | RDS Console → DB → Connectivity & security → Endpoint |
| `YOUR_RDS_PASSWORD` | Password you chose in Step 5 |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
