import os
import csv
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY = os.environ["TOMTOM_API_KEY"]

# Initial test point, not yet verified as a warehouse-adjacent road
ROADS = {
    "Port Morris test": (40.805, -73.915)
}

url = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)

filename = "freshdirect_traffic.csv"

for road, (lat, lon) in ROADS.items():
    response = requests.get(
        url,
        params={
            "key": API_KEY,
            "point": f"{lat},{lon}"
        },
        timeout=20
    )
    response.raise_for_status()

    data = response.json()["flowSegmentData"]

    now = datetime.now(ZoneInfo("America/New_York"))

    current = data["currentTravelTime"]
    freeflow = data["freeFlowTravelTime"]

    row = {
        "timestamp": now.isoformat(),
        "road": road,
        "latitude": lat,
        "longitude": lon,
        "current_speed_kmh": data["currentSpeed"],
        "free_flow_speed_kmh": data["freeFlowSpeed"],
        "current_travel_seconds": current,
        "free_flow_seconds": freeflow,
        "delay_percent": round(
            (current - freeflow) / freeflow * 100, 1
        ) if freeflow else None,
        "matched_coordinates": str(
            data.get("coordinates", {})
        )
    }

    exists = os.path.exists(filename)

    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        if not exists:
            writer.writeheader()

        writer.writerow(row)

    print(road, row["delay_percent"], "% delay")
