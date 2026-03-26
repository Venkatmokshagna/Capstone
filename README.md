# 💧 Waterborne Disease Monitoring System
**SIH Project — Team CEREBRO TECH**

🚀 **Live Demo:** [http://a173c5ddc4e854918bef501c51998df0-1291905136.eu-north-1.elb.amazonaws.com](http://a173c5ddc4e854918bef501c51998df0-1291905136.eu-north-1.elb.amazonaws.com)

A full-stack, AI-powered waterborne disease monitoring platform with multi-role dashboards, real-time water quality analysis, and cloud-native deployment on AWS.

---

## ✅ Working Features

- **User Registration & Login** — Live authentication with BCrypt-hashed passwords
- **Multi-role System** — ASHA Worker, Volunteer, Admin, and Patient dashboards
- **AI Water Analysis** — Image-based drinkability detection using NumPy & Pillow
- **MySQL Database** — Persistent, production-grade data storage (AWS RDS)
- **Multi-language Support**
- **Responsive Design**

---

## 🛠 Technology Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.10** | Core language |
| **Flask 2.3.3** | Web framework & REST API |
| **Gunicorn** | Production WSGI server |
| **Flask-CORS** | Cross-origin resource sharing |
| **Werkzeug 2.3.7** | WSGI utilities |

### Database
| Technology | Purpose |
|---|---|
| **MySQL** | Relational database |
| **AWS RDS (MySQL)** | Managed cloud database |
| **mysql-connector-python 8.3.0** | Python ↔ MySQL driver |

### AI / Machine Learning
| Technology | Purpose |
|---|---|
| **NumPy** | Numerical image processing |
| **Pillow** | Image loading & manipulation |

### Security & Auth
| Technology | Purpose |
|---|---|
| **BCrypt 4.0.1** | Password hashing |
| **Flask Sessions** | Session-based authentication |

### Infrastructure & DevOps
| Technology | Purpose |
|---|---|
| **Docker** | Containerization |
| **AWS ECR** | Container image registry |
| **AWS EKS** | Managed Kubernetes cluster |
| **Kubernetes** | Container orchestration (2 replicas) |
| **AWS RDS** | Managed MySQL database |

---

## 🚀 Deployment Architecture

```
User → AWS EKS (Kubernetes)
         └── Docker Container (Flask + Gunicorn)
                  └── AWS RDS (MySQL)
```

- Container image stored in **AWS ECR** (`eu-north-1`)
- Kubernetes `Deployment` with **2 replicas**, resource limits, readiness & liveness probes
- Secrets managed via **Kubernetes Secrets** (`waterborne-secret`)
- Database hosted on **AWS RDS MySQL**

---

## 🎯 Quick Test

1. Visit the live URL
2. Click any role → **"Request Access"**
3. Register as a new user
4. Login with the same credentials
5. Access your role-specific dashboard

---

## 📞 Contact

📧 [mokshagna1522@gmail.com](mailto:mokshagna1522@gmail.com)

> Search on Google: **SAMAJ HEALTH SURAKSHA - LOGIN PORTAL**
