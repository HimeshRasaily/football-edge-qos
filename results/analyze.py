import csv
import statistics
import os
import glob

RESULTS_DIR = os.path.dirname(__file__)

# ---- Find the most recent CSV for each mode ----
def find_latest(mode):
    files = glob.glob(os.path.join(RESULTS_DIR, f"run_{mode}_*.csv"))
    if not files:
        return None
    return max(files, key=os.path.getctime)  # most recently created

MODE_FILES = {
    "none": find_latest("none"),
    "naive": find_latest("naive"),
    "qos": find_latest("qos"),
}


def load_readings(filepath):
    readings = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["tier"] = int(row["tier"])
            row["edge_latency_ms"] = float(row["edge_latency_ms"])
            readings.append(row)
    return readings


def analyze(readings, mode_name):
    all_latencies = [r["edge_latency_ms"] for r in readings]
    tier1 = [r["edge_latency_ms"] for r in readings if r["tier"] == 1]
    tier2 = [r["edge_latency_ms"] for r in readings if r["tier"] == 2]

    print(f"\n===== MODE: {mode_name.upper()} =====")
    print(f"Total readings delivered: {len(readings)}")

    print(f"\n-- Overall --")
    print(f"  Avg latency: {statistics.mean(all_latencies):.2f} ms")
    print(f"  Max latency: {max(all_latencies):.2f} ms")
    print(f"  Jitter (stdev): {statistics.stdev(all_latencies):.2f} ms")

    if tier1:
        print(f"\n-- Tier 1 (Urgent) — {len(tier1)} readings --")
        print(f"  Avg latency: {statistics.mean(tier1):.2f} ms")
        print(f"  Max latency: {max(tier1):.2f} ms")
        if len(tier1) > 1:
            print(f"  Jitter (stdev): {statistics.stdev(tier1):.2f} ms")
    else:
        print(f"\n-- Tier 1 (Urgent) — 0 readings --")

    if tier2:
        print(f"\n-- Tier 2 (Routine) — {len(tier2)} readings --")
        print(f"  Avg latency: {statistics.mean(tier2):.2f} ms")
        print(f"  Max latency: {max(tier2):.2f} ms")
        print(f"  Jitter (stdev): {statistics.stdev(tier2):.2f} ms")


# ---- RUN ANALYSIS FOR ALL THREE MODES ----
print("Files being analyzed:")
for mode, path in MODE_FILES.items():
    print(f"  {mode}: {path}")

for mode, path in MODE_FILES.items():
    if path is None:
        print(f"\n[WARNING] No file found for mode '{mode}' — skipping.")
        continue
    readings = load_readings(path)
    analyze(readings, mode)