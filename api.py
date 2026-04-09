from fastapi import FastAPI
from safar_core import plan_routes

app = FastAPI()

@app.get("/route")
def get_route(start: str, end: str):
    fastest, safest, status = plan_routes(start, end)

    if fastest is None:
        return {"error": status}

    return {
        "fastest": {
            "coords": fastest.coords,
            "distance_km": fastest.distance_km,
            "time_min": fastest.time_min,
            "safety_score": fastest.safety_score,
            "safety_label": fastest.safety_label,
            "safety_explanation": fastest.safety_explanation
        },
        "safest": {
            "coords": safest.coords,
            "distance_km": safest.distance_km,
            "time_min": safest.time_min,
            "safety_score": safest.safety_score,
            "safety_label": safest.safety_label,
            "safety_explanation": safest.safety_explanation
        },
        "status": status
    }