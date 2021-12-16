#!/usr/bin/env bash

source .env

gcloud builds submit --tag $IMAGE
gcloud run deploy bg-remover --region us-central1 --image $IMAGE --cpu=2 --memory=2Gi
