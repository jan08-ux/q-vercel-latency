from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import numpy as np
import pathlib

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load JSON file
BASE_DIR = pathlib.Path(__file__).parent
file_path = BASE_DIR / "q-vercel-latency.json"

with open(file_path) as f:
    data = json.load(f)


@app.post("/api/analytics")
async def analytics(body: dict):

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    result = {}

    for region in regions:
        region_data = [r for r in data if r["region"] == region]

        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime"] for r in region_data]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return JSONResponse(result)
 
