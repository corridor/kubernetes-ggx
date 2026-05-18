# kubernetes-ggx

Kubernetes manifests for deploying GenGuardX with Kustomize.

## Quickstart

1. Get the docker credentials from the Corridor Team - Contact <support@corridorplatforms.com>
2. Create a kubernetes secret with the docker credentials
3. Deploy the services (Note: For more customized setups, check the Configurations section below)
4. Verify the rollout

```bash
# 1. Copy the provided docker credentials json file to /tmp/corridor-registry-key.json (or a preferred path)

# 2. Create a kubernetes secret with the docker credentials
kubectl create secret docker-registry corridor-registry-secret \
  --docker-server=us-central1-docker.pkg.dev \
  --docker-username=_json_key \
  --docker-password="$(cat /tmp/corridor-registry-key.json)" \
  --namespace ggx

# 3. Deploy the services (NOTE: Use --dry-run=server for safety)
kubectl apply -k overlays/example

# 4. Verify rollout
kubectl get pods -n ggx
kubectl get svc -n ggx
kubectl get ingress -n ggx
```

## Architecture

The deployment architecture is based on the existing Corridor GenGuardX setup:

- `corridor-app`: Primary API and Web application which serves the GGX platform
- `corridor-worker`: Background worker process for heavy execution tasks
- `corridor-jupyter`: Jupyter/JupyterHub-facing service for ad-hoc analytics
- Shared persistent volumes for data, uploads, notebooks, Jupyter state, and backups
- A single ingress routing `/` to the app and `/jupyter` to jupyter-service

## Cloud Compatibility

This repo is cloud agnostic.

It can be used on any Kubernetes cluster, including managed Kubernetes offerings such as GKE, EKS, AKS, Openshift, etc.

## Layout

```text
base/               Reusable application manifests
overlays/example/   Minimal deployable overlay with placeholder configuration
```

It is possible to host multiple instances of GenGuardX - for example: `overlays/prod`, `overlays/staging`, `overlays/dev`. Or `overlays/team1` and `/overlays/team2`

## Configure

Feel free to configure the kubernetes setup based on your needs. Some common configurations are:

- By default the `kustomization.yaml` uses the `latest` tag. To use a older version of Corridor GenGaurdX,
  set the docker image tag in `overlays/example/kustomization.yaml` > `newTag` variable.
- Set the public hostname based on your egress domain name in
  `overlays/example/kustomization.yaml`
- Set database and application-specific settings in
  `overlays/example/configs/api_config.py`
- If your cluster uses a different RWX storage class, update the PVC patches in
  `overlays/example/kustomization.yaml`.
- Configure TLS secret keys etc in `base/ingress.yaml`
- Configure other nginx configs like gzip/timeout etc. in `base/ingress.yaml`
- Change Memory requests and limits in the respective `base/*.yaml` files for that service.

## Recommended Cluster Configuration

The following configuration is a good starting point for managed Kubernetes clusters.

| Provider | Cluster type | Region / Zone | Initial nodes | Autoscaling | Node size | Disk | Notes |
|---|---|---|---|---|---|---|---|
| GKE | Standard | zonal (e.g. `us-central1-f`) | 1 | min 1, max 3 | `e2-standard-8` | 100 GB | Enable IP aliasing; use approved infra VPC/subnet |
| EKS | Standard | one availability zone or multi-AZ | 1 | min 1, max 3 | `m5.xlarge` or similar | 100 GB | Attach to approved VPC/subnet; use AWS VPC CNI or Cilium |
| AKS | Standard | one region | 1 | min 1, max 3 | `Standard_D8s_v3` | 100 GB | Use Azure CNI and approved virtual network |

### Why this configuration

- A single node is sufficient for typical POC usage.
- A maximum of 3 nodes gives headroom for blue/green-style upgrades or temporary capacity spikes.
- A 100 GB node disk supports application storage needs.
- Choose a machine type with 8 vCPUs and around 32 GB RAM for balanced performance.

## FAQs

**My pod is showing `ImagePullBackOff`**

If your pod events show `ImagePullBackOff` or registry authorization errors -> The
image authentication is likely the culprit. Double check if the correct docker credentials
are added to the kubernetes secret

**App is taking a long time to start**

The app deployment runs a database migration in an init container before the main API starts.
This can be decoupled to reduce restart time.
