#!/usr/bin/env python3

import argparse
import json
import sys

from collections import defaultdict
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description="Find days with > threshold km travelled by car in Google Timeline JSON export file. Each activity's full distanceMeters is attributed to the calendar day of its startTime")
    p.add_argument("--file", "-f", required=True, help="Path to Timeline.json")
    p.add_argument("--threshold", "-t", type=float, default=100.0, help="Threshold in km")
    return p.parse_args()


def is_vehicle_type(candidate_type: str) -> bool:
    if not candidate_type:
        return False
    t = candidate_type.upper()
    keywords = ["VEHICLE", "CAR", "DRIVE", "DRIVING", "IN_PASSENGER", "IN_VEHICLE", "TAXI", "BUS"]
    return any(k in t for k in keywords)


def get_entries(data):
    # Support multiple possible top-level array keys used by Google exports
    if isinstance(data, dict):
        for key in ("semanticSegments", "timelineObjects", "segments", "timelineObjectsV2"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # fallback: look for any top-level value that's a list of dicts
        for v in data.values():
            if isinstance(v, list):
                return v
    if isinstance(data, list):
        return data
    return []


def parse_date(date_str: str) -> datetime.date:
    # Use fromisoformat which accepts offset like +02:00 in modern Pythons
    try:
        dt = datetime.fromisoformat(date_str)
    except Exception:
        # fallback: strip milliseconds and timezone offset
        try:
            if "+" in date_str:
                core = date_str.split("+")[0]
            elif "-" in date_str[19:]:
                # timezone like -01:00
                core = date_str.rsplit("-", 1)[0]
            else:
                core = date_str
            dt = datetime.fromisoformat(core)
        except Exception:
            raise
    return dt.date()


def analyze(entries, threshold_km) -> list[tuple[str, float]]:
    per_day_meters = defaultdict(float)

    for e in entries:
        # try several shapes: 'activity' (sample), or 'activitySegment', or nested 'activity' in 'activitySegment'
        activity = e.get("activity") or e.get("activitySegment") or e.get("activities")
        if not activity:
            # sometimes activities are nested or named differently; try keys
            # also skip plain timelinePath / visit entries
            continue

        # Normalize to dict possibly containing distanceMeters and topCandidate
        # If 'activities' is a list, iterate it
        acts = []
        if isinstance(activity, list):
            acts = activity
        elif isinstance(activity, dict):
            acts = [activity]
        else:
            continue

        for act in acts:
            # distanceMeters sometimes under act['distanceMeters']
            dist = None
            if isinstance(act, dict) and "distanceMeters" in act:
                dist = act.get("distanceMeters")
            # sometimes distance is under act['distance'] or nested under 'metadata' - handle common ones
            if dist is None:
                if isinstance(act, dict) and "distance" in act:
                    try:
                        dist = float(act.get("distance"))
                    except Exception:
                        dist = None

            if dist is None:
                # nothing to sum
                continue

            # find candidate type
            cand = None
            if isinstance(act.get("topCandidate"), dict):
                cand = act.get("topCandidate").get("type")
            # sometimes nested differently
            if not cand and isinstance(act.get("topCandidate"), str):
                cand = act.get("topCandidate")

            if not is_vehicle_type(cand or ""):
                continue

            # attribute to day of startTime
            start = e.get("startTime") or e.get("startTimestamp") or e.get("startTimeLocal")
            if not start and isinstance(act.get("start"), dict) and act.get("start").get("timestamp"):
                start = act.get("start").get("timestamp")
            if not start:
                # skip if no start time
                continue
            try:
                day = parse_date(start)
            except Exception:
                # if parsing fails, skip
                continue

            per_day_meters[day] += float(dist)

    # print days exceeding threshold
    threshold_m = threshold_km * 1000.0
    out = []
    for day, meters in sorted(per_day_meters.items()):
        km = meters / 1000.0
        if km > threshold_km:
            out.append((day.isoformat(), round(km, 3)))

    return out


def main():
    args = parse_args()
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = get_entries(data)
        results = analyze(entries, args.threshold)
    except Exception as exc:
        print(f"Error processing file: {exc}", file=sys.stderr)
        sys.exit(2)

    if not results:
        print(f"No days with > {args.threshold} km found.")
        return

    print(f"Days with > {args.threshold} km (date, km):")
    for day, km in results:
        print(f"{day}    {km}")


if __name__ == "__main__":
    main()
