# bgdestroyer.com: image background remover HTTP API / SaaS

A simple REST API in front of an ML model that removes backgrounds from images.

Credit to https://github.com/danielgatis/rembg for the library that
made this all very easy.

## Deploy to Cloud Run

```
PROJECT_ID=$(gcloud config get project)
gcloud builds submit --tag gcr.io/$PROJECT_ID/bgdestroyer
gcloud run deploy bg-remover --image=gcr.io/bgdestroyer/bgdestroyer-worker \
  --region=us-central1 --cpu=1 --memory=1Gi --max-instances=10 --allow-unauthenticated \
  --concurrency=1
```
