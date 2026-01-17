import requests
import tempfile
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from redis import Redis
from rq import Queue, Worker
from worker import transcribe_job  
from rq.job import Job
from redis.exceptions import RedisError

app = FastAPI()

redis_conn = Redis(host="localhost", port=6379)
queue = Queue("whisper", connection=redis_conn)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
def rate_lmt_handler(request: Request, exc):
    raise HTTPException(status_code=429, detail="Rate limit exceeded.")

def download_audio(url, output_path):
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


@app.get("/")
@limiter.limit("10/minute")
def transcribe_audio(request: Request):
    return {"message":"Server is Up"}

@app.get("/transcribe")
@limiter.limit("10/minute")
def transcribe_audio(request: Request,url: str):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            download_audio(url, tmp.name)

            job = queue.enqueue(
                transcribe_job,
                tmp.name,
                job_timeout=300,
                result_ttl=100,
            )

        return {
            "job_id": job.id,
            "status": "queued"
        }

    except requests.exceptions.RequestException:
        raise HTTPException(status_code=400, detail="Failed to download audio")

@app.get("/status")
def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)

        return {
            "job_id": job.id,
            "status": job.get_status(), 
            "result": job.result if job.is_finished else None
            
        }

    except RedisError:
        raise HTTPException(status_code=500, detail="Redis connection error")

    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")