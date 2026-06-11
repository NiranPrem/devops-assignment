# Cloud Native Application Platform.

## Overview

This project implements a complete cloud-native application platform consisting of:

* Frontend Web Application
* Backend FastAPI Service
* PostgreSQL Database
* Kubernetes (K3s)
* Jenkins CI/CD Pipeline
* Prometheus Monitoring
* Grafana Dashboards
* Loki Log Aggregation
* Trivy Container Security Scanning
* Kubernetes Network Policies

The platform is deployed across two environments:

* DEV
* QAT

---

# Architecture

GitHub → Jenkins → Docker Build → Trivy Scan → Kubernetes Deployment

Frontend → Backend API → PostgreSQL

Prometheus → Metrics Collection

Grafana → Visualization

Promtail → Log Collection

Loki → Log Storage

---

# Repository Structure

```text
.
├── app
│   ├── api
│   └── web
├── k8s
│   ├── base
│   └── overlays
│       ├── dev
│       └── qat
├── monitoring
├── environments
│   └── local
├── Jenkinsfile
├── deploy.sh
├── docker-compose.yml
└── README.md
```

---

# Prerequisites

## Operating System

Ubuntu 22.04+ (Recommended)

## Required Tools

Install:

```bash
sudo apt update

sudo apt install -y \
git \
curl \
wget \
jq \
net-tools
```

---

# Docker Installation

```bash
curl -fsSL https://get.docker.com | sh

sudo systemctl enable docker

sudo systemctl start docker
```

Verify:

```bash
docker version
```

---

# Kubernetes Installation (K3s)

Install K3s:

```bash
curl -sfL https://get.k3s.io | sh -
```

Verify:

```bash
kubectl get nodes
```

Expected:

```text
Ready
```

---

# Clone Repository

```bash
git clone https://github.com/<YOUR_USERNAME>/devops-assignment.git

cd devops-assignment
```

---

# Environment Variables

Create local environment file:

```bash
mkdir -p environments/local
```

```bash
cat > environments/local/.env <<EOF
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppassword
POSTGRES_DB=appdb
EOF
```

---

# Local Deployment

Start:

```bash
./deploy.sh start
```

Check status:

```bash
./deploy.sh status
```

Restart:

```bash
./deploy.sh restart
```

Stop:

```bash
./deploy.sh stop
```

---

# Build Images

Backend:

```bash
docker build -t devops-assignment/api:latest app/api
```

Frontend:

```bash
docker build -t devops-assignment/web:latest app/web
```

---

# Kubernetes Deployment

## DEV

```bash
kubectl apply -k k8s/overlays/dev
```

Verify:

```bash
kubectl get all -n dev
```

---

## QAT

```bash
kubectl apply -k k8s/overlays/qat
```

Verify:

```bash
kubectl get all -n qat
```

---

# Verify Application

## Products API

```bash
curl http://<SERVER_IP>:30082/products
```

Expected:

```json
[
  {
    "id": 1,
    "name": "Premium Smartphone"
  }
]
```

---

## Customer Registration

```bash
curl -X POST \
http://<SERVER_IP>:30082/customers/register \
-H "Content-Type: application/json" \
-d '{
"fullname":"John Doe",
"email":"john@example.com"
}'
```

---

## Customer List

```bash
curl http://<SERVER_IP>:30082/customers/list
```

---

# PostgreSQL Verification

Connect:

```bash
kubectl exec -it -n dev \
$(kubectl get pod -n dev -l app=postgres -o jsonpath='{.items[0].metadata.name}') \
-- psql -U appuser -d appdb
```

Show tables:

```sql
\dt
```

Query customers:

```sql
SELECT * FROM customers;
```

Query products:

```sql
SELECT * FROM products;
```

---

# Monitoring

## Prometheus

Port Forward:

```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

Access:

```text
http://localhost:9090
```

---

## Grafana

Port Forward:

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

Access:

```text
http://localhost:3000
```

---

# Logging

Components:

* Loki
* Promtail

Verify:

```bash
kubectl get pods -n monitoring
```

---

# Security

## Trivy Scan

Run:

```bash
trivy image devops-assignment/api:latest

trivy image devops-assignment/web:latest
```

---

# Network Policies

Verify:

```bash
kubectl get networkpolicy -A
```

Implemented:

* Default Deny Ingress
* Default Deny Egress
* Web → API Access
* API → PostgreSQL Access
* Prometheus Scraping Access

---

# CI/CD Pipeline

Pipeline Stages:

1. Checkout Source
2. Build Docker Images
3. Trivy Security Scan
4. Deploy DEV
5. Deploy QAT
6. Verify Rollout

Pipeline Trigger:

```bash
git push origin main
```

or

Run Jenkins Build Now.

---

# Health Checks

API:

```bash
curl http://<SERVER_IP>:30082/healthz
```

Frontend:

```bash
curl http://<SERVER_IP>:30080/healthz
```

PostgreSQL:

```bash
kubectl describe pod -n dev -l app=postgres
```

---

# Troubleshooting

Check Pods:

```bash
kubectl get pods -A
```

Check Logs:

```bash
kubectl logs -n dev deployment/api
```

Restart Deployment:

```bash
kubectl rollout restart deployment/api -n dev
```

Verify Rollout:

```bash
kubectl rollout status deployment/api -n dev
```

---

# Deliverables

* Frontend Application
* Backend API
* PostgreSQL Database
* Jenkins CI/CD
* Kubernetes Deployments
* Prometheus Monitoring
* Grafana Dashboards
* Loki Logging
* Trivy Security Scanning
* Network Policies
* DEV Environment
* QAT Environment
