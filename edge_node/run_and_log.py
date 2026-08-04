import sys
import os
import csv
import time

sys.path.append(os.path.dirname(__file__))
from edge import run_edge_node, MODE

# ---- OUTPUT FILE SETUP ----
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

output_filename = f"run_{MODE}_{int(time.time())}.csv"
output_path = os.path.join(RESULTS_DIR, output_filename)

FIELDNAMES = [
    "player_id", "sim_time_min", "heart_rate", "accel_value",
    "impact_event", "major_event", "tier",
    "network_delay_ms", "edge_latency_ms"
]

print(f"Logging to: {output_path}\n")

with open(output_path, mode="w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()

    tier1_count = 0
    tier2_count = 0

    for reading in run_edge_node():
        row = {key: reading.get(key, "") for key in FIELDNAMES}
        writer.writerow(row)

        if reading["tier"] == 1:
            tier1_count += 1
            print(f"[LOGGED] TIER1-URGENT | Player {reading['player_id']:>2} "
                  f"| edge_latency={reading['edge_latency_ms']}ms")
        else:
            tier2_count += 1
            # Only print every 50th tier-2 reading, to reduce clutter
            if tier2_count % 50 == 0:
                print(f"[LOGGED] tier2-routine | Player {reading['player_id']:>2} "
                      f"| edge_latency={reading['edge_latency_ms']}ms "
                      f"(...{tier2_count} tier-2 readings so far)")

print(f"\nDone. Tier 1 readings: {tier1_count} | Tier 2 readings: {tier2_count}")
print(f"Saved to: {output_path}")