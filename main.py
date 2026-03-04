from render import create_window, create_junction_renderer, update_camera_from_input
import sdl3
import ctypes

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

        # Draw the junction with current camera and zoom
        draw_scene(renderer, camera_x, camera_y, zoom)

        # Simple delay to maintain ~60 FPS (16ms per frame)
        sdl3.SDL_Delay(16)

    # Clean up resources
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()

if __name__ == "__main__":
    main()