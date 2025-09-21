# Deployment Guide

## Production Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- Helm 3.x
- Docker registry access
- SSL certificates

### Environment Setup

#### 1. Infrastructure Provisioning
```bash
# AWS EKS cluster
eksctl create cluster --name research-papers --region us-west-2 --nodes 3

# GCP GKE cluster  
gcloud container clusters create research-papers --zone us-central1-a --num-nodes 3
```

#### 2. Database Setup
```bash
# PostgreSQL (AWS RDS / GCP Cloud SQL)
helm install postgres bitnami/postgresql \
  --set auth.postgresPassword=<secure-password> \
  --set primary.persistence.size=100Gi

# Redis (AWS ElastiCache / GCP Memorystore)
helm install redis bitnami/redis \
  --set auth.password=<secure-password>
```

#### 3. Search & Analytics
```bash
# Elasticsearch cluster
helm install elasticsearch elastic/elasticsearch \
  --set replicas=3 \
  --set minimumMasterNodes=2

# Kafka for streaming
helm install kafka bitnami/kafka \
  --set replicaCount=3
```

### Application Deployment

#### 1. Build & Push Images
```bash
# Backend API
docker build -t research-papers/backend:v1.0.0 ./backend
docker push research-papers/backend:v1.0.0

# ML Service
docker build -t research-papers/ml-service:v1.0.0 ./ml-service
docker push research-papers/ml-service:v1.0.0

# Frontend
docker build -t research-papers/frontend:v1.0.0 ./frontend
docker push research-papers/frontend:v1.0.0

# Data Pipeline
docker build -t research-papers/data-pipeline:v1.0.0 ./data-pipeline
docker push research-papers/data-pipeline:v1.0.0
```

#### 2. Kubernetes Deployment
```bash
# Deploy all services
kubectl apply -f deployment/k8s/

# Verify deployments
kubectl get pods -n research-papers
kubectl get services -n research-papers
```

### Configuration Management

#### Environment Variables
```yaml
# ConfigMap for application settings
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/research_papers"
  REDIS_URL: "redis://redis:6379"
  ELASTICSEARCH_URL: "http://elasticsearch:9200"
  ARXIV_API_RATE_LIMIT: "100"
```

#### Secrets Management
```bash
# Create secrets for sensitive data
kubectl create secret generic app-secrets \
  --from-literal=database-password=<password> \
  --from-literal=redis-password=<password> \
  --from-literal=jwt-secret=<secret>
```

### Monitoring & Logging

#### Prometheus & Grafana
```bash
# Install monitoring stack
helm install monitoring prometheus-community/kube-prometheus-stack \
  --set grafana.adminPassword=<admin-password>
```

#### Application Metrics
- API response times and error rates
- Paper processing throughput
- ML model inference latency
- Database connection pool usage
- Cache hit/miss ratios

#### Log Aggregation
```bash
# ELK Stack deployment
helm install elasticsearch elastic/elasticsearch
helm install kibana elastic/kibana
helm install filebeat elastic/filebeat
```

### Scaling Configuration

#### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Vertical Pod Autoscaler
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ml-service-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-service
  updatePolicy:
    updateMode: "Auto"
```

### Backup & Disaster Recovery

#### Database Backups
```bash
# Automated PostgreSQL backups
kubectl create cronjob postgres-backup \
  --image=postgres:15 \
  --schedule="0 2 * * *" \
  -- pg_dump -h postgres -U user research_papers > /backup/$(date +%Y%m%d).sql
```

#### Application State Backup
- Vector embeddings backup to S3/GCS
- Elasticsearch snapshots
- Redis persistence configuration
- Configuration and secrets backup

### Security Considerations

#### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

#### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: research-papers-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

### Performance Tuning

#### Database Optimization
- Connection pooling (PgBouncer)
- Read replicas for query distribution
- Proper indexing strategy
- Query performance monitoring

#### Caching Strategy
- Redis cluster for distributed caching
- CDN for static assets (CloudFront/CloudFlare)
- Application-level caching
- Database query result caching

#### Resource Allocation
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```