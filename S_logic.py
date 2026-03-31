import math
import random

# --- S STREET PATH FUNCTIONS (Coming from Bottom, Heading North) ---

def S_Street_Path_1(drive_time, speed, start_y, turn_start_y):
    """Calculates the x, y, and rotation for a car turning LEFT (West) into the y = 50 lane."""
    # Force turn to start 50 pixels before the target lane
    turn_start_y = 100 
    
    distance_to_curve = abs(turn_start_y - start_y) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve (Heading North)
        car_y = start_y - (speed * drive_time)
        car_x = -50 # Left lane
        car_rotation = 90
        
    elif drive_time < t_turn_end:
        # Phase 2: The Left Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X curves West from -50 to -100, Y continues North from 100 to 50
        car_x = -100 + (50 * math.cos(angle_rad))
        car_y = turn_start_y - (50 * math.sin(angle_rad))
        
        car_rotation = 90 - (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading West)
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
        # Phase 1: Straight to the curve (Heading North)
        car_y = start_y - (speed * drive_time)
        car_x = -50
        car_rotation = 90
        
    elif drive_time < t_turn_end:
        # Phase 2: The Right Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X curves East from -50 to 0, Y curves North from 0 to -50
        car_x = 0 - (50 * math.cos(angle_rad))
        car_y = 0 - (50 * math.sin(angle_rad))
        
        car_rotation = 90 + (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading East)
        car_y = -50
        car_rotation = 180 
        dist_after_turn = speed * (drive_time - t_turn_end)
        car_x = 0 + dist_after_turn
        
    return car_x, car_y, car_rotation


# --- Path Randomiser ---
def path_randomiser_S():
    return random.choice([S_Street_Path_1, S_Street_Path_2, S_Street_Path_3])

# --- MAIN CAR STATE LOGIC ---
def change_states_of_carsS(current_time, street_light_states, _memory={"is_moving": False, "elapsed_time": 0.0, "last_time": None, "chosen_path": None}):
    speed = 300 
    
    start_y = 250 # Spawning at the bottom
    turn_start_y = 0 
    stop_line_y = 200 
    
    if _memory["chosen_path"] is None:
        _memory["chosen_path"] = path_randomiser_S()

    if _memory["last_time"] is None:
        _memory["last_time"] = current_time
    delta_t = current_time - _memory["last_time"]
    _memory["last_time"] = current_time

    distance_to_stop = abs(stop_line_y - start_y)
    t_to_stop_line = distance_to_stop / speed

    # Traffic light logic (Assumed index 1 for South)
    if street_light_states[1] == 'green':
        _memory["is_moving"] = True          
    elif street_light_states[1] == 'red':
        if _memory["elapsed_time"] < t_to_stop_line:
            _memory["is_moving"] = False
            
    if _memory["is_moving"]:
        _memory["elapsed_time"] += delta_t
        
    drive_time = _memory["elapsed_time"]
    
    my_path_function = _memory["chosen_path"]
    cyan_x, cyan_y, cyan_rotation = my_path_function(drive_time, speed, start_y, turn_start_y)

    curent_cars = ['car_body_1', cyan_x, cyan_y, cyan_rotation, [0, 200, 200, 255]]

    return [curent_cars]