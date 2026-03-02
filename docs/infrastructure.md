# Infrastructure Overview

This document describes the MareAnalytica infrastructure that all services deploy into.

## Cluster

| Component | Details |
|-----------|---------|
| **Distribution** | k3s v1.34.4+k3s1 |
| **Control plane** | `liquidmetal` — 16 CPU, 16 GB RAM, 192.168.1.135 (TS: 100.112.68.53) |
| **Worker** | `liquidmetallabs` — 6 CPU, 64 GB RAM, 192.168.1.236 (TS: 100.117.222.119) |
| **Ingress controller** | nginx-ingress (in-cluster), MetalLB external IP `192.168.1.240` |
| **DNS** | Wildcard `*.mareanalytica.com` → 100.112.68.53 (Tailscale) / 192.168.1.240 (LAN) |
| **Storage** | `local-path` provisioner (default) |

## Networking

```
Internet / LAN
     │
     ▼
MetalLB (192.168.1.240)
     │
     ▼
nginx-ingress controller
     │
     ├── *.mareanalytica.com → various services
     │
     ▼
ClusterIP Services → Pods
```

All services are exposed via **nginx Ingress** with TLS certificates issued by **cert-manager**.

### Tailscale

Both k3s nodes and the build machine (`bigboii`) are on the Tailscale network. This allows:
- `kubectl` access from bigboii without VPN
- GitHub Actions runners (on `liquidmetallabs`) to push to the registry
- Remote access to all services via Tailscale IPs

## TLS / Certificates

| Issuer | Type | Usage |
|--------|------|-------|
| `mareanalytica-ca` | Self-signed CA (ClusterIssuer) | Internal services, registry |
| `letsencrypt-prod` | ACME (ClusterIssuer) | Public-facing services (if needed) |

All `*.mareanalytica.com` ingresses use `mareanalytica-ca` by default. Add this annotation to your Ingress:
```yaml
annotations:
  cert-manager.io/cluster-issuer: "mareanalytica-ca"
```

The CA certificate is distributed to k3s nodes via a DaemonSet (`k3s-registry-setup` in `kube-system`).

## Container Registry

| Field | Value |
|-------|-------|
| **Software** | Docker Distribution (registry:2) |
| **Namespace** | `registry` |
| **Internal URL** | `http://registry.registry.svc.cluster.local:5000` |
| **External URL** | `https://registry.mareanalytica.com` |
| **UI** | `https://registry-ui.mareanalytica.com` |
| **TLS** | cert-manager with `mareanalytica-ca` |

### Pushing images

Images are pushed during CI/CD by the ARC runner (Docker-in-Docker). The DinD sidecar trusts the registry CA cert mounted at `/etc/docker/certs.d/registry.mareanalytica.com/ca.crt`.

### Pulling images

k3s nodes pull images directly. They trust the registry via `/etc/rancher/k3s/registries.yaml`:
```yaml
configs:
  "registry.mareanalytica.com":
    tls:
      ca_file: "/etc/rancher/k3s/certs/mareanalytica-ca.crt"
```

## CI/CD — GitHub Actions

### GitHub App

| Field | Value |
|-------|-------|
| **Name** | OpenHands MareAnalytica |
| **App ID** | 2980569 |
| **Organization** | MareAnalytica |

### Self-hosted Runners (ARC)

Runners are managed by **Actions Runner Controller (ARC)** v0.13.1:

| Component | Namespace | Details |
|-----------|-----------|---------|
| ARC Controller | `arc-systems` | Manages runner lifecycle |
| Runner Scale Set | `arc-runners` | Label: `arc-runner-set` |

Runner pods run on `liquidmetallabs` (64 GB RAM) via `nodeSelector` to avoid competing with app workloads on `liquidmetal`.

Each runner pod has:
- **runner** container — GitHub Actions runner with JIT config
- **dind** container — Docker-in-Docker (privileged) with `--mtu=1400`
- **init-dind-externals** — init container that copies runner externals

Key resources in `arc-runners` namespace:
- `Secret/github-app-secret` — GitHub App PEM + App ID
- `Secret/runner-kubeconfig` — kubeconfig for deploy jobs
- `ConfigMap/registry-ca-cert` — CA cert for registry trust
- `ServiceAccount/arc-runner-deployer` — ClusterRole for kubectl apply

### Pipeline Flow

```
Push to main ──► build.yml ──► deploy.yml ──► dev
                    │               │
                    │               └── kubectl apply -k kube/overlays/dev
                    │               └── rollout restart
                    │               └── wait for rollout
                    │
                    └── docker build + push to registry.mareanalytica.com

Tag v* ─────► build.yml ──► deploy.yml ──► prod
```

### Workflow Files

| File | Type | Purpose |
|------|------|---------|
| `_build.yml` | Reusable | Build & push Docker images (copy as-is) |
| `_deploy.yml` | Reusable | Deploy via kustomize (copy as-is) |
| `dev-push.yml` | Caller | Push to main → build + deploy to dev (edit per project) |
| `dev-manual.yml` | Caller | Manual deploy of any branch to dev (edit per project) |
| `prod-tag.yml` | Caller | Tag v* → build + deploy to prod (edit per project) |

Each project gets two namespaces:
- `<project>-dev` — dev environment (push to main)
- `<project>` — production (tag v*)

## Node Allocation

| Node | Role | Workloads |
|------|------|-----------|
| `liquidmetal` | Control plane | App pods, databases, PVC-bound workloads |
| `liquidmetallabs` | Worker | CI/CD runners (via nodeSelector), overflow workloads |

Important: PVCs using `local-path` are node-affine. If a PVC is created on `liquidmetal`, the pod must schedule there.
