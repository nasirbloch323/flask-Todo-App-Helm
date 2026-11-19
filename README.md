# ReleaseBoard — Complete DevOps Learning Project

> **Goal:** Learn how a real web application moves from Python source code to a Docker image, then to Kubernetes, and finally gets managed through Helm. This README is your study guide: read it from top to bottom, run each command, and explain the flow in your own words.

**Application:** ReleaseBoard — a small release/deployment tracking dashboard  
**Stack:** Python · Flask · SQLite · HTML/CSS · Docker · Kubernetes · Helm · GitHub Actions  
**Maintainer:** Nasir Mehmood  
**Learning branch:** `feature/helm-complete-learning-project`

---

## 1. First understand what this project does

This is not the original TODO application anymore. The application has been changed into a **ReleaseBoard**.

Imagine a software team is preparing a new version of its application. The team needs to record:

- Which service is being released (for example, `payments-api`).
- Which version is being released (for example, `v2.4.0`).
- Which environment will receive it (Development, Staging, or Production).
- The release status (Planned, Deploying, Deployed, or Failed).
- Optional notes describing the release.

ReleaseBoard stores this information in an SQLite database and displays it in a dashboard. The purpose is to give us an application that is easy to understand but still demonstrates real DevOps concepts: containerization, configuration, persistent storage, health checks, Kubernetes networking, Helm templating, and CI validation.

### What happens when you use the website?

1. Open the dashboard in your browser.
2. Enter a service name, version, environment, and optional notes.
3. Flask receives the form and validates required fields.
4. Flask writes the release record to SQLite.
5. The dashboard reads the records from SQLite and displays them.
6. You can change the status or delete a release.
7. When Kubernetes replaces the Pod, the database remains on the mounted persistent volume (when persistence is enabled and the PVC is retained).

---

## 2. Understand the complete architecture

### Application request flow

```text
Your browser
    |
    | HTTP request
    v
Kubernetes Service (stable address, port 80)
    |
    | forwards traffic to container port 5000
    v
Deployment
    |
    v
ReleaseBoard Pod
    |
    v
Gunicorn web server
    |
    v
Flask application (app.py)
    |                 |                 |
    v                 v                 v
HTML template     SQLite database    Health/metrics endpoints
templates/        /data/releases.db  /healthz /readyz /metrics
    |
    v
Browser displays ReleaseBoard
```

### How Helm fits into the picture

```text
Chart.yaml       -> identifies the Helm chart and its version
values.yaml      -> contains configurable default values
templates/       -> contains Kubernetes YAML templates
       |
       v
helm template    -> renders normal Kubernetes YAML
       |
       v
helm install / upgrade
       |
       v
Kubernetes API
       |
       +--> Deployment --> Pods
       +--> Service -----> stable internal network endpoint
       +--> ConfigMap ---> normal application configuration
       +--> Secret ------> sensitive Flask signing key (optional)
       +--> PVC ----------> persistent storage request
       +--> Ingress ------> external HTTP routing (optional)
       +--> HPA ----------> replica scaling (optional)
       +--> PDB ----------> voluntary disruption protection (optional)
       +--> NetworkPolicy -> network traffic rules (optional)
```

**Important difference:** Docker packages and runs the application. Kubernetes manages containers across a cluster. Helm creates and updates the Kubernetes resources using reusable templates and values.

---

## 3. Repository map — where everything lives

```text
.
├── app.py                         # Flask routes, validation, SQLite, health and metrics
├── requirements.txt               # Python packages installed in the image
├── Dockerfile                     # Instructions for building the application image
├── templates/
│   └── index.html                 # Dashboard structure and Flask/Jinja expressions
├── static/
│   └── style.css                  # Dashboard appearance and responsive styling
├── helm/
│   └── releaseboard/
│       ├── Chart.yaml             # Helm chart identity and versions
│       ├── values.yaml            # Default settings consumed by templates
│       ├── README.md              # Dedicated Helm learning guide
│       └── templates/
│           ├── _helpers.tpl       # Reusable names and labels
│           ├── deployment.yaml    # Pods, image, probes, security and volumes
│           ├── service.yaml       # Stable network access to Pods
│           ├── configmap.yaml     # Non-secret environment settings
│           ├── secret.yaml       # Optional Flask secret
│           ├── pvc.yaml          # PersistentVolumeClaim
│           ├── ingress.yaml      # Optional external HTTP routing
│           ├── hpa.yaml           # Optional CPU-based autoscaling
│           ├── pdb.yaml           # Optional disruption protection
│           ├── networkpolicy.yaml # Optional incoming traffic restrictions
│           ├── serviceaccount.yaml # Pod identity
│           └── tests/
│               └── test-connection.yaml # Helm test hook
└── .github/
    └── workflows/
        └── helm-ci.yml            # GitHub Actions Helm validation
```

