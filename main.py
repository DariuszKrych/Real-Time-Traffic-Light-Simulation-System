from render import create_window, create_junction_renderer, update_camera_from_input
from light_logic import change_street_light_colour
from car_logic import change_states_of_cars
import sdl3
import ctypes
import math

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

    event = sdl3.SDL_Event()
    running = True

    while running:
        # Process events
        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                running = False

        # Get keyboard state and update camera
        keys = sdl3.SDL_GetKeyboardState(None)
        camera_x, camera_y, zoom = update_camera_from_input(
            keys, camera_x, camera_y, zoom,
            camera_speed, zoom_speed, min_zoom, max_zoom,
            window_width, window_height
        )

        # Check the current street light colour and pass it to be drawn. FOR CHRIS
        street_light_state = change_street_light_colour(global_time)
        # Check the current cars states. FOR JUSTIN
        cars_states = change_states_of_cars(global_time)
        # Draw the junction with current camera, zoom and street light colour.
        draw_scene(renderer, camera_x, camera_y, zoom, street_light_state, cars_states)

        # Simple delay to maintain ~60 FPS (16ms per frame)
        sdl3.SDL_Delay(frametime_msec)
        global_time += frametime_sec

    # Clean up resources
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()

if __name__ == "__main__":
    main()