from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load data
current_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(current_dir, 'q-vercel-latency.json')

with open(file_path, 'r') as f:
    telemetry_data = json.load(f)

@app.post("/api")
async def get_metrics(request: Request):
    payload = await request.json()
    target_regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    response_data = {}
    
    # --- DIAGNOSTIC: Auto-detect keys ---
    # We look at the first row to see what the labels are called
    sample = telemetry_data[0] if telemetry_data else {}
    
    # Find the region key (look for 'region', 'loc', or 'area')
    reg_key = next((k for k in sample if k.lower() in ['region', 'loc', 'location']), 'region')
    # Find the latency key (look for 'latency', 'ms', or 'delay')
    lat_key = next((k for k in sample if k.lower() in ['latency', 'ms', 'delay']), 'latency')
    # Find the uptime key
    up_key = next((k for k in sample if k.lower() in ['uptime', 'status', 'up']), 'uptime')
    
    for region in target_regions:
        # Filter data using the detected keys
        region_records = [row for row in telemetry_data if str(row.get(reg_key)).lower() == region.lower()]
        
        if not region_records:
            response_data[region] = {"error": "No data found for this region"}
            continue
            
        latencies = [float(row.get(lat_key, 0)) for row in region_records]
        uptimes = [float(row.get(up_key, 0)) for row in region_records]
        
        response_data[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for lat in latencies if lat > threshold))
        }
        
    return response_data