---

## 4. Understand the Python application (app.py)

The source file is deliberately commented. These are the main sections and why they exist.

| Code section | What it does | Why it matters |
|---|---|---|
| Imports | Loads Flask, SQLite, OS and date/time helpers | Connects the web framework to the operating system and database |
| Flask configuration | Creates `app`, reads secret, database path, environment and version | Lets Docker/Kubernetes configure the same image differently |
| `get_db()` | Opens a database connection and closes it safely | Prevents connections being left open |
| `initialize_database()` | Creates the releases table if it does not exist | First startup prepares the database |
| `dashboard()` | Reads releases and summary counts | Supplies data to the HTML page |
| `create_release()` | Validates form data and inserts a release | Demonstrates an HTTP POST and SQL insert |
| `update_status()` | Checks the requested status and updates a row | Demonstrates input validation and SQL update |
| `delete_release()` | Deletes a selected record | Demonstrates a SQL delete |
| `health()` | Returns HTTP 200 from `/healthz` | Kubernetes liveness probe checks the process |
| `readiness()` | Checks the database through `/readyz` | Kubernetes knows whether the Pod can receive traffic |
| `metrics()` | Returns release counters in Prometheus text format | Demonstrates a basic monitoring endpoint |

### Important Python concepts

- **Route:** a URL handled by a Python function, such as `@app.get("/")`.
- **GET:** normally reads or displays information.
- **POST:** sends data or changes application state.
- **SQL placeholder (`?`):** safely passes values into SQL rather than joining untrusted text into a query.
- **Environment variable:** configuration passed to the running process without hardcoding it into the source.
- **Gunicorn:** production WSGI server that imports the Flask object as `app:app`.
- **SQLite:** file-based database. Here its file is `/data/releases.db`.

### Application endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Show the release dashboard |
| `/releases` | POST | Create a release |
| `/releases/<id>/status` | POST | Change release status |
| `/releases/<id>/delete` | POST | Delete a release |
| `/healthz` | GET | Liveness check |
| `/readyz` | GET | Database readiness check |
| `/metrics` | GET | Prometheus-format counters |

---

## 5. Understand the Dockerfile

Dockerfile instructions are processed to build an image.

| Instruction | Meaning in this project |
|---|---|
| `FROM python:3.12-slim` | Starts from a small official Python base image |
| `ENV` | Sets Python and pip runtime/build behavior |
| `RUN groupadd ... useradd ...` | Creates a dedicated non-root user with UID 10001 |
| `WORKDIR /app` | Sets the working directory inside the image |
| `COPY requirements.txt .` | Copies dependency definitions first for build caching |
| `RUN pip install ...` | Installs Flask and Gunicorn dependencies |
| `COPY app.py/templates/static` | Copies the application source and UI |
| `RUN mkdir ... chown ...` | Creates the data directory and assigns ownership |
| `USER app` | Runs the web server without root privileges |
| `EXPOSE 5000` | Documents the port used by Gunicorn |
| `CMD [...]` | Starts Gunicorn and serves the Flask object |

### Build and run Docker

From the repository root:

```bash
docker build -t releaseboard:1.0.0 .
docker run --rm -p 5000:5000 -v releaseboard-data:/data releaseboard:1.0.0
```

