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

### 2. Find & replace `mcp-router`

Replace all occurrences of `mcp-router` with your project name (lowercase, hyphen-separated):

```bash
# macOS
find . -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) \
  -exec sed -i '' 's/mcp-router/my-new-service/g' {} +

# Linux
find . -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) \
  -exec sed -i 's/mcp-router/my-new-service/g' {} +
```

### 3. Add your Dockerfiles

Add one or more `Dockerfile`s for your service components. The directory structure is up to you — organize it however makes sense for your project.

### 4. Update the workflow image lists

Edit these files and update the `images` JSON array to match your Dockerfiles:
- `.github/workflows/dev-push.yml`
- `.github/workflows/prod-tag.yml`
- `.github/workflows/dev-manual.yml`

Example for a single-image project:
```yaml
images: >-
  [
    { "name": "my-new-service", "context": ".", "dockerfile": "./Dockerfile" }
  ]
```

### 5. Update kube manifests

Add your Kubernetes `.yaml` files to `kube/base/` and list them in `kube/base/kustomization.yaml`. The template includes some example manifests to get you started — edit or replace them as needed.

### 6. Open a PR to main

```bash
git checkout -b initial-setup
git add -A
git commit -m "Initial service setup"
git push origin initial-setup
```

Open a pull request on GitHub. Once reviewed and merged to `main`, the CI/CD pipeline runs automatically:
1. **Build** — Docker images are built and pushed to `registry.mareanalytica.com`
2. **Deploy** — Kustomize applies to `my-new-service-dev` namespace
3. **Rollout** — Deployments are restarted and verified

Your service will be available at: `https://my-new-service-dev.mareanalytica.com`

### 7. Deploy a branch to dev (manual)

You can deploy any branch to dev without merging by using the **Deploy Branch → Dev** workflow:

1. Go to the **Actions** tab on GitHub
2. Select **Deploy Branch → Dev** from the workflow list
3. Click **Run workflow** and pick the branch you want to deploy

This builds the images from that branch and deploys them to the dev environment, letting you test changes before opening a PR.

### 8. Deploy to production

```bash
git tag v1.0.0
git push origin v1.0.0
```

Available at: `https://my-new-service.mareanalytica.com`

## What's Included

```
.github/workflows/
  _build.yml             # Reusable: build + push Docker images (DO NOT EDIT)
  _deploy.yml            # Reusable: deploy via kustomize (DO NOT EDIT)
  dev-push.yml           # Push main → build + deploy to dev (edit per project)
  dev-manual.yml         # Manual deploy any branch to dev (edit per project)
  prod-tag.yml           # Tag v* → build + deploy to prod (edit per project)

kube/
  base/                  # Your Kubernetes .yaml manifests go here
    kustomization.yaml
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
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  PR → main   │────►│  Build imgs  │────►│  Deploy to dev   │
│  (merged)    │     │  (DinD on    │     │  (kubectl apply  │
│              │     │   ARC runner)│     │   -k overlays/   │
┌──────────────┐     │              │     │   dev)           │
│  Tag v*      │────►│              │────►│  Deploy to prod  │
└──────────────┘     └──────────────┘     └──────────────────┘
                           │
┌──────────────┐           │
│  Manual:     │───────────┘
│  Deploy      │
│  Branch→Dev  │
└──────────────┘     ┌─────────────┐
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
6. Open a PR — once merged, it auto-builds and deploys

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
