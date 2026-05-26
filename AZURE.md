REGION="westus2"
CLUSTER_NAME="ggx-cluster"

# Permissions needed for a user to run this script:
# In practice, run this as an Owner or Contributor on the subscription or
# resource group, with permission to create role assignments if your org
# requires them for managed identities.
# At a minimum, the identity should be able to create and manage:
# - Resource groups
# - AKS clusters and node pools
# - Managed identities used by AKS
# - Load balancer, VNet, subnet, and public IP resources created by AKS
# - Storage resources created by the Azure Files CSI driver

# Prerequisites:
# - az CLI installed and logged in to the target subscription
# - kubectl installed

# Create the resource group.
az group create \
  --name "${CLUSTER_NAME}-rg" \
  --location "$REGION"

# Create the AKS cluster.
# This keeps the command readable and uses Azure-managed networking defaults
# instead of asking for a custom VNet up front.
az aks create \
  --resource-group "${CLUSTER_NAME}-rg" \
  --name "$CLUSTER_NAME" \
  --location "$REGION" \
  --node-count 1 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5 \
  --node-vm-size Standard_D8s_v3 \
  --node-osdisk-size 100 \
  --network-plugin azure \
  --enable-managed-identity \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --generate-ssh-keys

# Fetch cluster credentials.
az aks get-credentials \
  --resource-group "$${CLUSTER_NAME}-rg" \
  --name "$CLUSTER_NAME" \
  --overwrite-existing

# Make sure the Azure Files CSI driver is enabled.
az aks update \
  --resource-group "$${CLUSTER_NAME}-rg" \
  --name "$CLUSTER_NAME" \
  --enable-file-driver
