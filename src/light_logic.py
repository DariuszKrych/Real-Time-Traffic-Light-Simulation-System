import sdl3

N_GREEN_DURATION = 4.0
N_ORANGE_DURATION = 1.0
E_GREEN_DURATION = 4.0
E_ORANGE_DURATION = 1.0
S_GREEN_DURATION = 4.0
S_ORANGE_DURATION = 1.0
W_GREEN_DURATION = 4.0
W_ORANGE_DURATION = 1.0

def get_current_phase(current_time):
    total_cycle = (
        N_GREEN_DURATION + N_ORANGE_DURATION
        + E_GREEN_DURATION + E_ORANGE_DURATION
        + S_GREEN_DURATION + S_ORANGE_DURATION
        + W_GREEN_DURATION + W_ORANGE_DURATION
    )

    cycle_time = current_time % total_cycle

    t = 0.0
    t += N_GREEN_DURATION
    if cycle_time < t:
        return "N_GREEN"
    t += N_ORANGE_DURATION
    if cycle_time < t:
        return "N_ORANGE"
    t += E_GREEN_DURATION
    if cycle_time < t:
        return "E_GREEN"
    t += E_ORANGE_DURATION
    if cycle_time < t:
        return "E_ORANGE"
    t += S_GREEN_DURATION
    if cycle_time < t:
        return "S_GREEN"
    t += S_ORANGE_DURATION
    if cycle_time < t:
        return "S_ORANGE"
    t += W_GREEN_DURATION
    if cycle_time < t:
        return "W_GREEN"
    return "W_ORANGE"

def set_light_timings(n_green=None, n_orange=None, e_green=None, e_orange=None,
                      s_green=None, s_orange=None, w_green=None, w_orange=None):
    global N_GREEN_DURATION, N_ORANGE_DURATION, E_GREEN_DURATION, E_ORANGE_DURATION
    global S_GREEN_DURATION, S_ORANGE_DURATION, W_GREEN_DURATION, W_ORANGE_DURATION

    if n_green is not None and n_green > 0:
        N_GREEN_DURATION = n_green
    if n_orange is not None and n_orange > 0:
        N_ORANGE_DURATION = n_orange
    if e_green is not None and e_green > 0:
        E_GREEN_DURATION = e_green
    if e_orange is not None and e_orange > 0:
        E_ORANGE_DURATION = e_orange
    if s_green is not None and s_green > 0:
        S_GREEN_DURATION = s_green
    if s_orange is not None and s_orange > 0:
        S_ORANGE_DURATION = s_orange
    if w_green is not None and w_green > 0:
        W_GREEN_DURATION = w_green
    if w_orange is not None and w_orange > 0:
        W_ORANGE_DURATION = w_orange

def change_street_light_colour(keys, current_time):
    phase = get_current_phase(current_time)

    # Default all lights to red
    west_light = 'red'
    east_light = 'red'
    south_light = 'red'
    north_light = 'red'

    if phase == "N_GREEN":
        north_light = 'green'
    elif phase == "N_ORANGE":
        north_light = 'orange'
    elif phase == "E_GREEN":
        east_light = 'green'
    elif phase == "E_ORANGE":
        east_light = 'orange'
    elif phase == "S_GREEN":
        south_light = 'green'
    elif phase == "S_ORANGE":
        south_light = 'orange'
    elif phase == "W_GREEN":
        west_light = 'green'
    elif phase == "W_ORANGE":
        west_light = 'orange'

    current_street_light_colour = [west_light, east_light, south_light, north_light]
    return current_street_light_colour