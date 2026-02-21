from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

# Enable CORS for everyone
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# 1. Load the data correctly
current_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(current_dir, 'q-vercel-latency.json')

try:
    with open(file_path, 'r') as f:
        telemetry_data = json.load(f)
except Exception as e:
    telemetry_data = []

@app.post("/api")
async def get_metrics(request: Request):
    payload = await request.json()
    target_regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    # 2. Automatically find the right "Labels" (Keys) in your JSON
    # This checks the first row of your data to see what the columns are named
    if not telemetry_data:
        return {"error": "Data file is empty or not found"}
        
    sample = telemetry_data[0]
    # Find keys that look like 'region', 'latency', and 'uptime'
    reg_key = next((k for k in sample if k.lower() in ['region', 'loc', 'location']), 'region')
    lat_key = next((k for k in sample if k.lower() in ['latency', 'ms', 'delay']), 'latency')
    up_key = next((k for k in sample if k.lower() in ['uptime', 'status', 'up']), 'uptime')

    response_data = {}
    
    for region in target_regions:
        # 3. Filter data (Case-Insensitive)
        # We use .lower() so 'Amer' and 'amer' both match
        region_records = [
            row for row in telemetry_data 
            if str(row.get(reg_key, '')).lower() == region.lower()
        ]
        
        if not region_records:
            continue
            
        # Extract the numbers
        latencies = [float(row.get(lat_key, 0)) for row in region_records]
        uptimes = [float(row.get(up_key, 0)) for row in region_records]
        
        # 4. Perform the Math
        response_data[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for lat in latencies if lat > threshold))
        }
        
    return response_data
