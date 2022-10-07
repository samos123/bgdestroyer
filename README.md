# bgdestroyer.com: image background remover HTTP API / SaaS

Automatically remove the background from your image with the power of AI.
Available for free through SaaS at bgdestroyer.com and available as open source
to run it yourself.

This repo provides the REST API that's consumed by the the frontend. The REST
API for SaaS version is deployed on Google Cloud Run, however you can deploy
it somewhere else by simply deploying the docker container.

The source for the frontend used by bgdestroyer.com is available here:
https://github.com/samos123/bgdestroyer-ui

Credit to https://github.com/danielgatis/rembg for the library to remove the
background image which made this all very easy.

## Test it locally

You will first need to download u2net model from here: https://drive.google.com/uc?id=1tCU5MM1LhRgGou5OpmpjBQbSrYIUoYab
and name the file `u2net.onnx`

Now you can bring up a development environment by running:
```
docker-compose up
```

## Deploy to Cloud Run

```
PROJECT_ID=$(gcloud config get project)
gcloud builds submit --tag gcr.io/$PROJECT_ID/bgdestroyer
gcloud run deploy bg-remover --image=gcr.io/bgdestroyer/bgdestroyer-worker \
  --region=us-central1 --cpu=1 --memory=1Gi --max-instances=10 --allow-unauthenticated \
  --concurrency=1
```
