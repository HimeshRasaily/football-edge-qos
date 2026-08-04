import random
import time
import sys
import os

# Allow importing generator.py from the sibling data_generator folder
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data_generator"))
from generator import run_match

# ---- CONFIGURATION ----
MIN_DELAY_MS = 20
MAX_DELAY_MS = 150
PACKET_LOSS_CHANCE = 0.01  # 1%


def transmit(reading):
    """
    Simulates sending one reading across a network.
    Returns the reading with added network metadata,
    or None if the packet was 'lost'.
    """
    # Simulate packet loss
    if random.random() < PACKET_LOSS_CHANCE:
        return None  # packet dropped

    # Simulate transmission delay
    delay_ms = random.uniform(MIN_DELAY_MS, MAX_DELAY_MS)
    time.sleep(delay_ms / 1000)  # convert ms to seconds for the actual pause

    reading["network_delay_ms"] = round(delay_ms, 2)
    reading["sent_time"] = time.time()
    return reading


def run_network_simulation():
    """
    Pulls readings from the data generator, passes them through
    the simulated network, and yields the ones that survive
    (i.e., weren't 'lost').
    """
    lost_count = 0
    delivered_count = 0

    for reading in run_match():
        result = transmit(reading)

        if result is None:
            lost_count += 1
            print(f"    [NETWORK] Packet LOST — Player {reading['player_id']} "
                  f"at {reading['sim_time_min']} min")
            continue

        delivered_count += 1
        yield result

    print(f"\n[NETWORK SUMMARY] Delivered: {delivered_count} | Lost: {lost_count}")


# ---- RUN DIRECTLY (for testing this file on its own) ----
if __name__ == "__main__":
    for reading in run_network_simulation():
        pass  # readings already printed inside generator; this just drives the loop