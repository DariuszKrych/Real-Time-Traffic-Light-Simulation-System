import math
import random

# --- PATH FUNCTIONS ---
def N_Street_Path_1(drive_time, speed, start_y, turn_start_y):
    """Calculates the x, y, and rotation for a car turning LEFT (East) into the y = -50 lane."""
    # We force the turn to start exactly 50 pixels before our target lane (-50)
    turn_start_y = -100 
    
    distance_to_curve = abs(turn_start_y - start_y) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve
        car_y = start_y + (speed * drive_time)
        car_x = 50
        car_rotation = 270
        
    elif drive_time < t_turn_end:
        # Phase 2: The Turn
        # Removed the "- 0.1" so the turn timing flows perfectly from Phase 1
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X curves East, Y continues South from -100 down to -50
        car_x = 100 - (50 * math.cos(angle_rad))
        car_y = turn_start_y + (50 * math.sin(angle_rad))
        
        car_rotation = 270 - (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading East)
        car_y = -50 # Perfectly aligned with the Right Road!
        car_rotation = 180 
        dist_after_turn = speed * (drive_time - t_turn_end)
        
        car_x = 100 + dist_after_turn
        
    return car_x, car_y, car_rotation

def N_Street_Path_2(drive_time, speed, start_y, turn_start_y):
    # Straight path
    car_y = start_y + (speed * drive_time)
    car_x = 50
    car_rotation = 270
    return car_x, car_y, car_rotation

def N_Street_Path_3(drive_time, speed, start_y, turn_start_y):
    """Calculates the x, y, and rotation for a car turning from the North street."""
    distance_to_curve = abs(turn_start_y - start_y) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve
        car_y = start_y + (speed * drive_time)
        car_x = 50
        car_rotation = 270
        
    elif drive_time < t_turn_end:
        # Phase 2: The Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        car_x = 50 * math.cos(angle_rad)
        car_y = 50 * math.sin(angle_rad)
        car_rotation = 270 + (90 * rel_progress)
        
    else:
        # Phase 3: Driving off
        car_y = 50
        car_rotation = 0 
        dist_after_turn = speed * (drive_time - t_turn_end)
        car_x = 0 - dist_after_turn
        
    return car_x, car_y, car_rotation


# --- Path Randomiser ---
def path_randomiser():
    # random.choice directly picks one item from a list. 
    # Notice we are passing the ACTUAL functions, not calling them!
    return random.choice([N_Street_Path_1,N_Street_Path_2, N_Street_Path_3])

# --- MAIN CAR STATE LOGIC ---
# ADDED: "chosen_path": None to the default memory
def change_states_of_cars(current_time, street_light_states, _memory={"is_moving": False, "elapsed_time": 0.0, "last_time": None, "chosen_path": None}):
    speed = 300 
    
    start_y = -250 # The starting y value for the grey car.
    turn_start_y = 0 
    stop_line_y = -200 # The y value of the stop line.
    
    # --- 0. ASSIGN A PATH ---
    # If the car just spawned and has no path, roll the dice and save it!
    if _memory["chosen_path"] is None:
        _memory["chosen_path"] = path_randomiser()

    # --- 1. CALCULATE TIME TICK (Delta Time) ---
    if _memory["last_time"] is None:
        _memory["last_time"] = current_time
    delta_t = current_time - _memory["last_time"]
    _memory["last_time"] = current_time

    # Calculate the Point of No Return
    distance_to_stop = abs(stop_line_y - start_y)
    t_to_stop_line = distance_to_stop / speed

    # --- 2. THE TRAFFIC LIGHT LOGIC (The Pause Button) ---
    if street_light_states[3] == 'green':
        _memory["is_moving"] = True          
        
    elif street_light_states[3] == 'red':
        if _memory["elapsed_time"] < t_to_stop_line:
            _memory["is_moving"] = False
            
    # --- 3. UPDATE THE STOPWATCH ---
    if _memory["is_moving"]:
        _memory["elapsed_time"] += delta_t
        
    drive_time = _memory["elapsed_time"]
    
    # --- 4. CALL THE PATH FUNCTION ---
    # We grab the function we safely stored in memory, and call it!
    my_path_function = _memory["chosen_path"]
    grey_x, grey_y, grey_rotation = my_path_function(drive_time, speed, start_y, turn_start_y)
    #orange_x, orange_y, orange_rotation = my_path_function(drive_time, speed, start_y, turn_start_y)

    # --- 5. CREATE CARS ---
    grey_car = ['car_body_1', grey_x, grey_y, grey_rotation, [100, 100, 100, 255]]

    # Return ALL cars at the very end in one list
    current_cars = [grey_car]

    return current_cars

