import random
import time

# ---- CONFIGURATION ----
NUM_PLAYERS = 22
MATCH_MINUTES_SIMULATED = 90        # real football match length
DEMO_MINUTES_REAL = 4               # how long our demo actually runs
TIME_MULTIPLIER = MATCH_MINUTES_SIMULATED / DEMO_MINUTES_REAL  # 22.5x speed

IMPACT_CHANCE_PER_READING = 0.0005    # 0.05% random chance per player per reading
READING_INTERVAL_REAL_SECONDS = 1   # how often (real time) we generate new readings

# ---- PLAYER SETUP ----
class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.heart_rate = random.randint(70, 90)  # resting-ish starting point

    def generate_reading(self, simulated_time_minutes):
        # Heart rate drifts slightly each reading (simulating exertion changes)
        self.heart_rate += random.randint(-3, 3)
        self.heart_rate = max(60, min(190, self.heart_rate))  # keep realistic bounds

        # Accelerometer: normal small values, unless an impact occurs
        impact_occurred = random.random() < IMPACT_CHANCE_PER_READING
        accel_value = random.uniform(0.5, 2.0)  # normal movement range
        if impact_occurred:
            accel_value = random.uniform(8.0, 12.0)  # simulate a hard impact spike

        return {
            "player_id": self.player_id,
            "sim_time_min": round(simulated_time_minutes, 2),
            "heart_rate": self.heart_rate,
            "accel_value": round(accel_value, 2),
            "impact_event": impact_occurred
        }


# ---- SIMULATION SETUP ----
players = [Player(i) for i in range(1, NUM_PLAYERS + 1)]

# Guarantee one major impact event at a random point in the match
guaranteed_impact_player = random.choice(players)
guaranteed_impact_time = random.uniform(10, 80)  # somewhere between 10-80 simulated minutes
guaranteed_impact_triggered = False

# ---- MAIN LOOP (now a generator function) ----
def run_match():
    global guaranteed_impact_triggered
    simulated_time_minutes = 0
    print("Match starting...\n")

    while simulated_time_minutes < MATCH_MINUTES_SIMULATED:

        for player in players:
            reading = player.generate_reading(simulated_time_minutes)

            # Check for the guaranteed major impact event
            if (not guaranteed_impact_triggered
                    and player.player_id == guaranteed_impact_player.player_id
                    and simulated_time_minutes >= guaranteed_impact_time):
                reading["accel_value"] = random.uniform(15.0, 20.0)  # major impact
                reading["impact_event"] = True
                reading["major_event"] = True
                guaranteed_impact_triggered = True
            else:
                reading["major_event"] = False

            # Print for our own visibility (temporary, until dashboard exists)
            if reading["impact_event"]:
                print(f"IMPACT EVENT! Player {reading['player_id']} at {reading['sim_time_min']} min "
                      f"| accel={reading['accel_value']} | heart_rate={reading['heart_rate']}")
            else:
                print(f"[{reading['sim_time_min']:>5.1f} min] Player {reading['player_id']:>2} "
                      f"| HR: {reading['heart_rate']:>3} bpm | Accel: {reading['accel_value']:>4.2f}")

            # THIS is the key change: hand the reading to whoever is using this generator
            yield reading

            # If it's the major guaranteed event, pause here (yield already happened,
            

        # advance simulated time based on real time elapsed
        simulated_time_minutes += (READING_INTERVAL_REAL_SECONDS * TIME_MULTIPLIER) / 60
        time.sleep(READING_INTERVAL_REAL_SECONDS)

    print("\nMatch ended.")


# ---- RUN DIRECTLY (only happens if you run this file by itself) ----
if __name__ == "__main__":
    for reading in run_match():
        pass  # readings are already printed inside run_match(); this just drives the loop

    # advance simulated time based on real time elapsed
    simulated_time_minutes += (READING_INTERVAL_REAL_SECONDS * TIME_MULTIPLIER) / 60
    time.sleep(READING_INTERVAL_REAL_SECONDS)

print("\nMatch ended.")