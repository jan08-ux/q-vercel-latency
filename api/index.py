from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import numpy as np

app = FastAPI()

# 1. THE SECRET HANDSHAKE (CORS Middleware)
# This handles the pre-check "knocks" automatically for you.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api")
async def analytics(request: Request):
    # Get the request data
    body = await request.json()
    
    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        data = json.load(f)

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        # Filter data for the region (case-insensitive)
        region_records = [
            r for r in data
            if str(r.get("region", "")).lower() == region.lower()
        ]

        if not region_records:
            continue

        # Extract values (using the keys that worked in your last run)
        latencies = [float(r.get("latency_ms", 0)) for r in region_records]
        uptimes = [float(r.get("uptime", 0)) for r in region_records]

        # Calculate metrics
        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold))
        }

    return result
