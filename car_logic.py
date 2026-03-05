def change_states_of_cars():
    # Notes on setting cars up for Justin from Dariusz.
    # current cars = [car, car, car, car] list of cars where every entry is a car
    # where, car = [car_x_pos, car_y_pos, car_rotation, car_rgba]
    # 0,0 is the center of the world.
    # Relative to 0,0. Up: -y, Down: +y, Right: +x, Left: -x
    # The road is 200 wide and lanes are 100 wide which is why +-50 centers the cars on them.
    # The car is facing left by default and rotation is in degrees clockwise.
    # rgba is how the car's colour is set, the below examples being light blue, orange and light grey respectively.
    current_cars = [
        [+230, +50, 0, [136, 213, 229, 255]],
        [+420, +50, 0, [241, 112, 35, 255]],
        [+50, -230, 270, [100, 100, 100, 255]],
    ]
    return current_cars