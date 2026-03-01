# Infrastructure Context for OpenHands

## Cluster
- **k3s** v1.34.4+k3s1 on 2 nodes: `liquidmetal` (control-plane, 16 CPU, 16 GB) and `liquidmetallabs` (worker, 6 CPU, 64 GB)
- **Ingress**: nginx-ingress with MetalLB at `192.168.1.240`
- **DNS**: Wildcard `*.mareanalytica.com` → cluster
- **TLS**: cert-manager with `mareanalytica-ca` ClusterIssuer (self-signed CA)
- **Storage**: `local-path` provisioner (default, node-affine)

## Container Registry
- `registry.mareanalytica.com` — Docker Distribution (registry:2) with TLS
- UI at `registry-ui.mareanalytica.com`
- In-cluster: `http://registry.registry.svc.cluster.local:5000`

## CI/CD
- **GitHub Actions** with self-hosted **ARC** runners on `liquidmetallabs`
- Runner label: `arc-runner-set`
- Docker-in-Docker with `--mtu=1400` and registry CA cert
- Pipeline: push main → build → deploy to dev | tag v* → build → deploy to prod
- Deploy via `kubectl apply -k kube/overlays/<env>`

## Monitoring
- **Prometheus** at `prometheus.mareanalytica.com`
- **Grafana** at `grafana.mareanalytica.com`
- **Alertmanager** at `alertmanager.mareanalytica.com`
- **Loki** for log aggregation (query via Grafana)
- **Headlamp** at `headlamp.mareanalytica.com`

## Conventions
- Image names: `registry.mareanalytica.com/<project>-<component>:latest`
- Dev namespace: `<project>-dev`, prod namespace: `<project>`
- Dev URL: `<project>-dev.mareanalytica.com`, prod URL: `<project>.mareanalytica.com`
- All deployments use `imagePullPolicy: Always`
- Resources: set both `requests` and `limits`; keep requests low for dev
- Dockerfiles should be slim/alpine-based where possible

## Build machine
- `bigboii` (x86_64 Linux) — has Docker, kubectl, Tailscale access to cluster
