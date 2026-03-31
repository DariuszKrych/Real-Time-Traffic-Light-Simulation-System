import math
import random

# --- W STREET PATH FUNCTIONS (Coming from Right, Heading West) ---

def W_Street_Path_1(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning LEFT (South) into the x = 50 lane."""
    turn_start_x = 100 
    
    distance_to_curve = abs(turn_start_x - start_x) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve (Heading West)
        car_x = start_x - (speed * drive_time)
        car_y = 50 # Bottom lane
        car_rotation = 360 # 360 acts as 0, but allows smooth subtraction
        
    elif drive_time < t_turn_end:
        # Phase 2: The Left Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X continues West from 100 to 50, Y curves South from 50 down to 100
        car_x = turn_start_x - (50 * math.sin(angle_rad))
        car_y = 100 - (50 * math.cos(angle_rad))
        
        car_rotation = 360 - (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading South)
        car_x = 50 
        car_rotation = 270 
        dist_after_turn = speed * (drive_time - t_turn_end)
        
        car_y = 100 + dist_after_turn
        
    return car_x, car_y, car_rotation

def W_Street_Path_2(drive_time, speed, start_x, turn_start_x):
    """Straight path (Heading West)"""
    car_x = start_x - (speed * drive_time)
    car_y = 50
    car_rotation = 0
    return car_x, car_y, car_rotation

def W_Street_Path_3(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning RIGHT (North) into the x = -50 lane."""
    distance_to_curve = abs(turn_start_x - start_x) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve (Heading West)
        car_x = start_x - (speed * drive_time)
        car_y = 50
        car_rotation = 0
        
    elif drive_time < t_turn_end:
        # Phase 2: The Right Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X curves West from 0 to -50, Y curves North from 50 up to 0
        car_x = 0 - (50 * math.sin(angle_rad))
        car_y = 0 + (50 * math.cos(angle_rad))
        
        car_rotation = 0 + (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading North)
        car_x = -50 
        car_rotation = 90
        dist_after_turn = speed * (drive_time - t_turn_end)
        
        car_y = 0 - dist_after_turn
        
    return car_x, car_y, car_rotation

# --- Path Randomiser ---
def path_randomiser_W():
    return random.choice([W_Street_Path_1, W_Street_Path_2, W_Street_Path_3])

# --- MAIN CAR STATE LOGIC ---
def change_states_of_carsW(current_time, street_light_states, _memory={"is_moving": False, "elapsed_time": 0.0, "last_time": None, "chosen_path": None}):
    speed = 300 
    
    start_x = 250 # Spawning at the right
    turn_start_x = 0 
    stop_line_x = 200 
    
    if _memory["chosen_path"] is None:
        _memory["chosen_path"] = path_randomiser_W()

    if _memory["last_time"] is None:
        _memory["last_time"] = current_time
    delta_t = current_time - _memory["last_time"]
    _memory["last_time"] = current_time

    distance_to_stop = abs(stop_line_x - start_x)
    t_to_stop_line = distance_to_stop / speed

    # Traffic light logic (Assumed index 2 for West)
    if street_light_states[2] == 'green':
        _memory["is_moving"] = True          
    elif street_light_states[2] == 'red':
        if _memory["elapsed_time"] < t_to_stop_line:
            _memory["is_moving"] = False
            
    if _memory["is_moving"]:
        _memory["elapsed_time"] += delta_t
        
    drive_time = _memory["elapsed_time"]
    
    my_path_function = _memory["chosen_path"]
    yellow_x, yellow_y, yellow_rotation = my_path_function(drive_time, speed, start_x, turn_start_x)

    yellow_car = ['car_body_1', yellow_x, yellow_y, yellow_rotation, [200, 200, 0, 255]]

    return [yellow_car]