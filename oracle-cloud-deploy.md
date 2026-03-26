# Deploy Waterborne Disease App on Oracle Kubernetes Engine (OKE)

## Prerequisites

Install these tools first:

| Tool | Install Link |
|---|---|
| OCI CLI | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm |
| kubectl | https://kubernetes.io/docs/tasks/tools/ |
| Docker Desktop | https://www.docker.com/products/docker-desktop/ |

---

## Step 1 — Find Your OCI Tenancy Namespace

```powershell
# After installing OCI CLI and running: oci setup config
oci os ns get
```
> Note the output (e.g., `axvd3xyz1abc`). This is your **TENANCY_NAMESPACE**.  
> Your **REGION** code is found in OCI Console top-right (e.g., `ap-mumbai-1`, `us-ashburn-1`).

---

## Step 2 — Create an OKE Cluster (OCI Console)

1. Go to **OCI Console → Developer Services → Kubernetes Clusters (OKE)**
2. Click **Create Cluster → Quick Create**
3. Set:
   - Name: `waterborne-cluster`
   - Kubernetes version: Latest (default)
   - Node shape: `VM.Standard.E2.1.Micro` (Always Free)
   - Node count: `2`
4. Click **Next → Create Cluster** (takes ~5 minutes)

---

## Step 3 — Connect kubectl to OKE

```powershell
# In OCI Console → OKE → waterborne-cluster → Access Cluster → Local Access
# Run the command shown, which looks like:
oci ce cluster create-kubeconfig `
  --cluster-id ocid1.cluster.oc1.xxx `
  --file $HOME\.kube\config `
  --region YOUR_REGION `
  --token-version 2.0.0

# Verify connection
kubectl get nodes
# Expected: 2 nodes in "Ready" state
```

---

## Step 4 — Create OCI MySQL HeatWave Database

1. **OCI Console → Databases → MySQL HeatWave**
2. Click **Create DB System**
3. Set:
   - Name: `waterborne-db`
   - Admin username: `admin`
   - Admin password: *(your strong password)*
   - Shape: `MySQL.Free` (Always Free tier)
4. After creation (~5 min), go to the DB details and **copy the Private IP** (Endpoint)
5. **Update `k8s/secret.yaml`** — replace `YOUR_OCI_MYSQL_ENDPOINT` with this IP

---

## Step 5 — Initialize the Database Schema

```powershell
# SSH into an OCI compute instance in the same VCN as the DB, OR use MySQL Shell:
# OCI Console → MySQL DB → Connect → Cloud Shell connection

# Then run the init.sql:
mysql -h YOUR_OCI_MYSQL_ENDPOINT -u admin -p waterborne_db < init.sql
```

> If `waterborne_db` doesn't exist yet, create it first:
> ```sql
> CREATE DATABASE waterborne_db;
> ```

---

## Step 6 — Create OCIR Repository & Push Docker Image

```powershell
# 1. Generate an OCI Auth Token:
#    OCI Console → Profile (top-right) → Auth Tokens → Generate Token
#    Copy the token — it won't be shown again!

# 2. Log Docker into OCIR
docker login YOUR_REGION.ocir.io `
  --username "YOUR_TENANCY_NAMESPACE/YOUR_OCI_USERNAME" `
  --password "YOUR_AUTH_TOKEN"

# 3. Build your Docker image
cd c:\Users\moksh\Downloads\waterbornedisease-main\waterbornedisease-main
docker build -t waterborne-app:latest .

# 4. Tag for OCIR
docker tag waterborne-app:latest `
  YOUR_REGION.ocir.io/YOUR_TENANCY_NAMESPACE/waterborne-app:latest

# 5. Push to OCIR
docker push YOUR_REGION.ocir.io/YOUR_TENANCY_NAMESPACE/waterborne-app:latest
```

**Make it public (recommended for simplicity):**  
OCI Console → Developer Services → Container Registry → waterborne-app → Actions → **Change to Public**  
*(If public, you can skip Step 7)*

---

## Step 7 — Create OCIR Pull Secret in OKE

> Skip this step if you made the OCIR repository **public** in Step 6.

```powershell
kubectl create secret docker-registry ocir-secret `
  --docker-server=YOUR_REGION.ocir.io `
  --docker-username="YOUR_TENANCY_NAMESPACE/YOUR_OCI_USERNAME" `
  --docker-password="YOUR_AUTH_TOKEN" `
  --docker-email="YOUR_EMAIL"
```

---

## Step 8 — Fill In Your Values

Edit `k8s/deployment.yaml` line 19 — replace placeholders:
```
YOUR_REGION          → e.g., ap-mumbai-1
YOUR_TENANCY_NAMESPACE → from Step 1, e.g., axvd3xyz1abc
```

Edit `k8s/secret.yaml` — replace all placeholders with real values.

Generate a strong SECRET_KEY:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 9 — Deploy to OKE

```powershell
cd c:\Users\moksh\Downloads\waterbornedisease-main\waterbornedisease-main

# Apply in order:
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Watch pods come up (takes ~60 seconds):
kubectl get pods -w
```

Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
waterborne-app-xxx-yyy            1/1     Running   0          60s
waterborne-app-xxx-zzz            1/1     Running   0          60s
```

---

## Step 10 — Get Your Public URL

```powershell
kubectl get svc waterborne-service
```

Wait until `EXTERNAL-IP` shows a real IP (not `<pending>`). Then open:

```
http://EXTERNAL-IP/
```

Your app is live! 🎉

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Pods stuck in `ImagePullBackOff` | Check OCIR repo is public OR ocir-secret is correct |
| Pods stuck in `CrashLoopBackOff` | Run `kubectl logs <pod-name>` to see Flask errors |
| DB connection refused | Ensure OCI MySQL Security List allows port 3306 from OKE VCN CIDR |
| `EXTERNAL-IP` stays `<pending>` | Wait 2-3 min; OCI LB provisioning takes time |

### Check MySQL connectivity from OKE:
```powershell
# Test DB access from inside a pod
kubectl exec -it <pod-name> -- python -c "
import mysql.connector
c = mysql.connector.connect(host='YOUR_DB_IP', user='admin', password='YOUR_PW', database='waterborne_db')
print('DB connected:', c.is_connected())
"
```

---

## Architecture Summary

```
Internet (HTTP :80)
       ↓
OCI Load Balancer  ← auto-created by LoadBalancer Service
       ↓
OKE Cluster (2 pods, Flask/Gunicorn :5000)
       ↓
OCI MySQL HeatWave (private VCN, :3306)
```

---

## Quick Reference — Values To Collect

| Value | Where to Find |
|---|---|
| `YOUR_REGION` | OCI Console → top-right dropdown (e.g., `ap-mumbai-1`) |
| `YOUR_TENANCY_NAMESPACE` | `oci os ns get` |
| `YOUR_OCI_USERNAME` | OCI Console → Profile → Username |
| `YOUR_AUTH_TOKEN` | OCI Console → Profile → Auth Tokens |
| `YOUR_OCI_MYSQL_ENDPOINT` | OCI Console → MySQL DB System → Endpoint |
