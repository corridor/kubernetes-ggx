PROJECT_ID="ggx-project"
REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="ggx-cluster"

# Permissions needed for a user to run this script:
# At a minimum, the user should have:
# - roles/resourcemanager.projectCreator on the parent org/folder
#   so they can create the project.
# - roles/serviceusage.serviceUsageAdmin on the project
#   so they can enable the required Google APIs.
# - roles/container.admin on the project
#   so they can create and manage the GKE cluster.
# - roles/compute.admin on the project
#   so they can create the cluster's underlying compute resources.
# - roles/compute.networkAdmin on the project
#   so they can create the NAT router, subnet, and other VPC resources.
# - roles/file.editor on the project
#   so they can create and inspect the Filestore instance.
# - roles/iam.serviceAccountUser on the node service account
#   used by GKE nodes. If using the default Compute Engine service account,
#   grant this on PROJECT_NUMBER-compute@developer.gserviceaccount.com.

# Create project
if gcloud projects list | grep "$PROJECT_ID"; then
  echo "Project $PROJECT_ID already exists"
else
  gcloud projects create "$PROJECT_ID" --name="$PROJECT_ID"
  echo "Created project $PROJECT_ID"
fi

# Enable required services
gcloud services enable aiplatform.googleapis.com --project="$PROJECT_ID"
gcloud services enable monitoring.googleapis.com --project="$PROJECT_ID"
gcloud services enable serviceusage.googleapis.com --project="$PROJECT_ID"
gcloud services enable generativelanguage.googleapis.com --project="$PROJECT_ID"
gcloud services enable cloudaicompanion.googleapis.com --project="$PROJECT_ID"
gcloud services enable discoveryengine.googleapis.com --project="$PROJECT_ID"
gcloud services enable cloudbilling.googleapis.com --project="$PROJECT_ID"
gcloud services enable dialogflow.googleapis.com --project="$PROJECT_ID"
gcloud services enable file.googleapis.com --project="$PROJECT_ID"

# Create GKE Cluster, this takes more than 5 minutes depends on machine availability in the zone
gcloud container clusters create "$CLUSTER_NAME" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type=e2-medium \
  --num-nodes=1 \
  --enable-autoscaling --min-nodes=1 --max-nodes=5 \
  --enable-private-nodes \
  --enable-ip-alias \
  --enable-network-policy \
  --workload-pool="$PROJECT_ID.svc.id.goog" \
  --release-channel=regular \
  --gateway-api=standard \
  --enable-shielded-nodes \
  --enable-autoupgrade \
  --enable-autorepair \
  --labels=name="$CLUSTER_NAME"

# Fetch cluster credentials
gcloud container clusters get-credentials "$CLUSTER_NAME" \
  --zone="$ZONE" \
  --project="$PROJECT_ID"

# Setup NAT since this is a private cluster (so we can fetch docker containers the GAR)
gcloud compute routers create nat-router \
  --network=default \
  --region=$REGION \
  --project=$PROJECT_ID
gcloud compute routers nats create nat-config \
  --router=nat-router \
  --router-region=$REGION \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips \
  --project=$PROJECT_ID

# Create the Filestore NFS server used by the cluster.
# This uses the default VPC so the private GKE nodes can mount it.
gcloud filestore instances create "ggx-filestore" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --tier="BASIC_HDD" \
  --file-share=name="ggx",capacity="1TiB" \
  --network=name="default"

NFS_SERVER_IP=$(gcloud filestore instances describe "ggx-filestore" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --format='value(networks[0].ipAddresses[0])')

# Setup the NFS mount using the Filestore instance created above (Called "nfs-client").
# This is an one-time activity at a cluster level
helm install nfs-client nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --namespace nfs-provisioner --create-namespace --set nfs.server="$NFS_SERVER_IP" \
  --set nfs.path=/ggx/ggx-k8s-nfs --set storageClass.name=nfs-client \
  --set storageClass.reclaimPolicy=Retain --set storageClass.mountOptions[0]=vers=4.1
