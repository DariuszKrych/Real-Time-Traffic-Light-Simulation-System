import ctypes
import sdl3

def create_window():
    sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

    window_dimensions = [1920, 1080]

    window_title = b"Traffic light simulation"
    window = sdl3.SDL_CreateWindow(window_title, window_dimensions[0], window_dimensions[1], 0)

    renderer = sdl3.SDL_CreateRenderer(window, None)

    return window_dimensions, window, renderer


def draw_junction(window_dimensions, sdl_window, sdl_renderer):
    window_width, window_height = window_dimensions
    window, renderer = sdl_window, sdl_renderer

    def draw_rectangle(x_coord, y_coord, rect_width, rect_height):
        rect = sdl3.SDL_FRect(x_coord, y_coord, rect_width, rect_height)
        sdl3.SDL_RenderFillRect(renderer, ctypes.byref(rect))


    # Common road details
    road_width = 200
    road_rgba_colour = [166, 156, 144, 255]

    # Defining horizontal road details
    horiz_road_width, horiz_road_height = [window_width, road_width]
    horiz_road_pos_x, horiz_road_pos_y = (window_width-horiz_road_width)/2, (window_height-horiz_road_height)/2

    # Defining vertical road details
    vert_road_width, vert_road_height = [road_width, window_height]
    vert_road_pos_x, vert_road_pos_y = (window_width-vert_road_width)/2, (window_height-vert_road_height)/2

    # Common lane line details
    lane_line_rgba_colour = [255, 255, 255, 255]
    lane_line_thickness = 10

    # Defining dotted lane lines
    lane_line_length = 50
    lane_line_gap = 30
    end_dist_before_junction = 20
    # Drawing dotted lane lines
    def dotted_lane_line_drawing():
        # Yes, the interpreter is complaining that the code is repeated, although it is worth it as otherwise it
        # would be incredibly illegible whereas now it is immediately very clear how all the dotted lane lines are being drawn.
        # Yes DRY is important although keeping maximum simplicity while creating the same features is also incredibly important.

        current_pos_y = (window_height - lane_line_thickness) / 2

        # Horizontal left road lane lines. (West)
        start_pos_x, end_pos_x = 0, ((window_width-road_width)/2) - end_dist_before_junction
        current_pos_x = start_pos_x + lane_line_gap
        while (current_pos_x+lane_line_length) < end_pos_x:
            draw_rectangle(current_pos_x, current_pos_y, lane_line_length, lane_line_thickness)
            current_pos_x = current_pos_x + lane_line_gap + lane_line_length

        # Horizontal right road lane lines. (East)
        start_pos_x, end_pos_x = window_width, ((window_width+road_width)/2) + end_dist_before_junction
        current_pos_x = start_pos_x - lane_line_gap - lane_line_length
        while current_pos_x > end_pos_x:
            draw_rectangle(current_pos_x, current_pos_y, lane_line_length, lane_line_thickness)
            current_pos_x = current_pos_x - lane_line_gap - lane_line_length

        current_pos_x = (window_width-lane_line_thickness)/2

        # Vertical top road lane lines. (North)
        start_pos_y, end_pos_y = 0, ((window_height-road_width)/2) - end_dist_before_junction
        current_pos_y = start_pos_y + lane_line_gap
        while (current_pos_y + lane_line_length) < end_pos_y:
            draw_rectangle(current_pos_x, current_pos_y, lane_line_thickness, lane_line_length)
            current_pos_y = current_pos_y + lane_line_gap + lane_line_length

        # Vertical bottom road lane lines. (South)
        start_pos_y, end_pos_y = window_height, ((window_height+road_width)/2) + end_dist_before_junction
        current_pos_y = start_pos_y - lane_line_gap - lane_line_length
        while current_pos_y > end_pos_y:
            draw_rectangle(current_pos_x, current_pos_y, lane_line_thickness, lane_line_length)
            current_pos_y = current_pos_y - lane_line_gap - lane_line_length

    # Drawing solid stop lines on the left lanes of each approach
    def stop_lane_line_drawing():
        line_length = road_width / 2  # half the road width

        # North approach (top)
        north_y = ((window_height - road_width) / 2) - end_dist_before_junction - lane_line_thickness
        north_x = window_width / 2
        draw_rectangle(north_x, north_y, line_length, lane_line_thickness)

        # South approach (bottom)
        south_y = ((window_height + road_width) / 2) + end_dist_before_junction
        south_x = (window_width - road_width) / 2
        draw_rectangle(south_x, south_y, line_length, lane_line_thickness)

        # East approach (right)
        east_x = ((window_width + road_width) / 2) + end_dist_before_junction
        east_y = window_height / 2
        draw_rectangle(east_x, east_y, lane_line_thickness, line_length)

        # West approach (left)
        west_x = ((window_width - road_width) / 2) - end_dist_before_junction - lane_line_thickness
        west_y = (window_height - road_width) / 2
        draw_rectangle(west_x, west_y, lane_line_thickness, line_length)


    event = sdl3.SDL_Event()
    running = True

    while running:

        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                running = False

        # Drawing background colour
        sdl3.SDL_SetRenderDrawColor(renderer, 172, 205, 111, 255)
        sdl3.SDL_RenderClear(renderer)

        # Setting to road colour
        sdl3.SDL_SetRenderDrawColor(renderer, road_rgba_colour[0], road_rgba_colour[1], road_rgba_colour[2], road_rgba_colour[3])
        # Drawing horizontal and vertical roads
        draw_rectangle(horiz_road_pos_x, horiz_road_pos_y, horiz_road_width, horiz_road_height)
        draw_rectangle(vert_road_pos_x, vert_road_pos_y, vert_road_width, vert_road_height)

        # Setting to lane line colour
        sdl3.SDL_SetRenderDrawColor(renderer, lane_line_rgba_colour[0], lane_line_rgba_colour[1], lane_line_rgba_colour[2], lane_line_rgba_colour[3])
        # Drawing lane lines
        dotted_lane_line_drawing()
        # Drawing stop lines
        stop_lane_line_drawing()

        # Present the frame to the window
        sdl3.SDL_RenderPresent(renderer)

        # Simple delay to maintain ~60 FPS (16ms per frame)
        sdl3.SDL_Delay(16)

    # Clean up resources
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()