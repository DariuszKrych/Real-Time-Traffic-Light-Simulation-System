import sdl3

N_GREEN_DURATION = 4.0
N_ORANGE_DURATION = 1.0
E_GREEN_DURATION = 4.0
E_ORANGE_DURATION = 1.0
S_GREEN_DURATION = 4.0
S_ORANGE_DURATION = 1.0
W_GREEN_DURATION = 4.0
W_ORANGE_DURATION = 1.0

# State machine: tracks current phase and time spent in it
_phase_index = 0  # 0-7 for the 8 phases
_phase_elapsed = 0.0
_last_time = None

PHASE_NAMES = [
    "N_GREEN", "N_ORANGE",
    "E_GREEN", "E_ORANGE",
    "S_GREEN", "S_ORANGE",
    "W_GREEN", "W_ORANGE",
]

# Manual override state
_manual_override = None  # None = automatic, or one of 'north','east','south','west'

def _get_phase_duration(index):
    durations = [
        N_GREEN_DURATION, N_ORANGE_DURATION,
        E_GREEN_DURATION, E_ORANGE_DURATION,
        S_GREEN_DURATION, S_ORANGE_DURATION,
        W_GREEN_DURATION, W_ORANGE_DURATION,
    ]
    return durations[index % 8]

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

def set_manual_override(direction):
    global _manual_override
    _manual_override = direction

def clear_manual_override():
    global _manual_override
    _manual_override = None

def change_street_light_colour(keys, current_time):
    global _phase_index, _phase_elapsed, _last_time

    # Manual override: directly set one direction green, rest red
    if _manual_override is not None:
        west_light = 'red'
        east_light = 'red'
        south_light = 'red'
        north_light = 'red'
        if _manual_override == 'north':
            north_light = 'green'
        elif _manual_override == 'east':
            east_light = 'green'
        elif _manual_override == 'south':
            south_light = 'green'
        elif _manual_override == 'west':
            west_light = 'green'
        return [west_light, east_light, south_light, north_light]

    # Automatic mode: state machine that advances forward
    if _last_time is None:
        _last_time = current_time

    delta = current_time - _last_time
    _last_time = current_time

    _phase_elapsed += delta

    # Advance through phases as needed
    while _phase_elapsed >= _get_phase_duration(_phase_index):
        _phase_elapsed -= _get_phase_duration(_phase_index)
        _phase_index = (_phase_index + 1) % 8

    phase = PHASE_NAMES[_phase_index]

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

def get_total_cycle_duration():
    return (N_GREEN_DURATION + N_ORANGE_DURATION
            + E_GREEN_DURATION + E_ORANGE_DURATION
            + S_GREEN_DURATION + S_ORANGE_DURATION
            + W_GREEN_DURATION + W_ORANGE_DURATION)

def update_dynamic_timings(n_queue, e_queue, s_queue, w_queue, base_green=4.0, min_green=2.0, max_green=8.0):
    total = n_queue + e_queue + s_queue + w_queue
    if total == 0:
        set_light_timings(n_green=base_green, e_green=base_green,
                          s_green=base_green, w_green=base_green)
        return
    for queue_len, setter_key in [(n_queue, 'n_green'), (e_queue, 'e_green'),
                                   (s_queue, 's_green'), (w_queue, 'w_green')]:
        proportion = queue_len / total
        duration = base_green + proportion * (max_green - min_green)
        duration = max(min_green, min(max_green, duration))
        set_light_timings(**{setter_key: duration})
