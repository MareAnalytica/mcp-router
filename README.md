# MareAnalytica Service Template

Use this template to create a new service that auto-deploys to the MareAnalytica k3s cluster.

## Quick Start

### 1. Create a repo from this template

Click **"Use this template"** on GitHub, or:
```bash
gh repo create MareAnalytica/my-new-service --template MareAnalytica/service-template --private
git clone git@github.com:MareAnalytica/my-new-service.git
cd my-new-service
```

### 2. Find & replace `MY_PROJECT`

Replace all occurrences of `MY_PROJECT` with your project name (lowercase, hyphen-separated):

```bash
# macOS
find . -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) \
  -exec sed -i '' 's/MY_PROJECT/my-new-service/g' {} +

# Linux
find . -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) \
  -exec sed -i 's/MY_PROJECT/my-new-service/g' {} +
```

### 3. Add your Dockerfiles

Create your service directories with Dockerfiles:
```
my-new-service/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/
```

### 4. Update the workflow image lists

Edit these files and update the `images` JSON array:
- `.github/workflows/ci-dev.yml`
- `.github/workflows/release-prod.yml`
- `.github/workflows/deploy-branch-dev.yml`

Example for a single-service project:
```yaml
images: >-
  [
    { "name": "my-new-service", "context": ".", "dockerfile": "./Dockerfile" }
  ]
```

### 5. Update kube manifests

- Edit `kube/base/secrets.yaml` with your DB credentials
- Edit `kube/base/backend.yaml` with your backend config (ports, env vars, health check)
- Edit `kube/base/frontend.yaml` with your frontend config and Ingress host
- Remove `kube/base/postgres.yaml` if you don't need a database
- Update `kube/base/kustomization.yaml` to list your manifest files

### 6. Push to main

```bash
git add -A
git commit -m "Initial service setup"
git push origin main
```

This triggers the CI/CD pipeline:
1. **Build** — Docker images are built and pushed to `registry.mareanalytica.com`
2. **Deploy** — Kustomize applies to `my-new-service-dev` namespace
3. **Rollout** — Deployments are restarted and verified

Your service will be available at: `https://my-new-service-dev.mareanalytica.com`

### 7. Deploy to production

```bash
git tag v1.0.0
git push origin v1.0.0
```

Available at: `https://my-new-service.mareanalytica.com`

## What's Included

```
.github/workflows/
  build.yml              # Reusable: build + push Docker images (DO NOT EDIT)
  deploy.yml             # Reusable: deploy via kustomize (DO NOT EDIT)
  ci-dev.yml             # Push main → build + deploy to dev (edit per project)
  release-prod.yml       # Tag v* → build + deploy to prod (edit per project)
  deploy-branch-dev.yml  # Manual deploy any branch to dev (edit per project)

kube/
  base/                  # Base Kubernetes manifests
    kustomization.yaml
    namespace.yaml
    secrets.yaml
    postgres.yaml        # Optional: remove if no DB needed
    backend.yaml
    frontend.yaml
  overlays/
    dev/kustomization.yaml   # Dev overrides (namespace, hosts, resources)
    prod/kustomization.yaml  # Prod overrides

docs/
  infrastructure.md      # Cluster, networking, registry, CI/CD details
  monitoring.md          # Prometheus, Grafana, Loki, alerting guide

.openhands/
  microagents/
    infrastructure.md    # OpenHands AI agent context
```

## Pipeline Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Push main  │────►│  Build imgs  │────►│  Deploy to dev   │
└─────────────┘     │  (DinD on    │     │  (kubectl apply  │
                    │   ARC runner)│     │   -k overlays/   │
┌─────────────┐     │              │     │   dev)           │
│  Tag v*     │────►│              │────►│  Deploy to prod  │
└─────────────┘     └──────────────┘     └──────────────────┘
                           │
                    ┌──────┴──────┐
                    │  registry.  │
                    │  mare       │
                    │  analytica  │
                    │  .com       │
                    └─────────────┘
```

## Adding a New Service Component

1. Create a directory with a `Dockerfile`
2. Add it to the `images` array in the caller workflows
3. Add a `kube/base/<service>.yaml` with Deployment + Service
4. Add it to `kube/base/kustomization.yaml`
5. Add the deployment name to the `deployments` list in the caller workflows
6. Push — it auto-builds and deploys

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build: "Docker not ready" | DinD sidecar slow to start. Usually resolves on retry. |
| Build: SSL cert error | CA cert not mounted in runner. Check `registry-ca-cert` ConfigMap in `arc-runners`. |
| Build: Stuck downloading layers | MTU issue. Verify `--mtu=1400` in DinD args. |
| Deploy: "kubectl not found" | The `deploy.yml` workflow installs it automatically. |
| Deploy: Rollout timeout | Increase `rollout_timeout` in caller workflow. Check pod events: `kubectl get events -n <ns>`. |
| Deploy: Pod stuck Pending | Check node resources: `kubectl top nodes`. May need to reduce resource requests. |
| Images not updating | Ensure `imagePullPolicy: Always` in your Deployment spec. |

## Documentation

- [Infrastructure details](docs/infrastructure.md) — cluster, networking, registry, CI/CD
- [Monitoring & observability](docs/monitoring.md) — Prometheus, Grafana, Loki, alerts
