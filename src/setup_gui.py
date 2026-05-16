"""Pre-simulation setup screen.

Renders inside the same SDL window the simulation uses, lets the user pick
offline or LAN mode, edit server/junction settings, and select this junction's
slot in a 4x4 city grid.

Returns a settings dict consumed by main.py, or None if the user closes the
window before pressing Start.
"""

import ctypes
import json
import socket
import threading
import time

import sdl3


CHAR_W = 8
CHAR_H = 8

BG_COLOR = (22, 26, 34, 255)
PANEL_BG = (44, 50, 64, 240)
PANEL_BORDER = (90, 100, 120, 255)
BTN_COLOR = (70, 80, 100, 255)
BTN_ACTIVE_COLOR = (50, 140, 80, 255)
BTN_DISABLED_COLOR = (50, 55, 65, 255)
BTN_BORDER = (160, 170, 190, 255)
TEXT_COLOR = (235, 235, 240, 255)
TEXT_DIM_COLOR = (130, 135, 145, 255)
LABEL_COLOR = (185, 195, 215, 255)
FIELD_BG = (20, 25, 35, 255)
FIELD_ACTIVE_BG = (35, 45, 60, 255)
FIELD_DISABLED_BG = (30, 32, 38, 255)
FIELD_BORDER = (110, 120, 140, 255)
FIELD_ACTIVE_BORDER = (220, 200, 90, 255)
GRID_CELL_COLOR = (55, 65, 80, 255)
GRID_CELL_SELECTED = (50, 140, 80, 255)
GRID_CELL_DISABLED = (40, 44, 52, 255)
GRID_CELL_TAKEN = (90, 35, 35, 255)
GRID_BORDER_COLOR = (130, 140, 160, 255)
GRID_BORDER_TAKEN = (200, 80, 80, 255)
TITLE_COLOR = (250, 220, 100, 255)
ACCENT_COLOR = (120, 200, 255, 255)

MAX_FIELD_LEN = 40
GRID_COLS = 4
GRID_ROWS = 3

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
    '`': '~',
}


def _fill_rect(renderer, x, y, w, h, color):
    sdl3.SDL_SetRenderDrawColor(renderer, *color)
    rect = sdl3.SDL_FRect(float(x), float(y), float(w), float(h))
    sdl3.SDL_RenderFillRect(renderer, ctypes.byref(rect))


def _outline_rect(renderer, x, y, w, h, color):
    sdl3.SDL_SetRenderDrawColor(renderer, *color)
    rect = sdl3.SDL_FRect(float(x), float(y), float(w), float(h))
    sdl3.SDL_RenderRect(renderer, ctypes.byref(rect))


def _draw_text(renderer, x, y, text, color):
    if isinstance(text, str):
        text = text.encode()
    sdl3.SDL_SetRenderDrawColor(renderer, *color)
    sdl3.SDL_RenderDebugText(renderer, float(x), float(y), text)


def _draw_scaled_text(renderer, x, y, text, color, scale=2.0):
    if isinstance(text, str):
        text = text.encode()
    sdl3.SDL_SetRenderScale(renderer, float(scale), float(scale))
    sdl3.SDL_SetRenderDrawColor(renderer, *color)
    sdl3.SDL_RenderDebugText(renderer, float(x) / scale, float(y) / scale, text)
    sdl3.SDL_SetRenderScale(renderer, 1.0, 1.0)


def _in_rect(px, py, rect):
    return (rect["x"] <= px <= rect["x"] + rect["w"]
            and rect["y"] <= py <= rect["y"] + rect["h"])


def _draw_button(renderer, btn, active=False, disabled=False, large=False):
    if disabled:
        color = BTN_DISABLED_COLOR
        label_color = TEXT_DIM_COLOR
    elif active:
        color = BTN_ACTIVE_COLOR
        label_color = TEXT_COLOR
    else:
        color = BTN_COLOR
        label_color = TEXT_COLOR

    _fill_rect(renderer, btn["x"], btn["y"], btn["w"], btn["h"], color)
    _outline_rect(renderer, btn["x"], btn["y"], btn["w"], btn["h"], BTN_BORDER)

    label = btn["label"]
    if large:
        scale = 1.8
        text_w = len(label) * CHAR_W * scale
        text_h = CHAR_H * scale
        text_x = btn["x"] + (btn["w"] - text_w) / 2
        text_y = btn["y"] + (btn["h"] - text_h) / 2
        _draw_scaled_text(renderer, text_x, text_y, label, label_color, scale=scale)
    else:
        text_w = len(label) * CHAR_W
        text_x = btn["x"] + (btn["w"] - text_w) / 2
        text_y = btn["y"] + (btn["h"] - CHAR_H) / 2
        _draw_text(renderer, text_x, text_y, label, label_color)


