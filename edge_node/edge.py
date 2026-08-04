import sys
import os
import time
import threading
import queue

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "network_sim"))
from network import run_network_simulation

# ---- CONFIGURATION ----
BATCH_WINDOW_SECONDS = 2

# Modes: "none" = no aggregation, "naive" = batch everything, "qos" = QoS-aware
MODE = "qos"   # change this to "none" or "naive" to test other modes


def classify_tier(reading):
    """Tier 1 = urgent (impact event), Tier 2 = routine"""
    return 1 if reading["impact_event"] else 2


def process_reading(reading, tier2_batch):
    """
    Applies the selected MODE's logic to a single reading.
    Returns a list of readings that should be 'delivered' right now
    (empty list if nothing is delivered yet, e.g. still batching).
    """
    reading["arrival_time"] = time.time()
    tier = classify_tier(reading)
    reading["tier"] = tier

    if MODE == "none":
        # No aggregation: everything forwarded immediately
        reading["delivered_time"] = time.time()
        return [reading]

    elif MODE == "naive":
        # Naive aggregation: EVERYTHING (Tier 1 and Tier 2) gets batched equally
        tier2_batch.append(reading)
        return []  # released later by the batch flush timer

    elif MODE == "qos":
        if tier == 1:
            # Tier 1: forward immediately, no batching
            reading["delivered_time"] = time.time()
            return [reading]
        else:
            # Tier 2: hold for batching
            tier2_batch.append(reading)
            return []

    else:
        raise ValueError(f"Unknown MODE: {MODE}")


def flush_batch(batch):
    """Marks all readings in the batch as delivered NOW, then clears it."""
    now = time.time()
    delivered = []
    for reading in batch:
        reading["delivered_time"] = now
        delivered.append(reading)
    batch.clear()
    return delivered


def run_edge_node():
    """
    Pulls readings from the network layer, applies MODE logic,
    and yields readings as they get 'delivered'.
    """
    tier2_batch = []
    last_flush_time = time.time()

    for reading in run_network_simulation():
        delivered_now = process_reading(reading, tier2_batch)

        for d in delivered_now:
            latency_ms = round((d["delivered_time"] - d["sent_time"]) * 1000, 2)
            d["edge_latency_ms"] = latency_ms
            yield d

           # Pause the entire simulation on ANY Tier 1 (impact) event
            if d["tier"] == 1:
                label = "MAJOR INJURY" if d.get("major_event") else "MINOR IMPACT"

                # Flush any waiting Tier 2 readings BEFORE pausing,
                # so they don't sit frozen during the pause
                if tier2_batch:
                    flushed = flush_batch(tier2_batch)
                    for f in flushed:
                        latency_ms = round((f["delivered_time"] - f["sent_time"]) * 1000, 2)
                        f["edge_latency_ms"] = latency_ms
                        yield f
                    last_flush_time = time.time()

                print(f"\n>>> {label} DETECTED — Player {d['player_id']} "
                      f"at {d['sim_time_min']} min <<<")
                print(">>> SIMULATION PAUSED. Press Enter to resume... <<<")
                input()

                # Reset the flush timer after resuming, so pause duration
                # is never counted as batching delay
                last_flush_time = time.time()

        # Check if it's time to flush the batch (for "naive" and "qos" modes)
        if MODE in ("naive", "qos") and (time.time() - last_flush_time) >= BATCH_WINDOW_SECONDS:
            flushed = flush_batch(tier2_batch)
            for d in flushed:
                latency_ms = round((d["delivered_time"] - d["sent_time"]) * 1000, 2)
                d["edge_latency_ms"] = latency_ms
                yield d
            last_flush_time = time.time()

    # Flush any remaining batched readings at the very end
    if tier2_batch:
        flushed = flush_batch(tier2_batch)
        for d in flushed:
            latency_ms = round((d["delivered_time"] - d["sent_time"]) * 1000, 2)
            d["edge_latency_ms"] = latency_ms
            yield d


# ---- RUN DIRECTLY (for testing this file on its own) ----
if __name__ == "__main__":
    for reading in run_edge_node():
        tier_label = "TIER1-URGENT" if reading["tier"] == 1 else "tier2-routine"
        print(f"[EDGE OUT] {tier_label} | Player {reading['player_id']:>2} "
              f"| edge_latency={reading['edge_latency_ms']}ms")