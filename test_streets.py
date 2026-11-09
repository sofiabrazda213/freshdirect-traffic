import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

API_KEY = os.environ["TOMTOM_API_KEY"]

# Candidate points to test around Port Morris.
# These are NOT yet verified street locations.

POINTS = {
    "E 132nd near warehouse": (40.8017, -73.9170),
    "E 133rd area": (40.8025, -73.9155),
    "E 134th area": (40.8033, -73.9140),
    "E 135th area": (40.8040, -73.9125),
    "E 136th area": (40.8047, -73.9110),
    "E 137th area": (40.8054, -73.9095),
    "E 138th area": (40.8045, -73.9095),
    "Walnut Ave area": (40.8020, -73.9080),
    "Locust Ave area": (40.8010, -73.9065),
    "Port Morris west": (40.8005, -73.9140),
    "Port Morris east": (40.8015, -73.9100),
}

URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/18/json"
OUTPUT = Path("freshdirect_traffic.csv")
FIELDS = [
    "timestamp", "candidate", "query_lat", "query_lon", "status",
    "current_speed_kmh", "free_flow_speed_kmh", "current_travel_seconds",
    "free_flow_seconds", "delay_percent", "matched_start_lat",
    "matched_start_lon", "matched_end_lat", "matched_end_lon", "error",
]


def collect():
    timestamp = datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
    rows = []
    for name, (lat, lon) in POINTS.items():
        row = {field: "" for field in FIELDS}
        row.update(timestamp=timestamp, candidate=name, query_lat=lat, query_lon=lon)
        try:
            response = requests.get(
                URL, params={"key": API_KEY, "point": f"{lat},{lon}"}, timeout=20
            )
            if response.status_code != 200:
                row.update(status=f"HTTP {response.status_code}", error=response.text[:150])
            else:
                data = response.json()["flowSegmentData"]
                coords = data.get("coordinates", {}).get("coordinate", [])
                current = data.get("currentTravelTime")
                free = data.get("freeFlowTravelTime")
                row.update(
                    status="ok",
                    current_speed_kmh=data.get("currentSpeed", ""),
                    free_flow_speed_kmh=data.get("freeFlowSpeed", ""),
                    current_travel_seconds=current,
                    free_flow_seconds=free,
                    delay_percent=round((current / free - 1) * 100, 1) if free and current is not None else "",
                )
                if coords:
                    row.update(
                        matched_start_lat=coords[0]["latitude"],
                        matched_start_lon=coords[0]["longitude"],
                        matched_end_lat=coords[-1]["latitude"],
                        matched_end_lon=coords[-1]["longitude"],
                    )
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            row.update(status="error", error=str(exc)[:150])
        rows.append(row)
        print(f"{name}: {row['status']} | delay={row['delay_percent']}%")

    needs_header = not OUTPUT.exists() or OUTPUT.stat().st_size == 0
    with OUTPUT.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    collect()