def _keycode(name, default):
    return getattr(sdl3, name, default)


def _query_taken_slots(host, port, self_id, timeout=0.4):
    """Ask the traffic server which (gx, gy) slots are currently occupied.

    Returns a set of (gx, gy) tuples on success, or None if the server is
    unreachable / replied with something unexpected.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(b'{"type":"query"}\n')
            sock.settimeout(timeout)
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
    except (OSError, ValueError):
        return None

    if not buf:
        return None
    try:
        line = buf.split(b"\n", 1)[0]
        msg = json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if msg.get("type") != "grid_state":
        return None

    taken = set()
    for jid, info in (msg.get("junctions") or {}).items():
        if jid == self_id:
            continue
        if not info.get("connected", False):
            continue
        gp = info.get("grid_position") or [None, None]
        if len(gp) >= 2:
            try:
                taken.add((int(gp[0]), int(gp[1])))
            except (TypeError, ValueError):
                continue
    return taken


class _SlotProbe:
    """Background poller that keeps the setup GUI's taken-slot set fresh."""

    def __init__(self):
        self._lock = threading.Lock()
        self._target = (None, None, None, False)  # host, port, self_id, enabled
        self._taken = set()
        self._reachable = False
        self._wake = threading.Event()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="setup-slot-probe")

    def start(self):
        self._thread.start()

    def stop(self):
        self._running = False
        self._wake.set()

    def update_target(self, host, port, self_id, enabled):
        with self._lock:
            new = (host, port, self_id, enabled)
            if new == self._target:
                return
            self._target = new
            # Invalidate immediately so a stale set isn't used while we
            # probe the new target.
            self._taken = set()
            self._reachable = False
        self._wake.set()

    def snapshot(self):
        with self._lock:
            return set(self._taken), self._reachable

    def _run(self):
        while self._running:
            with self._lock:
                host, port, self_id, enabled = self._target
            if enabled and host and port:
                result = _query_taken_slots(host, port, self_id)
                with self._lock:
                    if result is None:
                        self._taken = set()
                        self._reachable = False
                    else:
                        self._taken = result
                        self._reachable = True
            else:
                with self._lock:
                    self._taken = set()
                    self._reachable = False
            self._wake.wait(timeout=1.0)
            self._wake.clear()


def _find_free_slot(taken):
    for ry in range(GRID_ROWS):
        for cx in range(GRID_COLS):
            if (cx, ry) not in taken:
                return cx, ry
    return None


