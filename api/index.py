from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import numpy as np

app = FastAPI()

# Standard FastAPI CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicitly handle OPTIONS requests (The 'Pre-flight' check)
@app.options("/api")
async def options_handler():
    return Response(status_code=200)

@app.post("/api")
async def analytics(request: Request):
    try:
        body = await request.json()
    except:
        return {"error": "Invalid JSON"}

    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        data = json.load(f)

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)
    result = {}

    for region in regions:
        # Match region case-insensitively
        region_records = [
            r for r in data 
            if str(r.get("region", "")).lower() == region.lower()
        ]

        if not region_records:
            continue

        # Based on your working terminal output:
        latencies = [float(r.get("latency_ms", 0)) for r in region_records]
        uptimes = [float(r.get("uptime", 0)) for r in region_records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold))
        }

    return result
