GCloud Install
https://cloud.google.com/sdk/docs/install#deb
GCloud reference
https://cloud.google.com/sdk/gcloud/reference

---------------------------------------------------------------------------------------------------------------------------------
# enable apis
gcloud services enable cloudfunctions.googleapis.com \
cloudbuild.googleapis.com \
cloudscheduler.googleapis.com \
documentai.googleapis.com


# AI SETUP AND TRAINING
# setup document ai
https://cloud.google.com/document-ai/docs/overview
# REFER TO THIS RESOURCE FOR HOW TO CREATE LABELS FOR DATA, TRAIN, BUILD, AND DEPLOY THE AI

# training the AI requirements
# create a bucket for training data
gcloud storage buckets create gs://jerry_v1_training_data

# upload your training data from your local machine to the bucket
gcloud storage cp /mnt/c/Users/AriCerrahyan/Downloads/order-summary-telus-training/* gs://jerry_v1_training_data

# attach document ai service account to the storage bucket with the appropriate role
gcloud storage buckets add-iam-policy-binding gs://jerry_v1_training_data \
--member="serviceAccount:service-$(gcloud projects describe $(gcloud config get project) --format="value(projectNumber)")@gcp-sa-prod-dai-core.iam.gserviceaccount.com" \
--role="roles/storage.objectViewer"
# notes
# when enabling the document ai api a service account is created in the form of
# service-{project number}@gcp-sa-prod-dai-core.iam.gserviceaccount.com
# project number can be retreived through / gcloud projects describe $(gcloud config get project) --format="value(projectNumber)"
# FROM HERE YOU CAN PROCEED TO LABELING THE DATA, TRAIN, BUILD, AND DEPLOY THE AI

# SETUP CRON JOB FOR THE AI / SCRIPT
# create service account the schedular will use to make a function call
gcloud iam service-accounts create jerry-v1-sa \
--description="Service account for jerry_v1" \
--display-name="jerry_v1_sa"

# create the function
gcloud functions deploy print_hello \
--runtime python312 \
--trigger-http \
--entry-point hello \
--region=us-central1 \
--no-allow-unauthenticated

# allow the SA to invoke the function
gcloud functions add-invoker-policy-binding print_hello \
--region=us-central1 \
--member=serviceAccount:jerry-v1-sa@ari-dev-463216.iam.gserviceaccount.com

# create the scheduler and attach the SA to it
gcloud scheduler jobs create http hello_scheduler_job \
--schedule "* * * * *" \
--uri https://us-central1-ari-dev-463216.cloudfunctions.net/print_hello \
--http-method=GET \
--oidc-service-account-email=jerry-v1-sa@ari-dev-463216.iam.gserviceaccount.com \
--location=us-central1 \
--time-zone="America/Toronto"
---------------------------------------------------------------------------------------------------------------------------------














questions...
- which project is this going to be hosted in?
    . unknown for production, development on any project is fine
- how will the bucket be organized?
    . possible solution
        - pickup, processing, succeeded, failed directories for each stage of file processing
- can i move a trained model from one project to another or even just copy it??? - this is for me to figure out


requirements...
- all business related data required from the pdf files
- a db schema
 . cpms ID
 . order ID
just dump the results into the db as long as the minimum extracted data requirements are met


services required
- bucket
- db
- functions
- scheduler
- document AI



scheduler triggers function to proccess all pdf files in bucket
each file calls document ai to extract the data
move file from a directory to a processed directory
using the link of the file and the data extracted - store it in the db






