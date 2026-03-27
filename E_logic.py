import math
import random

# --- PATH FUNCTIONS ---

def E_Street_Path_1(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning LEFT (North) into the x = -50 lane."""
    # We force the turn to start exactly 50 pixels before our target lane (-50)
    turn_start_x = -100 
    
    distance_to_curve = abs(turn_start_x - start_x) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve (Heading East)
        car_x = start_x + (speed * drive_time)
        car_y = -50
        car_rotation = 180
        
    elif drive_time < t_turn_end:
        # Phase 2: The Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X continues East from -100 to -50, Y curves North from -50 up to -100
        car_x = turn_start_x + (50 * math.sin(angle_rad))
        car_y = -100 + (50 * math.cos(angle_rad))
        
        car_rotation = 180 - (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading North)
        car_x = -50 # Perfectly aligned with the Top Road!
        car_rotation = 90 
        dist_after_turn = speed * (drive_time - t_turn_end)
        
        # Subtracting distance because North is the negative Y direction
        car_y = -100 - dist_after_turn
        
    return car_x, car_y, car_rotation

def E_Street_Path_2(drive_time, speed, start_x,turn_start_x):
    # Straight path
    car_x = start_x + (speed * drive_time)
    car_y = -50
    car_rotation = 180
    return car_x, car_y, car_rotation

def E_Street_Path_3(drive_time, speed, start_x, turn_start_x):
    """Calculates the x, y, and rotation for a car turning from the East street."""
    distance_to_curve = abs(turn_start_x - start_x) 
    t_to_curve = distance_to_curve / speed
    
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_to_curve + t_turn_duration

    if drive_time < t_to_curve:
        # Phase 1: Straight to the curve (Heading East)
        car_x = start_x + (speed * drive_time)
        car_y = -50
        car_rotation = 180
        
    elif drive_time < t_turn_end:
        # Phase 2: The Turn
        rel_progress = (drive_time - t_to_curve) / t_turn_duration
        angle_rad = (math.pi / 2) * rel_progress
        
        # X continues East from -100 to -50, Y curves North from -50 up to -100
        car_x = turn_start_x + (50 * math.sin(angle_rad))
        car_y = 0 - (50 * math.cos(angle_rad))
        
        car_rotation = 180 + (90 * rel_progress)
        
    else:
        # Phase 3: Driving off (Heading North)
        car_x = 50 # Perfectly aligned with the Top Road!
        car_rotation = 270
        dist_after_turn = speed * (drive_time - t_turn_end)
        
        # Subtracting distance because North is the negative Y direction
        car_y = 0 + dist_after_turn
        
    return car_x, car_y, car_rotation

# --- Path Randomiser ---
def path_randomiser():
    # random.choice directly picks one item from a list. 
    # Notice we are passing the ACTUAL functions, not calling them!
    return random.choice([E_Street_Path_1, E_Street_Path_2, E_Street_Path_3])

# --- MAIN CAR STATE LOGIC ---
# ADDED: "chosen_path": None to the default memory
def change_states_of_carsE(current_time, street_light_states, _memory={"is_moving": False, "elapsed_time": 0.0, "last_time": None, "chosen_path": None}):
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
    if street_light_states[0] == 'green':
        _memory["is_moving"] = True          
        
    elif street_light_states[0] == 'red':
        if _memory["elapsed_time"] < t_to_stop_line:
            _memory["is_moving"] = False
            
    # --- 3. UPDATE THE STOPWATCH ---
    if _memory["is_moving"]:
        _memory["elapsed_time"] += delta_t
        
    drive_time = _memory["elapsed_time"]
    
    # --- 4. CALL THE PATH FUNCTION ---
    # We grab the function we safely stored in memory, and call it!
    my_path_function = _memory["chosen_path"]
    purple_x, purple_y, purple_rotation = my_path_function(drive_time, speed, start_y, turn_start_y)
    #orange_x, orange_y, orange_rotation = my_path_function(drive_time, speed, start_y, turn_start_y)

    # --- 5. CREATE CARS ---
    purple_car = ['car_body_1', purple_x, purple_y, purple_rotation, [100, 0, 100, 255]]

    # Return ALL cars at the very end in one list
    current_cars = [purple_car]

    return current_cars
