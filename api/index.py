from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import numpy as np

app = FastAPI()

# Keep your working CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.post("/api")
async def analytics(request: Request):
    body = await request.json()
    
    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        data = json.load(f)

    target_regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}

    for region in target_regions:
        region_records = [
            r for r in data 
            if str(r.get("region", "")).lower() == region.lower()
        ]

        if not region_records:
            continue

        latencies = [float(r.get("latency_ms", 0)) for r in region_records]
        uptimes = [float(r.get("uptime", 0)) for r in region_records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold))
        }

    # THE CRITICAL CHANGE: Wrap the output in a "regions" key
    return {"regions": result}
