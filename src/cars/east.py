import math
import random

# --- PATH FUNCTIONS ---

def E_Street_Path_1(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning LEFT (North) into the x = -50 lane."""
    turn_start_x = -100

    distance_to_curve = abs(turn_start_x - start_x)
    t_to_curve = distance_to_curve / speed

    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        car_x = start_x + (speed * drive_time)
        car_y = -50
        car_rotation = 180

    elif drive_time < t_turn_end:
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress

        car_x = turn_start_x + (50 * math.sin(angle_rad))
        car_y = -100 + (50 * math.cos(angle_rad))

        car_rotation = 180 - (90 * rel_progress)

    else:
        car_x = -50
        car_rotation = 90
        dist_after_turn = speed * (drive_time - t_turn_end)

        car_y = -100 - dist_after_turn

    return car_x, car_y, car_rotation

def E_Street_Path_2(drive_time, speed, start_x, turn_start_x):
    """Straight path heading East."""
    car_x = start_x + (speed * drive_time)
    car_y = -50
    car_rotation = 180
    return car_x, car_y, car_rotation

def E_Street_Path_3(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning RIGHT (South) from the East street."""
    distance_to_curve = abs(turn_start_x - start_x)
    t_to_curve = distance_to_curve / speed

    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        car_x = start_x + (speed * drive_time)
        car_y = -50
        car_rotation = 180

    elif drive_time < t_turn_end:
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress

        car_x = turn_start_x + (50 * math.sin(angle_rad))
        car_y = 0 - (50 * math.cos(angle_rad))

        car_rotation = 180 + (90 * rel_progress)

    else:
        car_x = 50
        car_rotation = 270
        dist_after_turn = speed * (drive_time - t_turn_end)

        car_y = 0 + dist_after_turn

    return car_x, car_y, car_rotation

# --- PATH RANDOMISER ---
def path_randomiser():
    """Randomly selects one of the path functions."""
    return random.choice([E_Street_Path_1, E_Street_Path_2, E_Street_Path_3])

# --- MULTI-GROUP CAR MANAGEMENT ---

CAR_COLORS = [
    [200, 0, 0, 255], [0, 0, 200, 255], [200, 200, 0, 255],
    [0, 200, 0, 255], [200, 100, 0, 255], [100, 0, 200, 255],
    [0, 200, 200, 255], [200, 0, 200, 255], [100, 100, 100, 255],
    [200, 150, 200, 255],
]

DESPAWN_BOUNDARY = 1400
CAR_LENGTH = 200  # car_body_1 is ~174 units long + gap

_cars = []

def spawn_car():
    _cars.append({
        "is_moving": False,
        "elapsed_time": 0.0,
        "last_time": None,
        "chosen_path": path_randomiser(),
        "color": random.choice(CAR_COLORS),
        "passed_through": False,
    })

def _is_out_of_bounds(x, y):
    return abs(x) > DESPAWN_BOUNDARY or abs(y) > DESPAWN_BOUNDARY

def change_states_of_carsE(current_time, street_light_states):
    speed = 300
    start_y = -1000
    turn_start_y = 0
    base_stop_time = 800 / speed
    min_following_time = CAR_LENGTH / speed

    light = street_light_states[0]

    sorted_cars = sorted(enumerate(_cars), key=lambda ic: ic[1]["elapsed_time"], reverse=True)

    all_cars = []
    cars_to_remove = []
    prev_car_elapsed = None

    for orig_idx, car in sorted_cars:
        if car["last_time"] is None:
            car["last_time"] = current_time
        delta_t = current_time - car["last_time"]
        car["last_time"] = current_time

        max_elapsed = float('inf')

        if prev_car_elapsed is not None:
            max_elapsed = prev_car_elapsed - min_following_time

        if not car["passed_through"]:
            if light == 'red':
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

        prev_car_elapsed = car["elapsed_time"]
        all_cars.append(['car_body_1', x, y, rot, car["color"]])

    for i in reversed(sorted(cars_to_remove)):
        _cars.pop(i)

    return all_cars
