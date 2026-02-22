from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import statistics
import math

app = FastAPI()

# 1. FORCE CORS - This handles the 'Access-Control-Allow-Origin' error
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.post("/api")
async def analytics(request: Request):
    payload = await request.json()
    
    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        telemetry_data = json.load(f)

    results = {}
    target_regions = payload.get("regions", [])
    threshold_ms = payload.get("threshold_ms", 180)

    for region in target_regions:
        # Filtering (Case-insensitive)
        region_data = [
            r for r in telemetry_data 
            if str(r.get("region", "")).lower() == region.lower()
        ]
        
        if not region_data:
            continue
        
        # Use .get() to avoid KeyErrors. Most JSONs use "uptime" or "uptime_pct"
        # We check for "uptime" based on your previous logs
        latencies = [float(r.get("latency_ms", 0)) for r in region_data]
        uptimes = [float(r.get("uptime", 0)) for r in region_data]
        
        # MATH SECTION
        avg_latency = statistics.mean(latencies)
        
        # P95 Calculation - Using the specific formula you provided
        sorted_l = sorted(latencies)
        n = len(sorted_l)
        idx = 0.95 * (n - 1)
        low = int(idx)
        high = low + 1
        if high < n:
            p95 = sorted_l[low] + (idx - low) * (sorted_l[high] - sorted_l[low])
        else:
            p95 = sorted_l[low]
            
        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > threshold_ms)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95, 2),
            "avg_uptime": round(avg_uptime, 3), # This MUST be 3 to get 98.226
            "breaches": breaches
        }
    
    return {"regions": results}
