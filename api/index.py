from fastapi import FastAPI, Response, Request
import json
import pathlib
import numpy as np

app = FastAPI()

@app.post("/api/analytics")
async def options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {}

@app.post("/api")
async def analytics(request: Request, response: Response):

    response.headers["Access-Control-Allow-Origin"] = "*"

    body = await request.json()

    BASE_DIR = pathlib.Path(__file__).parent
    file_path = BASE_DIR / "q-vercel-latency.json"

    with open(file_path) as f:
        data = json.load(f)

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        region_records = [
            r for r in data
            if r.get("region", "").lower() == region.lower()
        ]

        latencies = [float(r.get("latency_ms", 0)) for r in region_records]
        uptimes = [float(r.get("uptime", 0)) for r in region_records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return result
