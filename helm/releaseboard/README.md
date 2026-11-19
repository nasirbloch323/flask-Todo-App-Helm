# ReleaseBoard Helm Chart — Learn Every Building Block

This chart deploys a Flask release-tracking application and demonstrates the Kubernetes objects used by a real web workload.

## 1. Helm in plain language

- **Chart**: a packaged folder of templates and default settings.
- **Release**: one installed instance of a chart. You can install the same chart as `dev`, `staging`, and `production`.
- **values.yaml**: the configuration input. Change image, replicas, storage, probes, and exposure without rewriting templates.
- **Template**: YAML containing Go-template expressions such as `{{ .Values.replicaCount }}`.
- **Rendered manifest**: ordinary Kubernetes YAML produced by `helm template`.
- **Revision**: each successful install or upgrade creates a revision that can be rolled back.

## 2. Chart file map

| File | What it teaches |
|---|---|
| Chart.yaml | Chart identity and versions |
| values.yaml | Every configurable default |
| templates/_helpers.tpl | Reusable names and labels |
| deployment.yaml | Pods, replicas, probes, resources, security, volumes |
| service.yaml | Stable in-cluster networking |
| configmap.yaml | Non-secret environment configuration |
| secret.yaml | Sensitive Flask signing key |
| pvc.yaml | Persistent storage request |
| ingress.yaml | Host/path routing (optional) |
| hpa.yaml | CPU-based horizontal scaling (optional) |
| pdb.yaml | Availability during voluntary disruption (optional) |
| networkpolicy.yaml | Incoming traffic restrictions (optional) |
| serviceaccount.yaml | Workload identity |
| tests/test-connection.yaml | `helm test` hook |

## 3. Local development

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
DATABASE_PATH=./data/releases.db flask --app app run --debug
```

Open http://127.0.0.1:5000. The app stores records in SQLite and exposes `/healthz`, `/readyz`, and `/metrics`.

## 4. Build and run the container

```bash
docker build -t releaseboard:1.0.0 .
docker run --rm -p 5000:5000 -v releaseboard-data:/data releaseboard:1.0.0
```

The image runs as UID 10001, uses Gunicorn, and stores writable data under `/data`.

## 5. Validate the chart before installing

```bash
helm lint ./helm/releaseboard
helm template demo ./helm/releaseboard --debug
helm template demo ./helm/releaseboard --set ingress.enabled=true
```

- `helm lint` checks chart structure and common mistakes.
- `helm template` renders templates locally; it does not contact the cluster.
- `--debug` prints useful rendering context.

## 6. Install on KIND or another Kubernetes cluster

Build the image and load it into KIND:

```bash
docker build -t releaseboard:1.0.0 .
kind load docker-image releaseboard:1.0.0 --name helm
```

For a local KIND image, override the image repository/tag:

```bash
helm upgrade --install releaseboard ./helm/releaseboard \
  --set image.repository=releaseboard \
  --set image.tag=1.0.0 \
  --set image.pullPolicy=IfNotPresent
```

Inspect the objects:

```bash
helm list
helm status releaseboard
kubectl get deploy,pods,svc,pvc
kubectl describe pod -l app.kubernetes.io/instance=releaseboard
kubectl logs deploy/releaseboard
kubectl port-forward svc/releaseboard 8080:80
```

Open http://127.0.0.1:8080.

> SQLite with one ReadWriteOnce PVC is a learning setup for a single replica. For multi-replica production use, move state to PostgreSQL or another external database before enabling HPA.

## 7. Explore Helm values

```bash
# Run two Pods (use shared/external storage before scaling stateful SQLite).
helm upgrade --install releaseboard ./helm/releaseboard --set replicaCount=2

# Enable ingress after installing an Ingress controller and setting a real hostname.
helm upgrade --install releaseboard ./helm/releaseboard \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=releaseboard.local

# Enable autoscaling only when metrics-server is available and the app uses external storage.
helm upgrade --install releaseboard ./helm/releaseboard --set autoscaling.enabled=true
```

For sensitive configuration, do not commit real values to Git. Supply a private values file or use an external secret manager:

```bash
helm upgrade --install releaseboard ./helm/releaseboard \
  --set secret.create=true \
  --set-string secret.flaskSecretKey='REPLACE_WITH_A_LONG_RANDOM_VALUE'
```

## 8. Upgrade, rollback, and remove

```bash
helm history releaseboard
helm upgrade releaseboard ./helm/releaseboard --set appConfig.environment=staging
helm rollback releaseboard 1
helm uninstall releaseboard
```

## 9. Interview questions to practice

1. Why does a Deployment use a selector and matching Pod labels?
2. What is the difference between liveness and readiness probes?
3. Why should configuration be outside the Docker image?
4. Why is a Secret different from a ConfigMap?
5. What does a PVC request, and what does a StorageClass do?
6. How does a Service continue working when Pod IP addresses change?
7. What does Helm render before Kubernetes receives the manifests?
8. What is a Helm release revision, and how does rollback work?
9. Why should a stateful SQLite application not be scaled to multiple Pods on one RWO volume?
10. How do CPU requests and limits affect scheduling and runtime behavior?
