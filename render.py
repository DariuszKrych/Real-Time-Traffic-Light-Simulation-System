import ctypes
import sdl3
import math


def create_window():
    sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

    window_dimensions = [1920, 1080]
    #window_dimensions = [1280,720]
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

    def draw_inside_points(renderer, coordinates_list, camera_x, camera_y, zoom):
        # Transform world coordinates to screen space
        screen_coords = []
        for p in coordinates_list:
            screen_x = (p[0] - camera_x) * zoom
            screen_y = (p[1] - camera_y) * zoom
            screen_coords.append((screen_x, screen_y))

        # Find the minimum and maximum Y coordinates to limit our scanlines
        min_y = min(p[1] for p in screen_coords)
        max_y = max(p[1] for p in screen_coords)

        n = len(screen_coords)

        # Sweep a horizontal line from the top to the bottom of the polygon
        for y in range(int(min_y), int(max_y) + 1):
            intersections = []
            j = n - 1  # The last vertex

            for i in range(n):
                p_i = screen_coords[i]
                p_j = screen_coords[j]

                # Check if the current scanline (y) crosses the edge between p_i and p_j
                # We use < on one side and >= on the other to prevent double-counting vertices
                if (p_i[1] < y and p_j[1] >= y) or (p_j[1] < y and p_i[1] >= y):
                    # Calculate the exact X coordinate of the intersection using linear interpolation
                    x = p_i[0] + (y - p_i[1]) / (p_j[1] - p_i[1]) * (p_j[0] - p_i[0])
                    intersections.append(x)

                j = i  # Move to the next edge

            # Sort the X intersections from left to right
            intersections.sort()

            # Draw horizontal lines between pairs of intersections
            # Step by 2 (e.g., from intersection 0 to 1, then 2 to 3, etc.)
            for i in range(0, len(intersections), 2):
                if i + 1 < len(intersections):
                    x1 = float(intersections[i])
                    x2 = float(intersections[i + 1])

                    # Draw the horizontal line filling that part of the polygon.
                    # In SDL3, SDL_RenderLine expects floats.
                    sdl3.SDL_RenderLine(renderer, x1, float(y), x2, float(y))


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

    def draw_traffic_lights(renderer, camera_x, camera_y, zoom,  light_states):
        pole_length, pole_thickness, gap_to_mid_sq, light_radius, light_gap = 130, 50, 30, 15, 10
        half_rd_width = road_width / 2

        current_light_states = []
        for light_state in light_states:
            match light_state:
                case "green":
                    alpha_values = [255, 75, 75]
                case "orange":
                    alpha_values = [75, 255, 75]
                case "red":
                    alpha_values = [75, 75, 255]
                case _:
                    raise ValueError(f"Unknown color, please input 'green', 'orange' or 'red'.")
            current_light_states.append(alpha_values)

        west_light_state = current_light_states[0]
        east_light_state = current_light_states[1]
        south_light_state = current_light_states[2]
        north_light_state = current_light_states[3]

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

    def draw_car(renderer, camera_x, camera_y, zoom, car_x_pos, car_y_pos, car_rotation, car_rgba_colour):
        car_body = [
            [4, 99], [4, 103], [6, 113], [8, 120], [11, 126], [15, 129],
            [17, 132], [18, 134], [20, 136], [24, 136], [30, 137], [53, 137],
            [56, 136], [58, 136], [125, 136], [127, 137], [158, 137], [161, 136],
            [163, 135], [165, 133], [168, 131], [170, 129], [173, 127], [176, 125],
            [177, 120], [178, 115], [178, 109], [178, 99], [178, 88], [178, 82],
            [177, 77], [176, 73], [173, 70], [170, 68], [168, 67], [165, 65],
            [163, 63], [161, 62], [158, 61], [127, 60], [125, 62], [58, 62],
            [56, 61], [53, 61], [30, 61], [24, 61], [20, 62], [18, 64],
            [17, 66], [15, 68], [11, 72], [8, 77], [6, 85], [4, 94]
        ]
        headlight_front_right = [
            [11, 80], [28, 75], [32, 68], [18, 69], [17, 70],
            [15, 72], [13, 74], [12, 76], [11, 78]
        ]
        headlight_front_left = [
            [11, 118], [28, 122], [32, 130], [18, 129], [17, 128],
            [15, 126], [13, 124], [12, 122], [11, 120]
        ]
        window_front = [
            [58, 95], [58, 86], [60, 79], [64, 70], [66, 69],
            [86, 75], [87, 76], [86, 80], [85, 85], [84, 90], [84, 96],
            [84, 102], [84, 107], [85, 112], [86, 117], [87, 122],
            [86, 122], [66, 129], [64, 127], [60, 119], [58, 111], [58, 103]
        ]
        window_right = [
            [72, 67], [90, 73], [93, 74], [96, 74],
            [130, 72], [132, 71], [132, 69], [116, 68]
        ]
        window_left = [
            [72, 131], [90, 124], [93, 124], [96, 124],
            [130, 126], [132, 126], [132, 128], [116, 130]
        ]
        window_rear = [
            [124, 80], [125, 79], [149, 79], [151, 79], [152, 81],
            [153, 84], [154, 89], [154, 93], [155, 97],
            [155, 101], [154, 104], [154, 109], [153, 113], [152, 117],
            [151, 118], [149, 118], [125, 118], [124, 118]
        ]
        brakelight_right = [
            [160, 73], [161, 70], [168, 70], [170, 72], [171, 72],
            [172, 74], [174, 80], [172, 78], [170, 76], [166, 75], [163, 73]
        ]
        brakelight_left = [
            [160, 125], [161, 128], [168, 127], [170, 126], [171, 125],
            [172, 123], [174, 118], [172, 120], [170, 121], [166, 123], [163, 124]
        ]

        # Internal helper to apply rotation and translation
        def transform_car_points(points_list):
            # The center of the car body polygon coordinates
            local_center_x, local_center_y = 90.8, 98.8

            # Convert degrees to radians for the math functions
            rotation_radians = math.radians(car_rotation)
            cos_angle = math.cos(rotation_radians)
            sin_angle = math.sin(rotation_radians)

            transformed_points = []
            for point in points_list:
                # 1. Shift the point so the car's local center acts as (0, 0)
                origin_x = point[0] - local_center_x
                origin_y = point[1] - local_center_y

                # 2. Rotate the point around the origin
                rotated_x = origin_x * cos_angle - origin_y * sin_angle
                rotated_y = origin_x * sin_angle + origin_y * cos_angle

                # 3. Translate the point to the desired world position
                final_x = rotated_x + car_x_pos + cx
                final_y = rotated_y + car_y_pos + cy

                transformed_points.append([final_x, final_y])

            return transformed_points

        # Apply transformations to all parts of the car
        transformed_car_body = transform_car_points(car_body)
        transformed_headlight_right = transform_car_points(headlight_front_right)
        transformed_headlight_left = transform_car_points(headlight_front_left)
        transformed_window_front = transform_car_points(window_front)
        transformed_window_right = transform_car_points(window_right)
        transformed_window_left = transform_car_points(window_left)
        transformed_window_rear = transform_car_points(window_rear)
        transformed_brakelight_right = transform_car_points(brakelight_right)
        transformed_brakelight_left = transform_car_points(brakelight_left)

        # Draw the car body
        sdl3.SDL_SetRenderDrawColor(renderer, car_rgba_colour[0], car_rgba_colour[1], car_rgba_colour[2], car_rgba_colour[3])
        draw_inside_points(renderer, transformed_car_body, camera_x, camera_y, zoom)

        # Draw the headlights
        sdl3.SDL_SetRenderDrawColor(renderer, 240, 211, 101, 255)  # Yellow
        draw_inside_points(renderer, transformed_headlight_right, camera_x, camera_y, zoom)
        draw_inside_points(renderer, transformed_headlight_left, camera_x, camera_y, zoom)

        # Draw the windows
        sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)  # Black
        draw_inside_points(renderer, transformed_window_front, camera_x, camera_y, zoom)
        draw_inside_points(renderer, transformed_window_right, camera_x, camera_y, zoom)
        draw_inside_points(renderer, transformed_window_left, camera_x, camera_y, zoom)
        draw_inside_points(renderer, transformed_window_rear, camera_x, camera_y, zoom)

        # Draw the brakelights
        sdl3.SDL_SetRenderDrawColor(renderer, 201, 79, 79, 255)  # Red
        draw_inside_points(renderer, transformed_brakelight_right, camera_x, camera_y, zoom)
        draw_inside_points(renderer, transformed_brakelight_left, camera_x, camera_y, zoom)



    # ---- main drawing function (returned) ----
    def draw_scene(renderer, camera_x, camera_y, zoom, current_light_state, current_cars):
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
        draw_traffic_lights(renderer, camera_x, camera_y, zoom, current_light_state)
        # Draw cars
        for car in current_cars:
            draw_car(renderer, camera_x, camera_y, zoom, car[0], car[1], car[2], car[3])

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