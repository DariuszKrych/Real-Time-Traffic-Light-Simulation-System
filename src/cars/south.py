import math
import random

# --- S STREET PATH FUNCTIONS (Coming from Bottom, Heading North) ---
def S_Street_Path_1(drive_time, speed, start_y, turn_start_y):
    """Calculates the x, y, and rotation for a car turning LEFT (West) into the y = 50 lane."""
    turn_start_y = 100
    distance_to_curve = abs(turn_start_y - start_y)
    t_to_curve = distance_to_curve / speed
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        car_y = start_y - (speed * drive_time)
        car_x = -50
        car_rotation = 90
    elif drive_time < t_turn_end:
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        car_x = -100 + (50 * math.cos(angle_rad))
        car_y = turn_start_y - (50 * math.sin(angle_rad))
        car_rotation = 90 - (90 * rel_progress)
    else:
        car_y = 50
        car_rotation = 0
        dist_after_turn = speed * (drive_time - t_turn_end)
        car_x = -100 - dist_after_turn

    return car_x, car_y, car_rotation

def S_Street_Path_2(drive_time, speed, start_y, turn_start_y):
    """Straight path (Heading North)"""
    car_y = start_y - (speed * drive_time)
    car_x = -50
    car_rotation = 90
    return car_x, car_y, car_rotation

def S_Street_Path_3(drive_time, speed, start_y, turn_start_y):
    """Calculates the x, y, and rotation for a car turning RIGHT (East) into the y = -50 lane."""
    distance_to_curve = abs(turn_start_y - start_y)
    t_to_curve = distance_to_curve / speed
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        car_y = start_y - (speed * drive_time)
        car_x = -50
        car_rotation = 90
    elif drive_time < t_turn_end:
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        car_x = 0 - (50 * math.cos(angle_rad))
        car_y = 0 - (50 * math.sin(angle_rad))
        car_rotation = 90 + (90 * rel_progress)
    else:
        car_y = -50
        car_rotation = 180
        dist_after_turn = speed * (drive_time - t_turn_end)
        car_x = 0 + dist_after_turn

    return car_x, car_y, car_rotation

def path_randomiser_S():
    return random.choice([S_Street_Path_1, S_Street_Path_2, S_Street_Path_3])

# --- MULTI-GROUP CAR MANAGEMENT ---

CAR_COLORS = [
    [200, 0, 0, 255], [0, 0, 200, 255], [200, 200, 0, 255],
    [0, 200, 0, 255], [200, 100, 0, 255], [100, 0, 200, 255],
    [0, 200, 200, 255], [200, 0, 200, 255], [100, 100, 100, 255],
    [200, 150, 200, 255],
]

DESPAWN_BOUNDARY = 1400
CAR_LENGTH = 200  # car_body_1 is ~174 units long + gap
CAR_BODY_MODELS = ['car_body_' + str(i) for i in range(1, 13)]

_cars = []

def spawn_car():
    _cars.append({
        "is_moving": False,
        "elapsed_time": 0.0,
        "last_time": None,
        "chosen_path": path_randomiser_S(),
        "color": random.choice(CAR_COLORS),
        "passed_through": False,
        "speed": random.randint(200, 400),
        "body": random.choice(CAR_BODY_MODELS),
    })

def get_queue_length():
    return len(_cars)

def has_cars_in_junction():
    for car in _cars:
        if car["passed_through"]:
            distance = car["elapsed_time"] * car["speed"]
            if distance < 1200:
                return True
    return False

def _is_out_of_bounds(x, y):
    return abs(x) > DESPAWN_BOUNDARY or abs(y) > DESPAWN_BOUNDARY

def change_states_of_carsS(current_time, street_light_states, junction_blocked=False):
    start_y = 1000
    turn_start_y = 0

    light = street_light_states[2]

    # Sort cars front-to-back (highest distance = closest to junction)
    sorted_cars = sorted(enumerate(_cars), key=lambda ic: ic[1]["elapsed_time"] * ic[1]["speed"], reverse=True)

    all_cars = []
    cars_to_remove = []
    prev_car_distance = None

    for orig_idx, car in sorted_cars:
        speed = car["speed"]
        base_stop_distance = 800
        base_stop_time = base_stop_distance / speed

        if car["last_time"] is None:
            car["last_time"] = current_time
        delta_t = current_time - car["last_time"]
        car["last_time"] = current_time

        max_elapsed = float('inf')

        if prev_car_distance is not None:
            max_distance = prev_car_distance - CAR_LENGTH
            max_elapsed = max_distance / speed

        if not car["passed_through"]:
            if light == 'red' or junction_blocked:
                max_elapsed = min(max_elapsed, base_stop_time)
            elif car["elapsed_time"] >= base_stop_time:
                car["passed_through"] = True

        if car["elapsed_time"] >= max_elapsed:
            car["is_moving"] = False
        else:
            car["is_moving"] = True

        if car["is_moving"]:
            car["elapsed_time"] += delta_t
            if car["elapsed_time"] > max_elapsed:
                car["elapsed_time"] = max_elapsed

        drive_time = car["elapsed_time"]
        x, y, rot = car["chosen_path"](drive_time, speed, start_y, turn_start_y)

        if _is_out_of_bounds(x, y):
            cars_to_remove.append(orig_idx)
            continue

        prev_car_distance = car["elapsed_time"] * speed
        all_cars.append([car["body"], x, y, rot, car["color"]])

    for i in reversed(sorted(cars_to_remove)):
        _cars.pop(i)

    return all_cars
