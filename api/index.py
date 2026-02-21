from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import numpy as np

app = FastAPI()

# 1. THE PROPER CORS FIX
# This handles the "Preflight" (OPTIONS) requests that are likely failing your grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api")
async def analytics(request: Request):
    # Load the body data
    body = await request.json()
    
    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        data = json.load(f)

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    # 2. THE UPTIME LABEL FINDER
    # Let's look at the first row to see what 'uptime' is actually called
    sample = data[0] if data else {}
    # This looks for any key that starts with 'up' (like 'uptime', 'uptime_pct', etc.)
    up_key = next((k for k in sample if k.lower().startswith('up')), 'uptime')
    # Do the same for latency just to be safe
    lat_key = next((k for k in sample if 'lat' in k.lower()), 'latency_ms')

    result = {}

    for region in regions:
        region_records = [
            r for r in data
            if str(r.get("region", "")).lower() == region.lower()
        ]

        if not region_records:
            continue

        # Use our detected keys here
        latencies = [float(r.get(lat_key, 0)) for r in region_records]
        uptimes = [float(r.get(up_key, 0)) for r in region_records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold))
        }

    return result
