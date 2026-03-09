import math


def change_states_of_cars(current_time):
    # Notes on setting cars up for Justin from Dariusz.
    # current cars = [car, car, car, car] list of cars where every entry is a car
    # where, car = [car_body_type, car_x_pos, car_y_pos, car_rotation, car_rgba_colour]
    # 0,0 is the center of the world.
    # Relative to 0,0. Up: -y, Down: +y, Right: +x, Left: -x
    # The road is 200 wide and lanes are 100 wide which is why +-50 centers the cars on them.
    # The car is facing left by default and rotation is in degrees clockwise.
    # rgba is how the car's colour is set, the below examples being light blue, orange and grey respectively.
    # Example:
    # current_cars = [
    #     ['car_body_1', +230, +50, 0, [136, 213, 229, 255]],
    #     ['car_body_2', +420, +50, 0, [241, 112, 35, 255]],
    #     ['car_body_1', +50, -230, 270, [100, 100, 100, 255]],
    # ]


    # Some example code for moving the cars as a starting point for ideas from Dariusz for Justin.
    speed = 300  # Pixels per second

    # CAR 1: LIGHT BLUE
    # Drives left immediately
    blue_delay = 2.7
    blue_x = 230
    if current_time > blue_delay:
        blue_x -= speed * (current_time - blue_delay)
    blue_car = ['car_body_1', blue_x, 50, 0, [136, 213, 229, 255]]

    # CAR 2: ORANGE
    # Starts driving after a 2-second delay
    orange_delay = 3.2
    orange_x = 420
    if current_time > orange_delay:
        orange_x -= speed * (current_time - orange_delay)
    orange_car = ['car_body_2', orange_x, 50, 0, [241, 112, 35, 255]]

    # CAR 3: GREY
    # Initial State
    grey_x, grey_y, grey_rotation = 50, -230, 270

    # Phase 1: Straight down to the start of the junction (y=0)
    # Time to reach y=0: distance(230) / speed
    t_turn_start = 230 / speed

    # Phase 2: The Turn (A 90-degree arc with radius 50)
    # The arc length is (PI/2)*50 ≈ 78.5 pixels.
    t_turn_duration = (math.pi * 50 / 2) / speed
    t_turn_end = t_turn_start + t_turn_duration

    if current_time < t_turn_start:
        # Just driving south
        grey_y = -230 + (speed * current_time)

    elif current_time < t_turn_end:
        # The Smooth Turn
        # Calculate progress through turn (0.0 to 1.0)
        progress = (current_time - t_turn_start) / t_turn_duration
        angle_rad = (math.pi / 2) * progress

        # Move along arc centered at (0, 0) with radius 50
        grey_x = 50 * math.cos(angle_rad)
        grey_y = 50 * math.sin(angle_rad)
        # Rotate from 270 to 360
        grey_rotation = 270 + (90 * progress)

    else:
        # Phase 3: Driving off to the left
        grey_y = 50
        grey_rotation = 0  # 360 deg = 0 deg
        dist_after_turn = speed * (current_time - t_turn_end)
        grey_x = 0 - dist_after_turn

    grey_car = ['car_body_1', grey_x, grey_y, grey_rotation, [100, 100, 100, 255]]

    current_cars = [blue_car, orange_car, grey_car]

    return current_cars