# transcript-generator
#Setup->

```
pip install -r "requirements.txt"
```

# Running the API->

```
uvicorn main:app --reload
```
# Run in separate terminal->
```
rq worker whisper
```

# API Endpoints->
## /transcribe ->
### In the request body send
```
{
url : "Your mp3 cloudinary link."
}
```
## Response ->

```
{
job_id : "Job Id for your request",
status : "Status of the Job (queued or rejected)."
}
```

## /status ->
### In the request body send
```
{
job_id : "Your job_id that you got from earlier."
}
```
## Response ->

```
{
job_id: "Your job_id",
status: "Job Id Status",
result: "Result or transcription of the mp3 file if the job status is compelete."
}
```
### For the /status endpoint create request periodically until you get a job_status of finished or other error.

