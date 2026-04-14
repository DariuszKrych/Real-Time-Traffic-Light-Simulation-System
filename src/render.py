import ctypes
import sdl3
import math


def create_window():
    sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

    #window_dimensions = [1920, 1080]
    window_dimensions = [1280,720]
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

    def draw_car(renderer, camera_x, camera_y, zoom, car_body_type, car_x_pos, car_y_pos, car_rotation, car_rgba_colour):
        # Car switch statement for Nathan to add cars to.
        match car_body_type:
            case 'car_body_1':
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
                    [11, 80], [28, 75], [32, 68], [18, 69], [17, 70], [15, 72], [13, 74], [12, 76], [11, 78]
                ]
                headlight_front_left = [
                    [11, 118], [28, 122], [32, 130], [18, 129], [17, 128], [15, 126], [13, 124], [12, 122], [11, 120]
                ]
                window_front = [
                    [58, 95], [58, 86], [60, 79], [64, 70], [66, 69], [86, 75], [87, 76], [86, 80], [85, 85], [84, 90],
                    [84, 96], [84, 102], [84, 107], [85, 112], [86, 117], [87, 122], [86, 122], [66, 129], [64, 127],
                    [60, 119], [58, 111], [58, 103]
                ]
                window_right = [
                    [72, 67], [90, 73], [93, 74], [96, 74], [130, 72], [132, 71], [132, 69], [116, 68]
                ]
                window_left = [
                    [72, 131], [90, 124], [93, 124], [96, 124], [130, 126], [132, 126], [132, 128], [116, 130]
                ]
                window_rear = [
                    [124, 80], [125, 79], [149, 79], [151, 79], [152, 81], [153, 84], [154, 89], [154, 93], [155, 97],
                    [155, 101], [154, 104], [154, 109], [153, 113], [152, 117], [151, 118], [149, 118], [125, 118], [124, 118]
                ]
                brakelight_right = [
                    [160, 73], [161, 70], [168, 70], [170, 72], [171, 72],
                    [172, 74], [174, 80], [172, 78], [170, 76], [166, 75], [163, 73]
                ]
                brakelight_left = [
                    [160, 125], [161, 128], [168, 127], [170, 126], [171, 125],
                    [172, 123], [174, 118], [172, 120], [170, 121], [166, 123], [163, 124]
                ]
                # The center of the car body polygon coordinates
                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_2':
                car_body = [
                    [3, 99],
                    [3, 87], [4, 72], [5, 71], [5, 70], [6, 69],
                    [18, 66], [29, 65], [51, 64], [75, 64],
                    [132, 64], [150, 65], [165, 66],
                    [175, 67], [177, 68], [178, 70], [178, 84],
                    [178, 99],
                    [178, 113], [178, 128], [177, 129], [175, 130],
                    [165, 131], [150, 133], [132, 133],
                    [75, 133], [51, 134], [29, 133], [18, 131],
                    [6, 128], [5, 128], [5, 126], [4, 125], [3, 110]
                ]
                headlight_front_right = [
                    [8, 72], [7, 83], [15, 83], [15, 83],
                    [16, 82], [16, 80], [16, 71]
                ]
                headlight_front_left = [
                    [8, 126], [7, 115], [15, 115], [15, 115],
                    [16, 116], [16, 118], [16, 127]
                ]
                window_front = [
                    [55, 99],
                    [55, 91], [56, 84], [57, 78], [58, 74], [59, 71], [61, 69],
                    [70, 72], [77, 74], [84, 77],
                    [83, 82], [83, 90], [82, 96],
                    [82, 99],
                    [82, 102], [83, 108], [83, 116],
                    [84, 121], [77, 124], [70, 126],
                    [61, 129], [59, 127], [58, 124], [57, 120], [56, 114], [55, 107]
                ]
                window_right = [
                    [68, 67], [72, 68], [88, 74], [94, 75],
                    [108, 75], [111, 68]
                ]
                window_left = [
                    [68, 131], [72, 130], [88, 124], [94, 123],
                    [108, 123], [111, 130]
                ]
                window_rear = [
                    [133, 78], [162, 74], [162, 80], [163, 92],
                    [163, 106], [162, 118], [162, 124], [133, 120],
                    [133, 109], [134, 99], [133, 89]
                ]
                brakelight_right = [
                    [169, 69], [171, 68], [172, 69], [174, 69],
                    [174, 71], [175, 76], [175, 80], [176, 89],
                    [176, 91], [170, 91]
                ]
                brakelight_left = [
                    [169, 129], [171, 130], [172, 129], [174, 129],
                    [174, 127], [175, 122], [175, 118], [176, 109],
                    [176, 107], [170, 107]
                ]
                # The center of the car body polygon coordinates
                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_3':
                car_body = [
                    [23, 75], [33, 73], [53, 73], [61, 75], [66, 75], [72, 71],
                    [74, 71], [72, 75], [100, 75], [103, 73], [108, 74], [109, 75],
                    [125, 75], [132, 73], [142, 72], [155, 73], [167, 77], [171, 83],
                    [175, 91], [177, 104], [178, 113], [177, 120], [175, 131], [171, 137],
                    [166, 142], [160, 144], [152, 146], [145, 147], [138, 147], [131, 145],
                    [127, 144], [117, 144], [109, 144], [107, 145], [101, 145], [100, 144],
                    [72, 143], [74, 148], [72, 148], [66, 144], [61, 145], [58, 146],
                    [51, 147], [43, 147], [35, 147], [30, 146], [24, 145], [20, 142],
                    [15, 137], [11, 134], [9, 131], [7, 127], [5, 120], [4, 111],
                    [5, 97], [10, 87], [13, 83]
                ]
                headlight_front_right = [
                    [26, 74], [24, 78], [23, 79], [9, 91], [11, 87], [13, 84], [19, 79], [27, 74], [26, 74]
                ]
                headlight_front_left = [
                    [26, 147], [24, 143], [23, 142], [9, 130], [11, 134], [13, 137], [19, 142], [27, 148], [26, 147]
                ]
                window_front = [
                    [82, 87], [58, 81], [55, 90], [53, 102], [53, 116], [53, 118], [55, 129], [55, 131],
                    [58, 140], [82, 134], [80, 119], [80, 109], [81, 94], [82, 87]
                ]
                window_right = [
                    [110, 80], [112, 85], [90, 84], [82, 82], [71, 80], [72, 79], [110, 80]
                ]
                window_left = [
                    [110, 142], [112, 136], [90, 138], [82, 140], [71, 142], [72, 143], [110, 142]
                ]
                window_rear = [
                    [141, 134], [158, 138], [163, 125], [164, 112], [164, 106], [163, 98], [162, 93], [158, 83],
                    [141, 87], [144, 96], [145, 104], [145, 112], [144, 121], [143, 128], [141, 134]
                ]
                brakelight_right = [
                    [175, 129], [174, 134], [172, 138], [166, 140], [166, 140], [172, 134], [174, 130], [175, 129]
                ]
                brakelight_left = [
                    [175, 91], [174, 86], [172, 82], [166, 80], [166, 80], [172, 86], [174, 90], [175, 91]
                ]
                # Adjusted local center based on the new scale
                local_center_x, local_center_y = 91.0, 109.5

            case 'car_body_4':
                car_body = [
                    [49, 62], [22, 62], [14, 63], [9, 71], [6, 77], [5, 86],
                    [4, 104], [5, 112], [7, 116], [12, 126], [14, 127], [21, 129],
                    [48, 129], [51, 129], [48, 128], [100, 129], [120, 129], [127, 130],
                    [149, 130], [171, 125], [174, 122], [178, 113], [178, 97], [177, 79],
                    [175, 71], [172, 67], [153, 61], [145, 61], [126, 61], [120, 62],
                    [48, 62], [49, 61], [49, 62]
                ]
                headlight_front_right = [
                    [24, 64], [18, 68], [12, 74], [12, 73], [16, 67],
                    [18, 65], [22, 64], [24, 64]
                ]
                headlight_front_left = [
                    [24, 129], [18, 125], [12, 119], [12, 120], [16, 126],
                    [18, 128], [22, 129], [24, 129]
                ]
                window_front = [
                    [79, 75], [65, 71], [62, 71], [60, 73], [58, 81], [57, 92],
                    [57, 100], [58, 111], [60, 117], [62, 119], [79, 115], [79, 112],
                    [78, 103], [78, 86], [79, 79], [80, 75], [79, 75]
                ]
                window_right = [
                    [71, 66], [98, 66], [121, 67], [143, 69], [147, 71],
                    [127, 73], [104, 74], [88, 73], [76, 71], [72, 69], [70, 66]
                ]
                window_left = [
                    [71, 127], [98, 128], [121, 126], [143, 125], [147, 123],
                    [127, 121], [104, 120], [88, 121], [76, 123], [72, 125], [70, 127]
                ]
                window_rear = [
                    [134, 76], [156, 76], [159, 78], [160, 87], [161, 96],
                    [160, 104], [159, 112], [155, 115], [134, 114], [134, 113],
                    [134, 110], [134, 105], [135, 99], [135, 93], [135, 87],
                    [134, 80], [133, 79], [134, 77], [134, 76]
                ]
                brakelight_right = [
                    [161, 66], [166, 69], [170, 74], [173, 78], [170, 70],
                    [168, 68], [165, 66], [161, 66]
                ]
                brakelight_left = [
                    [161, 127], [166, 124], [170, 120], [173, 116], [170, 123],
                    [168, 126], [165, 127], [161, 127]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_5':
                car_body = [
                    [48, 56], [29, 56], [21, 58], [15, 59], [9, 66], [7, 71],
                    [4, 81], [3, 86], [5, 86], [6, 111], [3, 112], [8, 130],
                    [12, 136], [18, 140], [23, 140], [31, 141], [44, 142], [54, 141],
                    [133, 141], [159, 142], [166, 141], [173, 137], [176, 134], [178, 118],
                    [179, 94], [177, 75], [174, 61], [167, 57], [139, 56], [53, 58],
                    [51, 56], [48, 56]
                ]

                headlight_front_right = [
                    [37, 61], [33, 60], [28, 60], [24, 61], [20, 63], [16, 67],
                    [16, 71], [15, 73], [13, 84], [15, 79], [18, 76], [21, 75], [37, 61]
                ]
                headlight_front_left = [
                    [37, 137], [33, 138], [28, 138], [24, 137], [20, 135], [16, 131],
                    [16, 127], [15, 125], [13, 114], [15, 119], [18, 122], [21, 123], [37, 137]
                ]

                window_front = [
                    [81, 125], [80, 116], [79, 111], [76, 105], [77, 92], [79, 88],
                    [81, 72], [79, 70], [51, 66], [46, 65], [43, 67], [41, 71],
                    [39, 80], [38, 89], [39, 108], [39, 116], [41, 124], [42, 128],
                    [44, 130], [46, 131], [51, 131], [80, 126], [80, 125], [81, 125]
                ]
                window_right = [
                    [64, 60], [66, 62], [70, 64], [83, 67], [97, 67],
                    [116, 68], [115, 65], [113, 61], [64, 60]
                ]
                window_left = [
                    [64, 138], [66, 136], [70, 134], [83, 131], [97, 131],
                    [116, 130], [115, 133], [113, 137], [64, 138]
                ]
                window_rear = [
                    [160, 78], [160, 85], [160, 105], [160, 120], [160, 122],
                    [162, 124], [168, 125], [170, 121], [171, 110], [171, 83],
                    [170, 76], [169, 74], [164, 75], [161, 76], [160, 78]
                ]

                brakelight_right = [
                    [158, 67], [160, 61], [162, 61], [168, 62], [170, 64],
                    [171, 67], [171, 69], [167, 69], [162, 71], [158, 72], [158, 67]
                ]
                brakelight_left = [
                    [158, 131], [160, 137], [162, 137], [168, 136], [170, 134],
                    [171, 131], [171, 129], [167, 129], [162, 127], [158, 126], [158, 131]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_6':
                car_body = [
                    [49, 63], [33, 63], [24, 64], [9, 67], [8, 68], [7, 71],
                    [7, 75], [6, 81], [5, 86], [4, 96], [4, 100], [4, 103],
                    [5, 110], [6, 117], [7, 126], [8, 130], [9, 131], [11, 132],
                    [18, 133], [22, 134], [50, 134], [62, 134], [99, 135], [139, 135],
                    [165, 135], [169, 134], [175, 132], [178, 130], [178, 68], [176, 66],
                    [171, 64], [164, 63], [97, 63], [49, 63]
                ]

                headlight_front_right = [
                    [24, 70], [24, 67], [21, 67], [17, 68], [14, 71], [13, 72],
                    [13, 73], [18, 72], [22, 72], [24, 71], [24, 70]
                ]
                headlight_front_left = [
                    [24, 127], [24, 130], [21, 130], [17, 129], [14, 126], [13, 125],
                    [13, 124], [18, 125], [22, 125], [24, 126], [24, 127]
                ]

                window_front = [
                    [80, 75], [55, 71], [53, 71], [51, 73], [48, 83],
                    [47, 95], [48, 108], [48, 116], [51, 124], [54, 127],
                    [80, 122], [79, 102], [79, 83], [80, 75]
                ]
                window_right = [
                    [65, 68], [66, 70], [85, 73], [98, 73], [123, 73],
                    [129, 71], [129, 68], [95, 68], [65, 68]
                ]
                window_left = [
                    [65, 129], [66, 127], [85, 124], [98, 124], [123, 124],
                    [129, 126], [129, 129], [95, 129], [65, 129]
                ]
                window_rear = [
                    [137, 75], [137, 122], [149, 122], [169, 124], [170, 123],
                    [170, 75], [169, 74], [137, 75]
                ]

                brakelight_right = [
                    [167, 68], [170, 70], [173, 73], [171, 73], [171, 74],
                    [175, 74], [175, 69], [174, 67], [172, 66], [167, 66], [167, 68]
                ]
                brakelight_left = [
                    [167, 129], [170, 127], [173, 124], [171, 124], [171, 123],
                    [175, 123], [175, 128], [174, 130], [172, 131], [167, 131], [167, 129]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_7':
                car_body = [
                    [50, 67], [30, 67], [26, 68], [21, 68], [15, 70], [12, 72],
                    [9, 75], [7, 80], [5, 88], [4, 95], [4, 103], [5, 110],
                    [7, 117], [9, 122], [12, 126], [15, 128], [21, 130], [26, 130],
                    [30, 131], [51, 131], [74, 131], [108, 131], [128, 131], [148, 130],
                    [155, 129], [164, 128], [170, 127], [173, 125], [175, 121], [176, 115],
                    [177, 108], [177, 94], [176, 84], [176, 79], [174, 74], [171, 71],
                    [167, 70], [157, 68], [149, 67], [50, 67]
                ]

                headlight_front_right = [
                    [20, 70], [18, 71], [16, 72], [14, 74], [12, 77], [10, 83],
                    [8, 92], [10, 85], [12, 81], [12, 77], [15, 74], [20, 70]
                ]
                headlight_front_left = [
                    [20, 127], [18, 126], [16, 125], [14, 123], [12, 120], [10, 114],
                    [8, 105], [10, 112], [12, 116], [12, 120], [15, 123], [20, 127]
                ]

                window_front = [
                    [60, 72], [80, 77], [81, 78], [81, 81], [80, 87],
                    [79, 95], [79, 102], [80, 110], [81, 117], [80, 119],
                    [79, 120], [74, 122], [60, 126], [57, 123], [55, 118],
                    [54, 112], [53, 102], [53, 99], [53, 94], [53, 89],
                    [54, 82], [56, 78], [57, 75], [60, 73], [60, 72]
                ]
                window_right = [
                    [69, 72], [80, 75], [85, 77], [99, 78], [112, 77],
                    [119, 77], [127, 74], [132, 72], [132, 71], [101, 71],
                    [87, 71], [70, 71], [69, 72]
                ]
                window_left = [
                    [69, 125], [80, 122], [85, 120], [99, 119], [112, 120],
                    [119, 120], [127, 123], [132, 125], [132, 126], [101, 126],
                    [87, 126], [70, 126], [69, 125]
                ]
                window_rear = [
                    [129, 79], [130, 83], [131, 87], [131, 94], [131, 101],
                    [131, 109], [130, 115], [129, 118], [130, 118], [135, 120],
                    [143, 122], [147, 121], [150, 118], [152, 115], [154, 110],
                    [154, 103], [154, 96], [154, 90], [154, 86], [152, 83],
                    [150, 80], [148, 77], [146, 76], [143, 75], [129, 79]
                ]
                brakelight_right = [
                    [168, 75], [163, 75], [163, 84], [168, 83], [168, 75]
                ]
                brakelight_left = [
                    [168, 122], [163, 122], [163, 113], [168, 114], [168, 122]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_8':
                car_body = [
                    [47, 66], [30, 67], [26, 67], [19, 70], [13, 74], [8, 82],
                    [6, 88], [6, 96], [5, 106], [6, 112], [7, 116], [11, 122],
                    [15, 126], [19, 128], [24, 130], [29, 131], [38, 131], [51, 132],
                    [62, 132], [83, 132], [97, 132], [119, 132], [134, 132], [147, 131],
                    [154, 130], [163, 128], [170, 125], [173, 120], [174, 118], [175, 111],
                    [175, 100], [175, 89], [174, 82], [172, 76], [169, 73], [163, 71],
                    [155, 69], [145, 68], [93, 66], [47, 66]
                ]

                headlight_front_right = [
                    [25, 71], [21, 72], [15, 74], [11, 78], [9, 84],
                    [8, 84], [11, 82], [12, 80], [15, 77], [22, 73], [25, 71]
                ]
                headlight_front_left = [
                    [25, 127], [21, 126], [15, 124], [11, 120], [9, 114],
                    [8, 114], [11, 116], [12, 118], [15, 121], [22, 125], [25, 127]
                ]

                window_front = [
                    [56, 74], [62, 75], [73, 77], [75, 78], [76, 79],
                    [75, 81], [74, 90], [73, 97], [74, 104], [74, 110],
                    [75, 117], [76, 120], [75, 120], [70, 122], [61, 123],
                    [55, 124], [54, 124], [53, 121], [52, 119], [51, 113],
                    [51, 106], [50, 100], [50, 95], [51, 90], [51, 83],
                    [53, 78], [53, 76], [54, 75], [56, 74]
                ]
                window_right = [
                    [64, 71], [65, 73], [75, 75], [89, 77], [101, 77],
                    [115, 76], [122, 76], [134, 74], [133, 73], [98, 71],
                    [91, 71], [64, 71], [64, 71]
                ]
                window_left = [
                    [64, 127], [65, 125], [75, 123], [89, 121], [101, 121],
                    [115, 122], [122, 122], [134, 124], [133, 125], [98, 127],
                    [91, 127], [64, 127], [64, 127]
                ]
                window_rear = [
                    [138, 77], [139, 121], [159, 122], [162, 117], [163, 111],
                    [164, 105], [164, 97], [164, 90], [164, 86], [162, 80],
                    [160, 76], [139, 77], [138, 77]
                ]

                brakelight_right = [
                    [157, 72], [158, 70], [164, 72], [167, 74], [169, 77],
                    [171, 80], [172, 85], [172, 88], [170, 84], [168, 79],
                    [166, 76], [164, 74], [157, 72]
                ]
                brakelight_left = [
                    [157, 126], [158, 128], [164, 126], [167, 124], [169, 121],
                    [171, 118], [172, 113], [172, 110], [170, 114], [168, 119],
                    [166, 122], [164, 124], [157, 126]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_9':
                car_body = [
                    [52, 59], [23, 59], [18, 61], [13, 64], [8, 72], [6, 80],
                    [5, 91], [5, 105], [6, 117], [7, 123], [9, 128], [11, 133],
                    [17, 137], [22, 139], [28, 139], [41, 139], [55, 139], [62, 140],
                    [76, 140], [125, 140], [147, 140], [167, 139], [168, 137], [170, 135],
                    [174, 128], [176, 114], [176, 105], [176, 90], [174, 75], [172, 65],
                    [170, 63], [169, 62], [166, 59], [150, 59], [125, 59], [93, 59],
                    [67, 59], [52, 59]
                ]

                headlight_front_right = [
                    [20, 63], [25, 65], [26, 67], [25, 68], [22, 72], [15, 77],
                    [11, 78], [9, 80], [10, 77], [11, 73], [14, 67], [16, 65], [20, 63]
                ]
                headlight_front_left = [
                    [20, 135], [25, 133], [26, 131], [25, 130], [22, 126], [15, 121],
                    [11, 120], [9, 118], [10, 121], [11, 125], [14, 131], [16, 133], [20, 135]
                ]

                window_front = [
                    [81, 74], [50, 68], [48, 73], [47, 80], [47, 84],
                    [46, 92], [46, 100], [46, 107], [46, 114], [47, 120],
                    [49, 128], [50, 131], [82, 123], [81, 113], [80, 100],
                    [80, 87], [81, 79], [81, 74]
                ]

                window_right = [
                    [68, 64], [101, 64], [121, 64], [138, 64], [145, 66],
                    [146, 68], [138, 69], [109, 70], [103, 70], [86, 69],
                    [74, 67], [68, 64]
                ]
                window_left = [
                    [68, 134], [101, 134], [121, 134], [138, 134], [145, 132],
                    [146, 130], [138, 129], [109, 128], [103, 128], [86, 129],
                    [74, 131], [68, 134]
                ]

                window_rear = [
                    [165, 70], [163, 70], [161, 71], [160, 75], [159, 78],
                    [160, 84], [161, 94], [162, 104], [161, 111], [160, 121],
                    [160, 126], [162, 128], [165, 128], [167, 124], [170, 114],
                    [171, 107], [171, 97], [171, 88], [169, 78], [166, 73], [165, 70]
                ]

                brakelight_right = [
                    [164, 64], [160, 64], [160, 63], [160, 62], [163, 62],
                    [165, 63], [169, 65], [170, 70], [171, 73], [170, 72],
                    [167, 68], [166, 65], [165, 64], [163, 64], [164, 64]
                ]
                brakelight_left = [
                    [164, 134], [160, 134], [160, 135], [160, 136], [163, 136],
                    [165, 135], [169, 133], [170, 128], [171, 125], [170, 126],
                    [167, 130], [166, 133], [165, 134], [163, 134], [164, 134]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_10':
                car_body = [
                    [57, 61], [27, 61], [22, 62], [18, 66], [12, 73], [12, 76],
                    [9, 83], [9, 92], [8, 107], [9, 114], [12, 120], [12, 123],
                    [19, 133], [24, 136], [45, 137], [55, 136], [161, 136], [167, 135],
                    [171, 131], [174, 125], [174, 116], [175, 97], [175, 82], [174, 76],
                    [172, 70], [170, 65], [166, 63], [163, 61], [57, 61]
                ]

                headlight_front_right = [
                    [25, 68], [21, 67], [22, 70], [16, 78], [24, 70], [25, 68]
                ]
                headlight_front_left = [
                    [25, 130], [21, 131], [22, 128], [16, 120], [24, 128], [25, 130]
                ]

                window_front = [
                    [79, 74], [62, 71], [58, 72], [55, 76], [53, 86],
                    [51, 97], [53, 108], [54, 117], [57, 123], [60, 125],
                    [79, 122], [78, 117], [76, 112], [75, 103], [75, 94],
                    [76, 89], [77, 78], [79, 74]
                ]

                window_right = [
                    [74, 66], [71, 67], [71, 68], [83, 72], [103, 73],
                    [123, 74], [137, 73], [144, 68], [110, 67], [95, 67],
                    [74, 66]
                ]
                window_left = [
                    [74, 132], [71, 131], [71, 130], [83, 126], [103, 125],
                    [123, 124], [137, 125], [144, 130], [110, 131], [95, 131],
                    [74, 132]
                ]

                window_rear = [
                    [160, 77], [152, 79], [152, 80], [154, 92], [153, 108],
                    [152, 117], [155, 119], [160, 119], [161, 119], [162, 108],
                    [162, 89], [161, 81], [160, 77]
                ]

                brakelight_right = [
                    [166, 68], [162, 65], [159, 66], [152, 71], [154, 72],
                    [157, 74], [168, 73], [166, 68]
                ]
                brakelight_left = [
                    [166, 130], [162, 133], [159, 132], [152, 127], [154, 126],
                    [157, 124], [168, 125], [166, 130]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_11':
                car_body = [
                    [53, 65], [39, 65], [24, 65], [17, 67], [13, 71], [9, 76],
                    [7, 78], [6, 84], [6, 95], [6, 103], [6, 111], [6, 118],
                    [6, 119], [10, 123], [15, 128], [16, 129], [21, 131], [32, 132],
                    [45, 132], [57, 132], [77, 133], [102, 132], [116, 132], [125, 132],
                    [131, 133], [141, 133], [151, 132], [158, 131], [168, 128], [172, 126],
                    [175, 122], [175, 115], [176, 101], [176, 93], [176, 83], [175, 76],
                    [174, 75], [171, 72], [168, 70], [162, 68], [154, 65], [134, 65],
                    [120, 65], [92, 65], [53, 65]
                ]

                headlight_front_right = [
                    [27, 70], [22, 69], [20, 69], [15, 73], [11, 78],
                    [9, 82], [8, 84], [10, 82], [12, 80], [15, 77],
                    [18, 74], [22, 72], [27, 71], [30, 70], [27, 70]
                ]
                headlight_front_left = [
                    [27, 128], [22, 129], [20, 129], [15, 125], [11, 120],
                    [9, 116], [8, 114], [10, 116], [12, 118], [15, 121],
                    [18, 124], [22, 126], [27, 127], [30, 128], [27, 128]
                ]

                window_front = [
                    [79, 78], [60, 74], [58, 74], [55, 78], [54, 84],
                    [52, 92], [52, 100], [52, 111], [53, 116], [56, 123],
                    [59, 125], [79, 120], [79, 110], [78, 104], [78, 103],
                    [78, 90], [79, 79], [79, 78]
                ]

                window_right = [
                    [60, 70], [74, 73], [85, 76], [98, 76], [131, 77],
                    [135, 77], [147, 73], [147, 72], [145, 71], [120, 70],
                    [100, 69], [88, 69], [73, 69], [60, 70]
                ]
                window_left = [
                    [60, 128], [74, 125], [85, 122], [98, 122], [131, 121],
                    [135, 121], [147, 125], [147, 126], [145, 127], [120, 128],
                    [100, 129], [88, 129], [73, 129], [60, 128]
                ]

                window_rear = [
                    [167, 78], [167, 77], [161, 79], [160, 79], [161, 80],
                    [161, 85], [162, 99], [161, 116], [161, 118], [159, 119],
                    [167, 121], [168, 119], [170, 112], [171, 106], [171, 102],
                    [171, 95], [170, 87], [170, 84], [169, 80], [167, 78]
                ]

                brakelight_right = [
                    [172, 85], [171, 74], [168, 70], [154, 66], [157, 68],
                    [163, 69], [168, 72], [171, 77], [173, 84], [172, 85]
                ]
                brakelight_left = [
                    [172, 113], [171, 124], [168, 128], [154, 132], [157, 130],
                    [163, 129], [168, 126], [171, 121], [173, 114], [172, 113]
                ]

                local_center_x, local_center_y = 90.8, 98.8
            case 'car_body_12':
                car_body = [
                    [47, 65], [31, 65], [23, 67], [15, 68], [11, 73], [9, 78],
                    [7, 86], [6, 93], [6, 100], [6, 107], [7, 112], [8, 117],
                    [10, 124], [13, 127], [17, 130], [21, 131], [30, 133], [37, 133],
                    [44, 133], [51, 132], [52, 132], [56, 133], [67, 133], [98, 133],
                    [135, 133], [149, 132], [164, 130], [169, 129], [172, 126], [174, 122],
                    [175, 115], [176, 108], [176, 103], [176, 93], [175, 86], [174, 80],
                    [173, 73], [171, 70], [168, 69], [161, 68], [152, 66], [144, 65],
                    [135, 65], [125, 65], [58, 65], [51, 66], [47, 65]
                ]

                headlight_front_right = [
                    [20, 70], [19, 69], [16, 70], [14, 72], [12, 75],
                    [11, 79], [10, 81], [10, 82], [11, 81], [12, 80],
                    [15, 75], [18, 71], [20, 70]
                ]
                headlight_front_left = [
                    [20, 128], [19, 129], [16, 128], [14, 126], [12, 123],
                    [11, 119], [10, 117], [10, 116], [11, 117], [12, 118],
                    [15, 123], [18, 127], [20, 128]
                ]

                window_front = [
                    [79, 78], [70, 75], [60, 72], [59, 71], [56, 72],
                    [54, 75], [51, 81], [50, 86], [49, 90], [50, 96],
                    [49, 101], [49, 107], [50, 112], [51, 117], [52, 121],
                    [54, 125], [57, 127], [63, 126], [75, 122], [79, 120],
                    [79, 117], [78, 115], [77, 108], [76, 100], [77, 92],
                    [77, 88], [79, 78]
                ]

                window_right = [
                    [63, 70], [74, 73], [83, 76], [90, 76], [104, 77],
                    [123, 76], [126, 75], [135, 72], [139, 70], [139, 69],
                    [63, 69]
                ]
                window_left = [
                    [63, 128], [74, 125], [83, 122], [90, 122], [104, 121],
                    [123, 122], [126, 123], [135, 126], [139, 128], [139, 129],
                    [63, 128]
                ]

                window_rear = [
                    [150, 75], [130, 80], [130, 118], [150, 123], [152, 117],
                    [154, 108], [154, 101], [154, 92], [153, 85], [152, 79],
                    [150, 75]
                ]

                brakelight_right = [
                    [167, 70], [169, 73], [171, 79], [172, 84], [172, 87],
                    [170, 87], [170, 80], [168, 74], [167, 72], [167, 70]
                ]
                brakelight_left = [
                    [167, 128], [169, 125], [171, 119], [172, 114], [172, 111],
                    [170, 111], [170, 118], [168, 124], [167, 126], [167, 128]
                ]

                local_center_x, local_center_y = 90.8, 98.8


        # Internal helper to apply rotation and translation
        def transform_car_points(points_list):
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
        # Nathan yippie
        #draw_car(renderer, camera_x, camera_y, zoom, 'car_body_12', 0, 0, 0, [136, 213, 229, 255])
        for car in current_cars:
            draw_car(renderer, camera_x, camera_y, zoom, car[0], car[1], car[2], car[3], car[4])

        # Note: SDL_RenderPresent is called from main.py after GUI overlay

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