def change_street_light_colour(current_time):
    # Notes on changing street lights for Chris from Dariusz.
    # current_street_light_colour = [west_light, east_light, south_light, north_light]
    # where west_light, east_light, south_light and north_light can be:
    # 'green' 'orange' 'red'
    # Example usage: current_street_light_colour = ['green', 'red', 'orange', 'green']
    current_street_light_colour = ['red', 'red', 'red', 'red']

    # Some example code for turning street lights on and off as a starting point for ideas from Dariusz for Chris.
    # 10 second loop where one light is green for 2.5 seconds each on repeat
    cycle_time = current_time % 10

    # default all to red
    west_light = 'red'
    east_light = 'red'
    south_light = 'red'
    north_light = 'red'

    if cycle_time < 2.5:
        # 0-10 seconds: North Green
        north_light = 'green'
    elif cycle_time < 5:
        # 10-20 seconds: East Green
        east_light = 'green'
    elif cycle_time < 7.5:
        # 20-30 seconds: South Green
        south_light = 'green'
    else:
        # 30-40 seconds: West Green
        west_light = 'green'

    current_street_light_colour = [west_light, east_light, south_light, north_light]

    return current_street_light_colour