Open [http://localhost:5000](http://localhost:5000).

- `-p 5000:5000`: maps your computer's port 5000 to the container's port 5000.
- `-v releaseboard-data:/data`: mounts a named Docker volume so the SQLite file is outside the disposable container layer.
- `--rm`: removes the stopped container when it exits; the named volume remains.

Useful Docker commands:

```bash
docker images
docker ps
docker logs <container-name-or-id>
docker exec -it <container-name-or-id> sh
docker volume ls
docker stop <container-name-or-id>
```

---

## 6. Helm fundamentals — understand before memorizing commands

| Term | Simple explanation |
|---|---|
| Helm | A package manager for Kubernetes applications |
| Chart | The folder containing chart metadata, default values and templates |
| Release | An installed instance of a chart |
| `Chart.yaml` | Chart name, chart version, type and application version |
| `values.yaml` | Default configuration values |
| Template | A Kubernetes YAML file with Go-template expressions |
| Render | Convert templates and values into ordinary Kubernetes YAML |
| Revision | A saved version of an installed Helm release |
| Upgrade | Apply a new chart/configuration to an existing release |
| Rollback | Return a release to a previous revision |

### Understand a template expression

Example:

```yaml
replicas: {{ .Values.replicaCount }}
```

- `{{ ... }}` tells Helm to evaluate a template expression.
- `.Values` means read the values supplied to this chart.
- `replicaCount` is the key inside `values.yaml`.
- If `replicaCount: 1`, Helm renders `replicas: 1`.

### Understand the helper expression

```yaml
name: {{ include "releaseboard.fullname" . }}
```

- `include` calls a reusable template defined in `_helpers.tpl`.
- `releaseboard.fullname` is the helper's name.
- `.` passes the current chart context to that helper.

The helper makes resource names consistent. It avoids repeating the same naming logic in every template.

### Useful Helm template functions

| Function | Purpose |
|---|---|
| `include` | Runs a named helper template |
| `default` | Uses a fallback when a value is empty |
| `required` | Stops rendering if a required value is missing |
| `quote` | Wraps a value in quotes |
| `toYaml` | Converts an object/list into YAML |
| `nindent` | Adds a newline and indentation |
| `with` | Changes context when a value is present |
| `range` | Loops through a list or map |
| `if` | Renders a section only when a condition is true |
| `trunc` | Limits a string's length |
| `trimSuffix` | Removes a suffix from a string |

For the complete chart file guide, continue to [helm/releaseboard/README.md](helm/releaseboard/README.md).

---

## 7. Kubernetes resources — what each template creates

| Resource | File | Job |
|---|---|---|
| Deployment | `deployment.yaml` | Maintains the desired Pods and performs rolling updates |
| Service | `service.yaml` | Gives Pods a stable network endpoint |
| ConfigMap | `configmap.yaml` | Supplies normal settings such as environment and database path |
| Secret | `secret.yaml` | Optionally supplies the Flask signing key |
| PersistentVolumeClaim | `pvc.yaml` | Requests persistent storage for SQLite |
| Ingress | `ingress.yaml` | Optionally routes external HTTP traffic to the Service |
| HorizontalPodAutoscaler | `hpa.yaml` | Optionally changes replica count based on CPU metrics |
| PodDisruptionBudget | `pdb.yaml` | Limits voluntary disruptions during maintenance |
| NetworkPolicy | `networkpolicy.yaml` | Optionally restricts incoming Pod traffic |
| ServiceAccount | `serviceaccount.yaml` | Gives the Pod a Kubernetes identity |
| Helm test Pod | `tests/test-connection.yaml` | Tests access to the application's health endpoint |

### Important Deployment concepts

- **Pod:** the Kubernetes object that runs the application container.
- **Replica:** one running copy of the Pod.
- **Selector:** identifies which Pods belong to a Deployment or Service.
- **Labels:** key/value metadata used to identify and select resources.
- **Rolling update:** gradually replaces old Pods with new ones.
- **Liveness probe:** if it repeatedly fails, Kubernetes restarts the container.
- **Readiness probe:** if it fails, the Pod is removed from Service traffic until ready.
- **Resource request:** helps Kubernetes decide where to schedule a Pod.
- **Resource limit:** sets a maximum CPU/memory allowance for a container.
- **Volume mount:** makes storage available at a path inside the container.

### ConfigMap versus Secret

- ConfigMap: ordinary configuration such as `APP_ENV` and `DATABASE_PATH`.
- Secret: sensitive values such as `FLASK_SECRET_KEY`.
- A Kubernetes Secret is not automatically a complete secret-management solution. Restrict RBAC, enable encryption at rest where appropriate, and consider an external secret manager for production.

### PV versus PVC

- **PersistentVolume (PV):** the actual storage resource available to the cluster.
- **PersistentVolumeClaim (PVC):** an application's request for storage.
- **StorageClass:** tells Kubernetes how to provision storage dynamically.
- This chart creates a PVC; the cluster's storage provisioner supplies the backing volume.

---

## 8. Install the tools

You need:

- Git
- Python 3.12+
- Docker
- kubectl
- Helm 3
- KIND (Kubernetes in Docker), for local Kubernetes practice

Check installations:

```bash
git --version
python3 --version
docker --version
kubectl version --client
helm version
kind version
```

---

## 9. Run the application locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
DATABASE_PATH=./data/releases.db flask --app app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
$env:DATABASE_PATH="./data/releases.db"
flask --app app run --debug
```

---

## 10. Validate the Helm chart before deployment

Run these from the repository root:

```bash
# Check chart metadata, values and template structure.
helm lint ./helm/releaseboard

# Render the chart locally; this does not install resources in Kubernetes.
helm template releaseboard ./helm/releaseboard --debug

# See what changes when optional Ingress is enabled.
helm template releaseboard ./helm/releaseboard --set ingress.enabled=true

# Save rendered YAML so you can inspect the actual Kubernetes resources.
helm template releaseboard ./helm/releaseboard > rendered.yaml
```

**Expected learning:** look at the rendered Deployment and find the image, replica count, container port, probes, environment variables, security context and volume mounts. Then find where each value came from in `values.yaml`.

---

## 11. Deploy to a KIND cluster

If you do not already have a KIND cluster, create one:

```bash
kind create cluster --name helm
kubectl cluster-info --context kind-helm
```

Build the image and load it into KIND:

```bash
docker build -t releaseboard:1.0.0 .
kind load docker-image releaseboard:1.0.0 --name helm
```

Install the chart:

```bash
helm upgrade --install releaseboard ./helm/releaseboard \
  --set image.repository=releaseboard \
  --set image.tag=1.0.0 \
  --set image.pullPolicy=IfNotPresent
```

Check the resources:

```bash
helm list
helm status releaseboard
kubectl get deploy,pods,svc,pvc
kubectl describe pod -l app.kubernetes.io/instance=releaseboard
kubectl logs deploy/releaseboard
```

Open the dashboard through port forwarding:

```bash
kubectl port-forward svc/releaseboard 8080:80
```

Then visit [http://127.0.0.1:8080](http://127.0.0.1:8080).

Test the endpoints:

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/readyz
curl http://127.0.0.1:8080/metrics
```

---

## 12. Practice Helm upgrades, history, tests and rollback

```bash
# Change the environment shown by the dashboard.
helm upgrade releaseboard ./helm/releaseboard --set appConfig.environment=staging

# List saved release revisions.
helm history releaseboard

# Run the chart's test hook Pod.
helm test releaseboard

# Return to revision 1 (use the revision shown by helm history).
helm rollback releaseboard 1

# Remove the Helm release and its managed resources.
helm uninstall releaseboard
```

After an upgrade, run `helm status releaseboard` and `kubectl get pods` to inspect the result.

---

## 13. GitHub Actions — understand the CI workflow

File: `.github/workflows/helm-ci.yml`

When code is pushed to the configured branches or a pull request is opened, GitHub Actions:

1. Starts a fresh Ubuntu runner.
2. Checks out the repository.
3. Installs Helm.
4. Runs `helm lint ./helm/releaseboard`.
5. Runs `helm template ci-release ./helm/releaseboard --debug`.

This workflow checks the chart structure and rendering. **It does not build/push a Docker image, create a Kubernetes cluster, or deploy to production.** Those can be added as separate pipeline stages after the basic chart checks work.

To inspect a run, open the repository's **Actions** tab on GitHub.

---

## 14. Troubleshooting guide

| Problem | What to check |
|---|---|
| Pod is `ImagePullBackOff` | Image repository/tag, registry access, and whether the image was loaded into KIND |
| Pod is `CrashLoopBackOff` | `kubectl logs deploy/releaseboard` and `kubectl describe pod` |
| PVC is `Pending` | Run `kubectl get storageclass`; check whether the cluster has a default StorageClass |
| Service cannot reach Pod | Check Service selector, Pod labels, readiness status and container port |
| Port-forward fails | Check Service name/port using `kubectl get svc` |
| Helm template fails | Run `helm lint`; check YAML indentation and missing values |
| Helm test fails | Check Pod logs and whether the Service and health endpoint are reachable |
| Dashboard data disappears | Check that the PVC is bound and mounted at `/data`; verify the database path |

Useful diagnostic commands:

```bash
kubectl get all
kubectl get pvc
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl describe deployment releaseboard
kubectl logs deployment/releaseboard
helm lint ./helm/releaseboard
helm template releaseboard ./helm/releaseboard --debug
```

---

## 15. Important design limitations — read before enabling scaling

The learning configuration uses **SQLite with one ReadWriteOnce PVC and one replica**.

- Do not turn on HPA or increase replicas for this SQLite setup as if it were a production multi-replica service.
- Multiple Pods writing to one SQLite file is not a suitable horizontally scaled database architecture.
- For a real multi-replica application, migrate the data layer to PostgreSQL or another suitable external database, then configure backups, credentials, networking and monitoring.
- The default Secret is disabled. Provide a strong Flask secret securely before using a public or production deployment.
- The example Ingress hostname is not a real domain. Configure DNS, an Ingress controller and TLS before exposing a real service.
- NetworkPolicy needs a compatible CNI plugin. Enabling a policy without allowing the correct source namespaces can block application traffic.
- HPA needs metrics-server and sensible resource requests. It does not make a stateful application safe to scale by itself.

---

## 16. Your practical learning roadmap

Follow this order. Do not skip directly to EKS before understanding the local workflow.

- [ ] **Stage 1 — Python/Flask:** run the app, create a release, update status, delete a release; explain each route in `app.py`.
- [ ] **Stage 2 — Database:** find the SQLite file, explain `/data`, and understand why the database needs persistent storage.
- [ ] **Stage 3 — Docker:** build the image, run the container, inspect logs, explain each Dockerfile instruction and the non-root user.
- [ ] **Stage 4 — Kubernetes basics:** understand Pod, Deployment, Service, labels, selectors, probes, resources and volumes.
- [ ] **Stage 5 — Helm basics:** explain Chart.yaml, values.yaml, templates, helpers, rendering and releases.
- [ ] **Stage 6 — Helm operations:** lint, template, install, upgrade, history, test and rollback.
- [ ] **Stage 7 — Troubleshooting:** intentionally inspect a failed Pod, image pull issue, unbound PVC and incorrect Service selector in a safe local cluster.
- [ ] **Stage 8 — CI:** make a small chart change and confirm GitHub Actions runs lint and template checks.
- [ ] **Stage 9 — Production design:** understand why SQLite must be replaced before multi-replica deployment; then plan PostgreSQL, external secrets, ingress TLS and monitoring.
- [ ] **Stage 10 — AWS EKS:** only after the local KIND deployment is understood, map the same concepts to EKS, ECR, IAM, VPC, Load Balancer and AWS storage.

---

## 17. Interview practice — explain in your own words

1. What problem does ReleaseBoard solve?
2. What happens after you submit the Create Release form?
3. What is the difference between Flask and Gunicorn?
4. Why do we build a Docker image?
5. Why should the container run as a non-root user?
6. What is the difference between a Docker image and a container?
7. What does a Kubernetes Deployment manage?
8. Why does a Service need selectors and labels?
9. What is the difference between liveness and readiness probes?
10. What is a ConfigMap, and what belongs in it?
11. Why should a sensitive key be stored in a Secret?
12. What is the difference between PV, PVC and StorageClass?
13. What is a Helm chart compared with a Helm release?
14. What does `helm template` do?
15. What is the purpose of `_helpers.tpl`?
16. What happens during `helm upgrade` and `helm rollback`?
17. What does HPA need before it can scale Pods?
18. Why is the current SQLite setup limited to one replica?
19. What does the GitHub Actions workflow validate?
20. What would you change before calling this a production-ready system?

**Interview rule:** do not memorize only definitions. Open the relevant file, point to the exact configuration, and explain how the pieces work together.

---

## 18. Suggested study routine

For each stage:

1. Read the relevant section in this README.
2. Open the named source file and read its comments.
3. Run the command yourself.
4. Observe the output using `kubectl`, `docker` or `helm`.
5. Explain what happened in simple words without looking at the README.
6. If something fails, capture the exact error and troubleshoot it before moving forward.

**The objective is not just to make the project run. The objective is to understand why every file, command and Kubernetes resource exists.**
