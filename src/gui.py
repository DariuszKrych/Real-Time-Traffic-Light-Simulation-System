import sdl3
import ctypes

# --- GUI State ---
simulation_running = True
light_mode = "automatic"
cycle_duration = 4.0
manual_direction = "north"  # which direction is green in manual mode
network_status = None

# --- Layout Constants ---
PANEL_X = 10
PANEL_Y = 10
PANEL_WIDTH = 440
ROW_HEIGHT = 30
PADDING = 10
CHAR_W = 8
CHAR_H = 8
BTN_HEIGHT = 22
BTN_PAD_Y = 4

# Colors
BG_COLOR = (40, 40, 40, 200)
BTN_COLOR = (80, 80, 80, 255)
BTN_ACTIVE_COLOR = (50, 140, 50, 255)
TEXT_COLOR = (255, 255, 255, 255)
LABEL_COLOR = (200, 200, 200, 255)

# Button definitions — computed at init
_buttons = {}

def _init_buttons():
    global _buttons
    x0 = PANEL_X + PADDING
    row1_y = PANEL_Y + PADDING
    row2_y = row1_y + ROW_HEIGHT + 5
    row3_y = row2_y + ROW_HEIGHT + 5
    row4_y = row3_y + ROW_HEIGHT + 5

    btn_x = x0 + 22 * CHAR_W

    _buttons = {
        "start":     {"label": "Start",     "x": btn_x,       "y": row1_y, "w": 50, "h": BTN_HEIGHT},
        "stop":      {"label": "Stop",      "x": btn_x + 60,  "y": row1_y, "w": 50, "h": BTN_HEIGHT},
        "manual":    {"label": "Manual",    "x": btn_x,       "y": row2_y, "w": 60, "h": BTN_HEIGHT},
        "automatic": {"label": "Automatic", "x": btn_x + 70,  "y": row2_y, "w": 80, "h": BTN_HEIGHT},
        "plus":      {"label": "+0.5",      "x": btn_x + 60,  "y": row3_y, "w": 45, "h": BTN_HEIGHT},
        "minus":     {"label": "-0.5",      "x": btn_x + 115, "y": row3_y, "w": 45, "h": BTN_HEIGHT},
        # Manual direction buttons (row 4, only visible in manual mode)
        "dir_north": {"label": "North", "x": btn_x,       "y": row4_y, "w": 55, "h": BTN_HEIGHT},
        "dir_east":  {"label": "East",  "x": btn_x + 60,  "y": row4_y, "w": 50, "h": BTN_HEIGHT},
        "dir_south": {"label": "South", "x": btn_x + 115, "y": row4_y, "w": 55, "h": BTN_HEIGHT},
        "dir_west":  {"label": "West",  "x": btn_x + 175, "y": row4_y, "w": 50, "h": BTN_HEIGHT},
    }

_init_buttons()

def _get_panel_height():
    if light_mode == "manual":
        return 4 * ROW_HEIGHT + 5 * PADDING
    return 3 * ROW_HEIGHT + 4 * PADDING


