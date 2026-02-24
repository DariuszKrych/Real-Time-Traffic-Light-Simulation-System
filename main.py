import ctypes
import sdl3


def main():
    sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

    window_title = b"SDL3 On Python Test"
    window = sdl3.SDL_CreateWindow(window_title, 800, 600, 0)

    renderer = sdl3.SDL_CreateRenderer(window, None)

    rect_x, rect_y = 350.0, 250.0
    rect_w, rect_h = 100.0, 100.0

    event = sdl3.SDL_Event()
    running = True

    while running:

        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                running = False

        sdl3.SDL_SetRenderDrawColor(renderer, 30, 30, 30, 255)
        sdl3.SDL_RenderClear(renderer)

        sdl3.SDL_SetRenderDrawColor(renderer, 50, 50, 255, 255)
        rect = sdl3.SDL_FRect(rect_x, rect_y, rect_w, rect_h)
        sdl3.SDL_RenderFillRect(renderer, ctypes.byref(rect))

        # Present the frame to the window
        sdl3.SDL_RenderPresent(renderer)

        # Simple delay to maintain ~60 FPS (16ms per frame)
        sdl3.SDL_Delay(16)

    # Clean up resources
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()


if __name__ == "__main__":
    main()