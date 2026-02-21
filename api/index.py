from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

# 1. Create the app
app = FastAPI()

# 2. Enable CORS (Allow anyone to send a POST request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# 3. Load the data when the app starts
current_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(current_dir, 'q-vercel-latency.json')

with open(file_path, 'r') as f:
    telemetry_data = json.load(f)

# 4. Create the POST endpoint
@app.post("/api")
async def get_metrics(request: Request):
    # Read the incoming JSON question
    payload = await request.json()
    target_regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    response_data = {}
    
    for region in target_regions:
        # Filter data for this specific region
        # Note: This assumes your JSON is a list of records like {"region": "amer", "latency": 150, "uptime": 0.99}
        region_records = [row for row in telemetry_data if row.get("region") == region]
        
        if not region_records:
            continue
            
        latencies = [row.get("latency", 0) for row in region_records]
        uptimes = [row.get("uptime", 0) for row in region_records]
        
        # Calculate the math requirements
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for lat in latencies if lat > threshold)
        
        # Format the answer
        response_data[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }
        
    return response_data
