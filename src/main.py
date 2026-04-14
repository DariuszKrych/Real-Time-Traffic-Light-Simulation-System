import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.render import create_window, create_junction_renderer, update_camera_from_input
from src.light_logic import change_street_light_colour, set_light_timings, update_dynamic_timings, set_manual_override, clear_manual_override
from src.cars import north, east, south, west
from src import gui
import sdl3
import ctypes
import math
import random

SPAWN_INTERVAL = 3.0

def main():
    window_dimensions, window, renderer = create_window()
    window_width, window_height = window_dimensions

    # Create the drawing function for the junction with all methods and attributes saved for it to access
    draw_scene = create_junction_renderer(window_dimensions)

    # Camera and zoom details
    camera_x, camera_y,camera_speed = 0, 0, 5
    zoom, min_zoom, max_zoom, zoom_speed = 1.0, 0.5, 2.0, 0.01

    # Enables alpha values for colour transparency when drawing
    sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

    framerate = 60
    frametime_sec = 1 / framerate
    frametime_msec = math.floor(1000/ framerate)
    global_time = 0

    # Spawn one car group per direction at the start
    direction_modules = [north, east, south, west]
    for mod in direction_modules:
        mod.spawn_car()

    last_spawn_time = 0

    last_dynamic_update = 0
    street_light_state = ['red', 'red', 'red', 'red']
    all_cars = []

    event = sdl3.SDL_Event()
    running = True

    while running:
        # Process events
        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                running = False
            elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
                gui.handle_mouse_click(event.button.x, event.button.y)

        # Get keyboard state and update camera
        keys = sdl3.SDL_GetKeyboardState(None)
        camera_x, camera_y, zoom = update_camera_from_input(
            keys, camera_x, camera_y, zoom,
            camera_speed, zoom_speed, min_zoom, max_zoom,
            window_width, window_height
        )

        # Read GUI state
        gui_state = gui.get_state()

        if gui_state["running"]:
            # Apply light mode logic
            if gui_state["light_mode"] == "automatic":
                clear_manual_override()
                if global_time - last_dynamic_update >= 1.0:
                    update_dynamic_timings(
                        north.get_queue_length(),
                        east.get_queue_length(),
                        south.get_queue_length(),
                        west.get_queue_length(),
                        base_green=gui_state["cycle_duration"]
                    )
                    last_dynamic_update = global_time
            else:
                set_manual_override(gui_state["manual_direction"])

            # Spawn a new car group at a random edge every SPAWN_INTERVAL seconds
            if global_time - last_spawn_time >= SPAWN_INTERVAL:
                random.choice(direction_modules).spawn_car()
                last_spawn_time = global_time

            # Check the current street light colour and pass it to be drawn
            street_light_state = change_street_light_colour(keys, global_time)

            # Check junction occupancy from each direction's current car state
            # Uses passed_through + distance, no 1-frame delay
            n_in = north.has_cars_in_junction()
            e_in = east.has_cars_in_junction()
            s_in = south.has_cars_in_junction()
            w_in = west.has_cars_in_junction()

            # A direction is blocked if ANY other direction has cars in the junction
            n_blocked = e_in or s_in or w_in
            e_blocked = n_in or s_in or w_in
            s_blocked = n_in or e_in or w_in
            w_blocked = n_in or e_in or s_in

            # Check the current cars states
            north_cars_states = north.change_states_of_cars(global_time, street_light_state, n_blocked)
            east_cars_states = east.change_states_of_carsE(global_time, street_light_state, e_blocked)
            west_cars_states = west.change_states_of_carsW(global_time, street_light_state, w_blocked)
            south_cars_states = south.change_states_of_carsS(global_time, street_light_state, s_blocked)

            all_cars = north_cars_states + east_cars_states + west_cars_states + south_cars_states

            # Advance time
            global_time += frametime_sec

        # Draw the junction with current camera, zoom and street light colour.
        draw_scene(renderer, camera_x, camera_y, zoom, street_light_state, all_cars)

        # Draw GUI overlay on top
        gui.draw_gui(renderer)

        # Present frame
        sdl3.SDL_RenderPresent(renderer)

        # Simple delay to maintain ~60 FPS (16ms per frame)
        sdl3.SDL_Delay(frametime_msec)

    # Clean up resources
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()

if __name__ == "__main__":
    main()
