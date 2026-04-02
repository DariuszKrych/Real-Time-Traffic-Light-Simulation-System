import sdl3

NS_GREEN_DURATION = 4.0
NS_ORANGE_DURATION = 1.0
EW_GREEN_DURATION = 4.0
EW_ORANGE_DURATION = 1.0

def get_current_phase(current_time):
    total_cycle = (
        NS_GREEN_DURATION
        + NS_ORANGE_DURATION
        + EW_GREEN_DURATION
        + EW_ORANGE_DURATION
    )

    cycle_time = current_time % total_cycle

    if cycle_time < NS_GREEN_DURATION:
        return "NS_GREEN"
    elif cycle_time < NS_GREEN_DURATION + NS_ORANGE_DURATION:
        return "NS_ORANGE"
    elif cycle_time < NS_GREEN_DURATION + NS_ORANGE_DURATION + EW_GREEN_DURATION:
        return "EW_GREEN"
    else:
        return "EW_ORANGE"

def set_light_timings(ns_green=None, ns_orange=None, ew_green=None, ew_orange=None):
    global NS_GREEN_DURATION, NS_ORANGE_DURATION, EW_GREEN_DURATION, EW_ORANGE_DURATION

    if ns_green is not None and ns_green > 0:
        NS_GREEN_DURATION = ns_green

    if ns_orange is not None and ns_orange > 0:
        NS_ORANGE_DURATION = ns_orange

    if ew_green is not None and ew_green > 0:
        EW_GREEN_DURATION = ew_green

    if ew_orange is not None and ew_orange > 0:
        EW_ORANGE_DURATION = ew_orange

def change_street_light_colour(keys, current_time):
    phase = get_current_phase(current_time)

    # Default all lights to red
    west_light = 'red'
    east_light = 'red'
    south_light = 'red'
    north_light = 'red'

    if phase == "NS_GREEN":
        north_light = 'green'
        south_light = 'green'

    elif phase == "NS_ORANGE":
        north_light = 'orange'
        south_light = 'orange'

    elif phase == "EW_GREEN":
        east_light = 'green'
        west_light = 'green'

    elif phase == "EW_ORANGE":
        east_light = 'orange'
        west_light = 'orange'

    current_street_light_colour = [west_light, east_light, south_light, north_light]
    return current_street_light_colour