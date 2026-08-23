# How this deploys

CI builds and pushes an image. **ArgoCD deploys.** CI holds no cluster
credentials — that is the whole point of the split.

- push to `main`  → `.github/workflows/dev-push.yml` builds both images into
  `harbor.dev.mareanalytica.com/mare-dev/` on the in-cluster runners
- tag `v*`        → `prod-tag.yml`, same but for a release build
- ArgoCD watches `MareAnalytica/gitops` → `apps/dev/mcp-router.yaml`, which
  points back at this repo's `kube/overlays/dev`

So the manifests still live here; only the *act* of applying them moved.

## What changed and why
This repo used to run `kubectl apply` from a runner inside the cluster
(`_deploy.yml`, now deleted). That works, but it means CI can write to the
cluster, and there is no single place that describes what is actually deployed.
Under the Jove model — which this estate is being rebuilt to match — the cluster
pulls its own desired state and nothing pushes into it.

## Target cluster
The **Liquid Metal** dev cluster (`liquidmetal-dev` control plane +
`liquidscale-dev`), not the aflabox clusters.

## Still to do before this runs green
- the images have never been built into Harbor; the old
  `registry.mareanalytica.com` died with the previous cluster
- `mcp-router-dev`'s database needs restoring from the backup on Jove `io`
  (`mcprouter.zst` — `pg_restore` as its own role, not `postgres`)