def run_setup_screen(window, renderer, window_dimensions, initial=None):
    """Show the setup screen and return chosen settings (or None on quit)."""
    width, height = window_dimensions

    state = {
        "network_enabled": False,
        "server_host": "127.0.0.1",
        "server_port": "8765",
        "junction_id": "junction-0-0",
        "grid_x": 0,
        "grid_y": 0,
    }
    # Track whether the user typed their own junction ID. If not, regenerate
    # it from the selected grid cell so two instances on the same machine pick
    # different IDs by default — sharing one ID makes the server overwrite the
    # first client's socket on re-register and drop it from broadcasts.
    junction_id_user_edited = False
    if initial:
        for key in state:
            if key in initial and initial[key] is not None:
                state[key] = initial[key]
        state["server_port"] = str(state["server_port"])
        state["grid_x"] = int(state["grid_x"]) % GRID_COLS
        state["grid_y"] = int(state["grid_y"]) % GRID_ROWS
        if state["junction_id"] not in ("", "junction-1"):
            junction_id_user_edited = True
    if not junction_id_user_edited:
        state["junction_id"] = f"junction-{state['grid_x']}-{state['grid_y']}"

    active_field = None

    # Layout: title bar, two panels side-by-side, Start button bottom-center.
    left_x, left_y = 60, 130
    left_w, left_h = 540, 470

    offline_btn = {"label": "Run Offline",
                   "x": left_x + 30, "y": left_y + 50, "w": 220, "h": 42}
    online_btn = {"label": "Connect to LAN",
                  "x": left_x + 280, "y": left_y + 50, "w": 230, "h": 42}

    field_label_x = left_x + 30
    field_input_x = left_x + 180
    field_w = 340
    field_h = 32

    text_fields = [
        {"key": "server_host", "label": "Server Host:", "y": left_y + 145},
        {"key": "server_port", "label": "Server Port:", "y": left_y + 195},
        {"key": "junction_id", "label": "Junction ID:", "y": left_y + 245},
    ]

    right_x, right_y = 650, 130
    right_w, right_h = 570, 470

    cell_size = 90
    cell_gap = 14
    grid_total_w = GRID_COLS * cell_size + (GRID_COLS - 1) * cell_gap
    grid_origin_x = right_x + (right_w - grid_total_w) // 2
    grid_origin_y = right_y + 80

    start_btn = {"label": "Start Simulation",
                 "x": (width - 320) // 2, "y": height - 75, "w": 320, "h": 55}

    # Keycodes — fall back to raw ASCII values if the binding lacks the symbol.
    K_BACKSPACE = _keycode("SDLK_BACKSPACE", 8)
    K_RETURN = _keycode("SDLK_RETURN", 13)
    K_ESCAPE = _keycode("SDLK_ESCAPE", 27)
    K_TAB = _keycode("SDLK_TAB", 9)

    sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

    probe = _SlotProbe()
    probe.start()

    event = sdl3.SDL_Event()
    done = False
    cancelled = False

    while not done:
        # Keep the background probe aimed at the user's current target so the
        # next reply reflects whatever host/port/id they have typed in.
        try:
            probe_port = int(state["server_port"])
        except ValueError:
            probe_port = None
        probe.update_target(
            (state["server_host"] or "").strip() or None,
            probe_port,
            state["junction_id"],
            state["network_enabled"],
        )
        taken_slots, server_reachable = probe.snapshot()

        # If the cell we're sitting on just got claimed by someone else,
        # auto-shift to the first free cell so the user never has a taken
        # slot selected.
        if state["network_enabled"] and (state["grid_x"], state["grid_y"]) in taken_slots:
            free = _find_free_slot(taken_slots)
            if free is not None:
                state["grid_x"], state["grid_y"] = free
                if not junction_id_user_edited:
                    state["junction_id"] = f"junction-{free[0]}-{free[1]}"

        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                cancelled = True
                done = True
            elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
                mx = float(event.button.x)
                my = float(event.button.y)

                if _in_rect(mx, my, offline_btn):
                    state["network_enabled"] = False
                    active_field = None
                    continue
                if _in_rect(mx, my, online_btn):
                    state["network_enabled"] = True
                    continue

                clicked_field = None
                if state["network_enabled"]:
                    for f in text_fields:
                        field_rect = {"x": field_input_x, "y": f["y"],
                                      "w": field_w, "h": field_h}
                        if _in_rect(mx, my, field_rect):
                            clicked_field = f["key"]
                            break
                if clicked_field is not None:
                    active_field = clicked_field
                    continue

                # Grid cells are always clickable so the user can preview their
                # spot even in offline mode; it just won't be sent over the wire.
                clicked_cell = False
                for ry in range(GRID_ROWS):
                    for cx in range(GRID_COLS):
                        x = grid_origin_x + cx * (cell_size + cell_gap)
                        y = grid_origin_y + ry * (cell_size + cell_gap)
                        if _in_rect(mx, my, {"x": x, "y": y,
                                             "w": cell_size, "h": cell_size}):
                            # Eat the click either way so the empty-space
                            # branch below doesn't deselect the active field,
                            # but only update selection if the slot is free.
                            clicked_cell = True
                            if state["network_enabled"] and (cx, ry) in taken_slots:
                                break
                            state["grid_x"] = cx
                            state["grid_y"] = ry
                            if not junction_id_user_edited:
                                state["junction_id"] = f"junction-{cx}-{ry}"
                            break
                    if clicked_cell:
                        break
                if clicked_cell:
                    active_field = None
                    continue

                if _in_rect(mx, my, start_btn):
                    # Refuse to launch onto a taken slot — the server would
                    # reject the registration anyway.
                    if state["network_enabled"] and (state["grid_x"], state["grid_y"]) in taken_slots:
                        continue
                    done = True
                    continue

                active_field = None

            elif event.type == sdl3.SDL_EVENT_KEY_DOWN:
                key = event.key.key
                mod = event.key.mod
                if key == K_ESCAPE:
                    active_field = None
                elif active_field is not None:
                    if key == K_BACKSPACE:
                        state[active_field] = state[active_field][:-1]
                        if active_field == "junction_id":
                            junction_id_user_edited = True
                    elif key == K_RETURN:
                        active_field = None
                    elif key == K_TAB:
                        keys = [f["key"] for f in text_fields]
                        if active_field in keys:
                            idx = keys.index(active_field)
                            active_field = keys[(idx + 1) % len(keys)]
                    elif 32 <= key <= 126 and len(state[active_field]) < MAX_FIELD_LEN:
                        ch = chr(key)
                        shift = bool(mod & 0x0003)
                        caps = bool(mod & 0x2000)
                        if shift:
                            if ch.isalpha():
                                ch = ch.upper() if not caps else ch.lower()
                            else:
                                ch = SHIFT_MAP.get(ch, ch)
                        elif caps and ch.isalpha():
                            ch = ch.upper()
                        state[active_field] += ch
                        if active_field == "junction_id":
                            junction_id_user_edited = True
                else:
                    if key == K_RETURN:
                        done = True

        # ---- Render ----
        sdl3.SDL_SetRenderDrawColor(renderer, *BG_COLOR)
        sdl3.SDL_RenderClear(renderer)

        title = "Traffic Simulation Setup"
        title_scale = 2.6
        title_w = len(title) * CHAR_W * title_scale
        _draw_scaled_text(renderer, (width - title_w) / 2, 28, title,
                          TITLE_COLOR, scale=title_scale)
        subtitle = "Pick offline mode or join a LAN city grid of junctions"
        sub_x = (width - len(subtitle) * CHAR_W) / 2
        _draw_text(renderer, sub_x, 92, subtitle, LABEL_COLOR)

        # --- Left panel: network settings ---
        _fill_rect(renderer, left_x, left_y, left_w, left_h, PANEL_BG)
        _outline_rect(renderer, left_x, left_y, left_w, left_h, PANEL_BORDER)
        _draw_scaled_text(renderer, left_x + 18, left_y + 14,
                          "Network Settings", TEXT_COLOR, scale=1.6)

        _draw_button(renderer, offline_btn, active=(not state["network_enabled"]))
        _draw_button(renderer, online_btn, active=state["network_enabled"])

        for f in text_fields:
            enabled = state["network_enabled"]
            is_active = (active_field == f["key"]) and enabled

            label_color = LABEL_COLOR if enabled else TEXT_DIM_COLOR
            _draw_text(renderer, field_label_x, f["y"] + 12, f["label"], label_color)

            if not enabled:
                field_bg = FIELD_DISABLED_BG
                field_border = FIELD_BORDER
            elif is_active:
                field_bg = FIELD_ACTIVE_BG
                field_border = FIELD_ACTIVE_BORDER
            else:
                field_bg = FIELD_BG
                field_border = FIELD_BORDER
            _fill_rect(renderer, field_input_x, f["y"], field_w, field_h, field_bg)
            _outline_rect(renderer, field_input_x, f["y"], field_w, field_h, field_border)

            value = state[f["key"]]
            display = (value + "_") if is_active else value
            text_color = TEXT_COLOR if enabled else TEXT_DIM_COLOR
            max_chars = (field_w - 16) // CHAR_W
            _draw_text(renderer, field_input_x + 8, f["y"] + 12,
                       display[-max_chars:], text_color)

        hint_y = left_y + left_h - 90
        if not state["network_enabled"]:
            _draw_text(renderer, left_x + 30, hint_y,
                       "Offline mode runs this junction on its own", LABEL_COLOR)
            _draw_text(renderer, left_x + 30, hint_y + 14,
                       "with no peers and no server traffic.", LABEL_COLOR)
        else:
            _draw_text(renderer, left_x + 30, hint_y,
                       "Click a field to edit. Tab cycles, Enter confirms.",
                       LABEL_COLOR)
            _draw_text(renderer, left_x + 30, hint_y + 14,
                       "Make sure the traffic server is reachable on the LAN.",
                       LABEL_COLOR)

        # --- Right panel: 4x4 grid picker ---
        _fill_rect(renderer, right_x, right_y, right_w, right_h, PANEL_BG)
        _outline_rect(renderer, right_x, right_y, right_w, right_h, PANEL_BORDER)
        _draw_scaled_text(renderer, right_x + 18, right_y + 14,
                          "City Grid Position", TEXT_COLOR, scale=1.6)
        _draw_text(renderer, right_x + 18, right_y + 50,
                   "Pick this junction's slot. (0,0) is top-left.",
                   LABEL_COLOR)

        enabled = state["network_enabled"]
        for ry in range(GRID_ROWS):
            for cx in range(GRID_COLS):
                x = grid_origin_x + cx * (cell_size + cell_gap)
                y = grid_origin_y + ry * (cell_size + cell_gap)
                selected = (cx == state["grid_x"] and ry == state["grid_y"])
                taken = enabled and (cx, ry) in taken_slots
                if taken:
                    cell_color = GRID_CELL_TAKEN
                    border_color = GRID_BORDER_TAKEN
                elif selected:
                    cell_color = GRID_CELL_SELECTED
                    border_color = GRID_BORDER_COLOR
                elif enabled:
                    cell_color = GRID_CELL_COLOR
                    border_color = GRID_BORDER_COLOR
                else:
                    cell_color = GRID_CELL_DISABLED
                    border_color = GRID_BORDER_COLOR
                _fill_rect(renderer, x, y, cell_size, cell_size, cell_color)
                _outline_rect(renderer, x, y, cell_size, cell_size, border_color)

                label = f"({cx},{ry})"
                if taken:
                    lc = TEXT_COLOR
                elif selected or enabled:
                    lc = TEXT_COLOR
                else:
                    lc = TEXT_DIM_COLOR
                tx = x + (cell_size - len(label) * CHAR_W) // 2
                ty = y + cell_size // 2 - 8
                _draw_text(renderer, tx, ty, label, lc)
                if taken:
                    sub = "TAKEN"
                    sx = x + (cell_size - len(sub) * CHAR_W) // 2
                    _draw_text(renderer, sx, ty + 12, sub, TEXT_COLOR)

        info_y = right_y + right_h - 50
        selection_txt = (f"Selected position: ({state['grid_x']}, "
                         f"{state['grid_y']})")
        _draw_text(renderer, right_x + 18, info_y, selection_txt, ACCENT_COLOR)
        if enabled:
            if server_reachable:
                taken_count = len(taken_slots)
                if taken_count == 0:
                    hint = "Server reachable — no slots taken yet."
                else:
                    hint = (f"Server reachable — {taken_count} slot"
                            f"{'s' if taken_count != 1 else ''} taken (red).")
            else:
                hint = "No server reachable yet — one will auto-start on launch."
            _draw_text(renderer, right_x + 18, info_y + 16, hint, LABEL_COLOR)
        else:
            _draw_text(renderer, right_x + 18, info_y + 16,
                       "Position is informational while offline.",
                       LABEL_COLOR)

        start_disabled = (state["network_enabled"]
                          and (state["grid_x"], state["grid_y"]) in taken_slots)
        _draw_button(renderer, start_btn, active=not start_disabled,
                     disabled=start_disabled, large=True)

        sdl3.SDL_RenderPresent(renderer)
        sdl3.SDL_Delay(16)

    probe.stop()

    if cancelled:
        return None

    try:
        port = int(state["server_port"])
    except ValueError:
        port = 8765

    return {
        "network": state["network_enabled"],
        "server_host": state["server_host"].strip() or "127.0.0.1",
        "server_port": port,
        "junction_id": state["junction_id"].strip() or "junction-1",
        "grid_x": state["grid_x"],
        "grid_y": state["grid_y"],
    }
