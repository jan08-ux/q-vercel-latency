from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import numpy as np

app = FastAPI()

# THE MAGIC FIX: This handles CORS and OPTIONS pre-flight checks automatically.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data once when the app starts
BASE_DIR = pathlib.Path(__file__).parent
file_path = BASE_DIR / "q-vercel-latency.json"

with open(file_path) as f:
    data = json.load(f)

@app.post("/api")
async def analytics(request: Request):
    body = await request.json()
    
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        # Filter the data for the requested region
        region_records = [
            r for r in data
            if str(r.get("region", "")).lower() == region.lower()
        ]

        if not region_records:
            continue

        # Extract the numbers using the keys that worked in your terminal
        latencies = [float(r.get("latency_ms", 0)) for r in region_records]
        uptimes = [float(r.get("uptime", 0)) for r in region_records]

        # Calculate and round the metrics
        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold))
        }

    return result