def draw_gui(renderer):
    # Draw panel background
    sdl3.SDL_SetRenderDrawColor(renderer, *BG_COLOR)
    panel_rect = sdl3.SDL_FRect(PANEL_X, PANEL_Y, PANEL_WIDTH, _get_panel_height())
    sdl3.SDL_RenderFillRect(renderer, ctypes.byref(panel_rect))

    x0 = PANEL_X + PADDING
    row1_y = PANEL_Y + PADDING
    row2_y = row1_y + ROW_HEIGHT + 5
    row3_y = row2_y + ROW_HEIGHT + 5

    # Row 1: Simulation label + Start/Stop buttons
    sdl3.SDL_SetRenderDrawColor(renderer, *LABEL_COLOR)
    sdl3.SDL_RenderDebugText(renderer, x0, row1_y + BTN_PAD_Y, b"Simulation")

    _draw_button(renderer, _buttons["start"], active=(simulation_running))
    _draw_button(renderer, _buttons["stop"], active=(not simulation_running))

    # Row 2: Toggle Light Control + Manual/Automatic buttons
    sdl3.SDL_SetRenderDrawColor(renderer, *LABEL_COLOR)
    sdl3.SDL_RenderDebugText(renderer, x0, row2_y + BTN_PAD_Y, b"Toggle Light Control")

    _draw_button(renderer, _buttons["manual"], active=(light_mode == "manual"))
    _draw_button(renderer, _buttons["automatic"], active=(light_mode == "automatic"))

    # Row 3: Light Cycle Duration + readout + +/- buttons
    sdl3.SDL_SetRenderDrawColor(renderer, *LABEL_COLOR)
    sdl3.SDL_RenderDebugText(renderer, x0, row3_y + BTN_PAD_Y, b"Light Cycle Duration")

    duration_text = f"{cycle_duration:.1f}s".encode()
    sdl3.SDL_SetRenderDrawColor(renderer, *TEXT_COLOR)
    sdl3.SDL_RenderDebugText(renderer, _buttons["plus"]["x"] - 50, row3_y + BTN_PAD_Y, duration_text)

    _draw_button(renderer, _buttons["plus"])
    _draw_button(renderer, _buttons["minus"])

    # Row 4: Direction buttons (only in manual mode)
    if light_mode == "manual":
        row4_y = row3_y + ROW_HEIGHT + 5
        sdl3.SDL_SetRenderDrawColor(renderer, *LABEL_COLOR)
        sdl3.SDL_RenderDebugText(renderer, x0, row4_y + BTN_PAD_Y, b"Active Direction")

        _draw_button(renderer, _buttons["dir_north"], active=(manual_direction == "north"))
        _draw_button(renderer, _buttons["dir_east"], active=(manual_direction == "east"))
        _draw_button(renderer, _buttons["dir_south"], active=(manual_direction == "south"))
        _draw_button(renderer, _buttons["dir_west"], active=(manual_direction == "west"))

    # Camera controls text in bottom left
    sdl3.SDL_SetRenderDrawColor(renderer, *TEXT_COLOR)
    sdl3.SDL_RenderDebugText(renderer, 10, 700,
        b"Camera controls: Up[w], Down[s], Left[a], Right[d], Zoom-in[q], Zoom-out[e]")

    if network_status is not None:
        status_text = (
            f"Network: {network_status['status']} | "
            f"junction {network_status['junction_id']} | "
            f"peers {network_status['peer_count']}"
        )
        if network_status["last_error"] and network_status["status"] != "connected":
            status_text += f" | {network_status['last_error'][:45]}"
        sdl3.SDL_RenderDebugText(renderer, 10, 685, status_text.encode())


def _draw_button(renderer, btn, active=False):
    if active:
        sdl3.SDL_SetRenderDrawColor(renderer, *BTN_ACTIVE_COLOR)
    else:
        sdl3.SDL_SetRenderDrawColor(renderer, *BTN_COLOR)

    rect = sdl3.SDL_FRect(btn["x"], btn["y"], btn["w"], btn["h"])
    sdl3.SDL_RenderFillRect(renderer, ctypes.byref(rect))

    # Draw border
    sdl3.SDL_SetRenderDrawColor(renderer, 160, 160, 160, 255)
    sdl3.SDL_RenderRect(renderer, ctypes.byref(rect))

    # Draw label centered in button
    text_w = len(btn["label"]) * CHAR_W
    text_x = btn["x"] + (btn["w"] - text_w) / 2
    text_y = btn["y"] + (btn["h"] - CHAR_H) / 2
    sdl3.SDL_SetRenderDrawColor(renderer, *TEXT_COLOR)
    sdl3.SDL_RenderDebugText(renderer, text_x, text_y, btn["label"].encode())


def handle_mouse_click(mx, my):
    global simulation_running, light_mode, cycle_duration, manual_direction

    mx = float(mx)
    my = float(my)

    for name, btn in _buttons.items():
        # Skip direction buttons if not in manual mode
        if name.startswith("dir_") and light_mode != "manual":
            continue

        if (btn["x"] <= mx <= btn["x"] + btn["w"] and
                btn["y"] <= my <= btn["y"] + btn["h"]):
            if name == "start":
                simulation_running = True
            elif name == "stop":
                simulation_running = False
            elif name == "manual":
                light_mode = "manual"
            elif name == "automatic":
                light_mode = "automatic"
            elif name == "plus":
                cycle_duration += 0.5
            elif name == "minus":
                cycle_duration = max(0.5, cycle_duration - 0.5)
            elif name == "dir_north":
                manual_direction = "north"
            elif name == "dir_east":
                manual_direction = "east"
            elif name == "dir_south":
                manual_direction = "south"
            elif name == "dir_west":
                manual_direction = "west"
            return


def get_state():
    return {
        "running": simulation_running,
        "light_mode": light_mode,
        "cycle_duration": cycle_duration,
        "manual_direction": manual_direction,
    }


def set_network_status(status):
    global network_status
    network_status = status
