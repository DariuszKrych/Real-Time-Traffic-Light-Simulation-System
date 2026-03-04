import ctypes
import sdl3

def create_window():
    sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

    window_dimensions = [1920, 1080]

    window_title = b"Traffic light simulation"
    window = sdl3.SDL_CreateWindow(window_title, window_dimensions[0], window_dimensions[1], 0)

    renderer = sdl3.SDL_CreateRenderer(window, None)

    return window_dimensions, window, renderer


def create_junction_renderer(window_dimensions):
    window_width, window_height = window_dimensions

    # Common road details
    road_length = 2000
    road_width = 200
    road_rgba_colour = [166, 156, 144, 255]

    # Defining horizontal road details
    horiz_road_width = road_length
    horiz_road_height = road_width
    horiz_road_pos_x = (window_width - horiz_road_width) / 2
    horiz_road_pos_y = (window_height - horiz_road_height) / 2

    # Defining vertical road details
    vert_road_width = road_width
    vert_road_height = road_length
    vert_road_pos_x = (window_width - vert_road_width) / 2
    vert_road_pos_y = (window_height - vert_road_height) / 2

    # Intersection centre (world coordinates)
    cx = horiz_road_pos_x + horiz_road_width / 2
    cy = horiz_road_pos_y + horiz_road_height / 2

    # Common lane line details
    lane_line_rgba_colour = [255, 255, 255, 255]
    lane_line_thickness = 10

    # Defining dotted lane lines
    lane_line_length = 50
    lane_line_gap = 30
    end_dist_before_junction = 20

    # ---- internal drawing helpers ----
    def draw_rectangle(renderer, x_coord, y_coord, rect_width, rect_height, camera_x, camera_y, zoom):
        # Translate world coordinates by camera offset and scale by zoom
        translated_x = x_coord - camera_x
        translated_y = y_coord - camera_y
        scaled_x = translated_x * zoom
        scaled_y = translated_y * zoom
        scaled_w = rect_width * zoom
        scaled_h = rect_height * zoom
        rect = sdl3.SDL_FRect(scaled_x, scaled_y, scaled_w, scaled_h)
        sdl3.SDL_RenderFillRect(renderer, ctypes.byref(rect))

    def draw_dotted_lines(renderer, camera_x, camera_y, zoom):
        # West approach (left side of horizontal road)
        start_x = cx - road_length / 2
        end_x = cx - road_width / 2 - end_dist_before_junction
        y = cy - lane_line_thickness / 2
        current_x = start_x + lane_line_gap
        while (current_x + lane_line_length) <= end_x:
            draw_rectangle(renderer, current_x, y, lane_line_length, lane_line_thickness, camera_x, camera_y, zoom)
            current_x = current_x + lane_line_gap + lane_line_length

        # East approach (right side of horizontal road)
        start_x = cx + road_length / 2
        end_x = cx + road_width / 2 + end_dist_before_junction
        current_x = start_x - lane_line_gap - lane_line_length
        while current_x >= end_x:
            draw_rectangle(renderer, current_x, y, lane_line_length, lane_line_thickness, camera_x, camera_y, zoom)
            current_x = current_x - lane_line_gap - lane_line_length

        # North approach (top side of vertical road)
        start_y = cy - road_length / 2
        end_y = cy - road_width / 2 - end_dist_before_junction
        x = cx - lane_line_thickness / 2
        current_y = start_y + lane_line_gap
        while (current_y + lane_line_length) <= end_y:
            draw_rectangle(renderer, x, current_y, lane_line_thickness, lane_line_length, camera_x, camera_y, zoom)
            current_y = current_y + lane_line_gap + lane_line_length

        # South approach (bottom side of vertical road)
        start_y = cy + road_length / 2
        end_y = cy + road_width / 2 + end_dist_before_junction
        current_y = start_y - lane_line_gap - lane_line_length
        while current_y >= end_y:
            draw_rectangle(renderer, x, current_y, lane_line_thickness, lane_line_length, camera_x, camera_y, zoom)
            current_y = current_y - lane_line_gap - lane_line_length

    def draw_stop_lines(renderer, camera_x, camera_y, zoom):
        line_length = road_width / 2  # half the road width

        # North approach (top)
        north_y = cy - road_width / 2 - end_dist_before_junction - lane_line_thickness
        north_x = cx
        draw_rectangle(renderer, north_x, north_y, line_length, lane_line_thickness, camera_x, camera_y, zoom)

        # South approach (bottom)
        south_y = cy + road_width / 2 + end_dist_before_junction
        south_x = cx - road_width / 2
        draw_rectangle(renderer, south_x, south_y, line_length, lane_line_thickness, camera_x, camera_y, zoom)

        # East approach (right)
        east_x = cx + road_width / 2 + end_dist_before_junction
        east_y = cy
        draw_rectangle(renderer, east_x, east_y, lane_line_thickness, line_length, camera_x, camera_y, zoom)

        # West approach (left)
        west_x = cx - road_width / 2 - end_dist_before_junction - lane_line_thickness
        west_y = cy - road_width / 2
        draw_rectangle(renderer, west_x, west_y, lane_line_thickness, line_length, camera_x, camera_y, zoom)

    # ---- main drawing function (returned) ----
    def draw_scene(renderer, camera_x, camera_y, zoom):
        # Drawing background colour
        sdl3.SDL_SetRenderDrawColor(renderer, 172, 205, 111, 255)
        sdl3.SDL_RenderClear(renderer)

        # Setting to road colour
        sdl3.SDL_SetRenderDrawColor(renderer, road_rgba_colour[0], road_rgba_colour[1], road_rgba_colour[2], road_rgba_colour[3])
        # Drawing horizontal and vertical roads
        draw_rectangle(renderer, horiz_road_pos_x, horiz_road_pos_y, horiz_road_width, horiz_road_height, camera_x, camera_y, zoom)
        draw_rectangle(renderer, vert_road_pos_x, vert_road_pos_y, vert_road_width, vert_road_height, camera_x, camera_y, zoom)

        # Setting to lane line colour
        sdl3.SDL_SetRenderDrawColor(renderer, lane_line_rgba_colour[0], lane_line_rgba_colour[1], lane_line_rgba_colour[2], lane_line_rgba_colour[3])
        # Drawing lane lines
        draw_dotted_lines(renderer, camera_x, camera_y, zoom)
        # Drawing stop lines
        draw_stop_lines(renderer, camera_x, camera_y, zoom)

        # Present the frame to the window
        sdl3.SDL_RenderPresent(renderer)

    return draw_scene


