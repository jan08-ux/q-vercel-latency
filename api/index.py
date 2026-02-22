from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import pathlib
import statistics

app = FastAPI()

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
    payload = await request.json()
    
    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        telemetry_data = json.load(f)

    results = {}
    
    # Use the keys from your payload
    target_regions = payload.get("regions", [])
    threshold_ms = payload.get("threshold_ms", 180)

    for region in target_regions:
        # Filter data (case-insensitive to be safe)
        region_data = [
            record for record in telemetry_data 
            if str(record.get("region", "")).lower() == region.lower()
        ]
        
        if not region_data:
            continue
        
        # NOTE: Using .get() with defaults to prevent crashes
        # Ensure "latency_ms" and "uptime" match your JSON file keys exactly
        latencies = [float(record.get("latency_ms", 0)) for record in region_data]
        uptimes = [float(record.get("uptime", 0)) for record in region_data]
        
        # Calculate mean latency
        avg_latency = statistics.mean(latencies)
        
        # Your custom P95 linear interpolation logic
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        fraction = index - lower
        
        if upper < n:
            p95_latency = sorted_latencies[lower] + fraction * (sorted_latencies[upper] - sorted_latencies[lower])
        else:
            p95_latency = sorted_latencies[lower]
        
        avg_uptime = statistics.mean(uptimes)
        
        # Count breaches
        breaches = sum(1 for lat in latencies if lat > threshold_ms)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3), # CRITICAL: Fixed to 3 decimal places
            "breaches": breaches
        }
    
    return {"regions": results}
