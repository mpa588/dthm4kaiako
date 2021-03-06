#!/bin/bash

source ./infrastructure/dev-deploy/load-dev-deploy-config-envs.sh

./dev start
./dev update

# Generate production static files
sudo rm -r ./dthm4kaiako/build/
sudo rm -r ./dthm4kaiako/staticfiles/
./dev static_prod
./dev collect_static

# Create authentic context cards
./dev load_achievement_objectives
./dev create_cards

# Install Google Cloud SDK
./infrastructure/install_google_cloud_sdk.sh

# Decrypt secret files archive that contain credentials.
./infrastructure/dev-deploy/decrypt-dev-secrets.sh

# Load environment variables.
source ./dthm4kaiako/load-dev-envs.sh

# Authenticate with gcloud tool using the decrypted service account credentials.
# See: https://cloud.google.com/sdk/gcloud/reference/auth/activate-service-account
gcloud auth activate-service-account --key-file ./dthm4kaiako/${GOOGLE_APPLICATION_CREDENTIALS}

# Create empty SSH keys with an empty passphrase, for Google Cloud SDK to
# copy files to a VM for building the Docker image.
# Only required for deploying to Google App Engine flexible environment.
# See: https://cloud.google.com/solutions/continuous-delivery-with-travis-ci#continuous_deployment_on_app_engine_flexible_environment_instances
ssh-keygen -q -N "" -f ~/.ssh/google_compute_engine

# Publish static files.
#
# This copies the generated static files from tests to the Google Storage
# Bucket.
# See: https://cloud.google.com/python/django/flexible-environment#deploy_the_app_to_the_app_engine_flexible_environment
gsutil -m rsync -R ./dthm4kaiako/staticfiles/ gs://dthm4kaiako-dev.appspot.com/static/
