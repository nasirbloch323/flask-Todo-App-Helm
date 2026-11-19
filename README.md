# ReleaseBoard — Flask, Docker, Kubernetes & Helm Learning Project

A hands-on DevOps project that transforms the original TODO demo into a **Cloud Operations Release Board**. Learn how an application is built, containerized, configured by Helm, and operated on Kubernetes.

## What the application does

- Create release records for services and versions.
- Track Planned, Deploying, Deployed, and Failed states.
- Persist release data in SQLite under `/data`.
- Expose Kubernetes liveness and readiness endpoints plus Prometheus-format metrics.
- Run with Gunicorn as a non-root container user.

## Architecture

```text
Browser -> Kubernetes Service -> Deployment -> Pod -> Gunicorn -> Flask ReleaseBoard
                                                        |             |
                                                        |             +--> /healthz /readyz /metrics
                                                        +--> PVC mounted at /data -> SQLite

Helm Chart (Chart.yaml + values.yaml + templates/)
  -> Deployment, Service, ConfigMap, optional Secret, PVC,
     optional Ingress, HPA, PDB, NetworkPolicy, ServiceAccount, Helm test
```

## Repository structure

```text
.
├── app.py
├── templates/index.html
├── static/style.css
├── Dockerfile
├── requirements.txt
├── helm/releaseboard/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── README.md
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── pvc.yaml
│       ├── ingress.yaml
│       ├── hpa.yaml
│       ├── pdb.yaml
│       ├── networkpolicy.yaml
│       ├── serviceaccount.yaml
│       └── tests/test-connection.yaml
└── .github/workflows/helm-ci.yml
```

## 1. Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
DATABASE_PATH=./data/releases.db flask --app app run --debug
```

Open http://127.0.0.1:5000. The database file is created automatically. Try adding releases and changing their statuses.

## 2. Build and run Docker

```bash
docker build -t releaseboard:1.0.0 .
docker run --rm -p 5000:5000 -v releaseboard-data:/data releaseboard:1.0.0
```

The image runs as UID 10001, uses Gunicorn, and writes application data to `/data`.

## 3. Understand and validate Helm

Read the [complete Helm learning guide](helm/releaseboard/README.md). Every chart value and Kubernetes resource is documented with comments.

```bash
helm lint ./helm/releaseboard
helm template releaseboard ./helm/releaseboard --debug
helm template releaseboard ./helm/releaseboard --set ingress.enabled=true
```

- `helm lint` checks chart structure and common mistakes.
- `helm template` renders ordinary Kubernetes YAML locally; it does not install anything.
- `values.yaml` is the configuration input; templates turn those values into Kubernetes resources.

## 4. Deploy to KIND

Build and load the image into your local KIND cluster:

```bash
docker build -t releaseboard:1.0.0 .
kind load docker-image releaseboard:1.0.0 --name helm
helm upgrade --install releaseboard ./helm/releaseboard \
  --set image.repository=releaseboard \
  --set image.tag=1.0.0 \
  --set image.pullPolicy=IfNotPresent
```

Inspect the release and Kubernetes resources:

```bash
helm list
helm status releaseboard
kubectl get deploy,pods,svc,pvc
kubectl logs deploy/releaseboard
kubectl port-forward svc/releaseboard 8080:80
```

Open http://127.0.0.1:8080.

## 5. Helm operations to practice

```bash
helm upgrade releaseboard ./helm/releaseboard --set appConfig.environment=staging
helm history releaseboard
helm rollback releaseboard 1
helm test releaseboard
helm uninstall releaseboard
```

## Important: understand stateful storage

The default SQLite + single ReadWriteOnce PVC setup is for learning and one replica. Do **not** scale this SQLite design with HPA or multiple replicas. For a multi-replica production application, move state to PostgreSQL or another external database first. Also supply a strong Flask secret through a private values file or a secret manager; never commit real credentials.

## Interview topics

1. Deployment selectors and matching Pod labels.
2. Liveness versus readiness probes.
3. ConfigMap versus Secret.
4. PersistentVolume versus PersistentVolumeClaim.
5. Service networking and ephemeral Pod IP addresses.
6. Helm chart, release, values, template, revision, and rollback.
7. CPU requests/limits and HorizontalPodAutoscaler.
8. Why SQLite on a single ReadWriteOnce volume is not a multi-replica architecture.

**Learning goal:** understand every line you deploy, not just copy Helm commands.
