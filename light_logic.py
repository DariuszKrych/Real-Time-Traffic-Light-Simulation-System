import sdl3


def change_street_light_colour(keys, current_time):
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

    if keys[sdl3.SDL_SCANCODE_1]:
        north_light = 'green'
    if keys[sdl3.SDL_SCANCODE_2]:
        east_light = 'green'
    if keys[sdl3.SDL_SCANCODE_3]:
        south_light = 'green'
    if keys[sdl3.SDL_SCANCODE_4]:
        west_light = 'green'

    # if cycle_time < 2.5:
    #     # 0-10 seconds: North Green
    #     north_light = 'green'
    # elif cycle_time < 5:
    #     # 10-20 seconds: East Green
    #     east_light = 'green'
    # elif cycle_time < 7.5:
    #     # 20-30 seconds: South Green
    #     south_light = 'green'
    # else:
    #     # 30-40 seconds: West Green
    #     west_light = 'green'

    current_street_light_colour = [west_light, east_light, south_light, north_light]

    return current_street_light_colour