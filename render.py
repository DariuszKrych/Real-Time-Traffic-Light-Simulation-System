import ctypes
import sdl3
import math


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

    def draw_circle(renderer, center_x, center_y, radius, camera_x, camera_y, zoom):
        # Translate world coordinates by camera offset
        translated_center_x = center_x - camera_x
        translated_center_y = center_y - camera_y
        # Scale by zoom to get screen coordinates
        screen_center_x = translated_center_x * zoom
        screen_center_y = translated_center_y * zoom
        screen_radius = radius * zoom
        # Loop over screen Y pixels that fall inside the circle's bounding box
        y_start = int(screen_center_y - screen_radius)
        y_end = int(screen_center_y + screen_radius)

        for screen_y in range(y_start, y_end + 1):
            dy = screen_y - screen_center_y
            if abs(dy) > screen_radius:
                continue
            # Half-width of the circle at this screen Y
            dx = int(math.sqrt(screen_radius * screen_radius - dy * dy))
            x1 = int(screen_center_x - dx)
            x2 = int(screen_center_x + dx)

            # Draw a horizontal line (screen_y is same for both endpoints)
            sdl3.SDL_RenderLine(renderer, x1, screen_y, x2, screen_y)


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

    def draw_traffic_lights(renderer, camera_x, camera_y, zoom,  light_state):
        pole_length, pole_thickness, gap_to_mid_sq, light_radius, light_gap = 130, 50, 30, 15, 10
        half_rd_width = road_width / 2

        west_light_state = light_state[0]
        east_light_state = light_state[1]
        south_light_state = light_state[2]
        north_light_state = light_state[3]

        # West traffic light
        x_pos, y_pos = cx - half_rd_width - pole_length - gap_to_mid_sq, cy - half_rd_width - pole_thickness - gap_to_mid_sq
        sdl3.SDL_SetRenderDrawColor(renderer, 38, 40, 43, 255)  # Dark Grey
        draw_rectangle(renderer, x_pos, y_pos, pole_length, pole_thickness, camera_x, camera_y, zoom)
            # green light
        x_pos, y_pos = x_pos + light_gap + light_radius, y_pos + light_gap + light_radius
        sdl3.SDL_SetRenderDrawColor(renderer, 87, 150, 92, west_light_state[0])  # Green
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # orange light
        x_pos = x_pos + light_gap + light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 203, 128, 77, west_light_state[1]) # Orange
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # red light
        x_pos = x_pos + light_gap + light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 201, 79, 79, west_light_state[2])  # Red
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)

        # East traffic light
        x_pos, y_pos = cx + half_rd_width + gap_to_mid_sq, cy + half_rd_width + gap_to_mid_sq
        sdl3.SDL_SetRenderDrawColor(renderer, 38, 40, 43, 255)  # Dark Grey
        draw_rectangle(renderer, x_pos, y_pos, pole_length, pole_thickness, camera_x, camera_y, zoom)
            # green light
        x_pos, y_pos = x_pos + pole_length - light_gap - light_radius, y_pos + light_gap + light_radius
        sdl3.SDL_SetRenderDrawColor(renderer, 87, 150, 92, east_light_state[0])  # Green
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # orange light
        x_pos = x_pos - light_gap - light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 203, 128, 77, east_light_state[1]) # Orange
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # red light
        x_pos = x_pos - light_gap - light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 201, 79, 79, east_light_state[2])  # Red
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)

        # South traffic light
        x_pos, y_pos = cx - half_rd_width - pole_thickness - gap_to_mid_sq, cy + half_rd_width + gap_to_mid_sq
        sdl3.SDL_SetRenderDrawColor(renderer, 38, 40, 43, 255)  # Dark Grey
        draw_rectangle(renderer, x_pos, y_pos, pole_thickness, pole_length, camera_x, camera_y, zoom)
            # green light
        x_pos, y_pos = x_pos + light_gap + light_radius, y_pos + pole_length - light_gap - light_radius
        sdl3.SDL_SetRenderDrawColor(renderer, 87, 150, 92, south_light_state[0])  # Green
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # orange light
        y_pos = y_pos - light_gap - light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 203, 128, 77, south_light_state[1]) # Orange
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # red light
        y_pos = y_pos - light_gap - light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 201, 79, 79, south_light_state[2])  # Red
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)

        # North traffic light
        x_pos, y_pos = cx + half_rd_width + gap_to_mid_sq, cy - half_rd_width - pole_length - gap_to_mid_sq
        sdl3.SDL_SetRenderDrawColor(renderer, 38, 40, 43, 255)  # Dark Grey
        draw_rectangle(renderer, x_pos, y_pos, pole_thickness, pole_length, camera_x, camera_y, zoom)
            # green light
        x_pos, y_pos = x_pos + light_gap + light_radius, y_pos + light_gap + light_radius
        sdl3.SDL_SetRenderDrawColor(renderer, 87, 150, 92, north_light_state[0])  # Green
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # orange light
        y_pos = y_pos + light_gap + light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 203, 128, 77, north_light_state[1]) # Orange
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)
            # red light
        y_pos = y_pos + light_gap + light_radius*2
        sdl3.SDL_SetRenderDrawColor(renderer, 201, 79, 79, north_light_state[2])  # Red
        draw_circle(renderer, x_pos, y_pos, light_radius, camera_x, camera_y, zoom)


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
        # Drawing traffic lights
        current_light_state = [[255, 75, 75],[255, 75, 75],[255, 75, 75],[255, 75, 75]]
        draw_traffic_lights(renderer, camera_x, camera_y, zoom, current_light_state)

        # # Testing drawing a circle
        # draw_circle(renderer, 300, 300, 50, camera_x, camera_y, zoom)
        # sdl3.SDL_SetRenderDrawColor(renderer, 20, 20, 200, 255)
        # draw_circle(renderer, cx+100, cy+100, 95, camera_x, camera_y, zoom)

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