def update_camera_from_input(keys, camera_x, camera_y, zoom, camera_speed, zoom_speed, min_zoom, max_zoom, window_width, window_height):
    new_camera_x = camera_x
    new_camera_y = camera_y
    new_zoom = zoom

    # WASD camera movement
    if keys[sdl3.SDL_SCANCODE_W]:
        new_camera_y -= camera_speed  # move camera up
    if keys[sdl3.SDL_SCANCODE_S]:
        new_camera_y += camera_speed  # move camera down
    if keys[sdl3.SDL_SCANCODE_A]:
        new_camera_x -= camera_speed  # move camera left
    if keys[sdl3.SDL_SCANCODE_D]:
        new_camera_x += camera_speed  # move camera right

    # Q/E Zoom inputs (zoom in/out centered on screen)
    if keys[sdl3.SDL_SCANCODE_Q]:
        # Zoom in
        new_zoom = zoom + zoom_speed
        if new_zoom > max_zoom:
            new_zoom = max_zoom
        if new_zoom != zoom:
            # Compute world point currently at screen centre before changing zoom
            world_center_x = camera_x + (window_width / 2) / zoom
            world_center_y = camera_y + (window_height / 2) / zoom
            new_zoom = new_zoom
            # Adjust camera so that same world point stays at screen centre
            new_camera_x = world_center_x - (window_width / 2) / new_zoom
            new_camera_y = world_center_y - (window_height / 2) / new_zoom

    if keys[sdl3.SDL_SCANCODE_E]:
        # Zoom out
        new_zoom = zoom - zoom_speed
        if new_zoom < min_zoom:
            new_zoom = min_zoom
        if new_zoom != zoom:
            world_center_x = camera_x + (window_width / 2) / zoom
            world_center_y = camera_y + (window_height / 2) / zoom
            new_zoom = new_zoom
            new_camera_x = world_center_x - (window_width / 2) / new_zoom
            new_camera_y = world_center_y - (window_height / 2) / new_zoom

    return new_camera_x, new_camera_y, new_zoom