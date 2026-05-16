import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from src.render import create_window, create_junction_renderer, update_camera_from_input
from src.light_logic import change_street_light_colour, set_light_timings, update_dynamic_timings, set_manual_override, clear_manual_override
from src.cars import north, east, south, west
from src import gui
from src.setup_gui import run_setup_screen
from src.network import TrafficNetworkClient
from src.traffic_server import TrafficServer
import sdl3
import ctypes
import math
import random
import socket
import threading
import time

SPAWN_INTERVAL = 3.0
NETWORK_UPDATE_INTERVAL = 0.05  # 20 Hz: keeps peer rendering smooth across the wire
JUNCTION_GRID_SPACING = 2400  # world units between rendered peer junction centres

# Exit edge -> (grid offset dx,dy, receiving module attribute).
# A car heading off the world's east edge arrives at the eastern neighbour's
# `east` module (cars in the `east` module enter at the west side heading east),
# heading south arrives at the southern neighbour's `north` module, etc.
_HANDOFF_ROUTES = {
    "east":  ((1, 0),  "east"),
    "west":  ((-1, 0), "west"),
    "south": ((0, 1),  "north"),
    "north": ((0, -1), "south"),
}
_MODULE_BY_NAME = {"north": north, "east": east, "south": south, "west": west}

# Which neighbour offset *feeds* each module via handoff. If that neighbour is
# present in the city grid, do not spawn locally into the module — let cars
# arrive from the neighbour instead. Keys are the direction module objects.
_SPAWN_FEEDER = {
    north: (0, -1),
    south: (0, 1),
    east:  (-1, 0),
    west:  (1, 0),
}


def _probe_traffic_server(host, port, timeout=0.4):
    """Return True if something accepts a TCP connection on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ensure_traffic_server(host, port):
    """If no server is reachable at host:port, start one in this process.

    The auto-started server binds to 0.0.0.0 so peers anywhere on the LAN can
    reach it, while this process's own client still connects to the user-typed
    host (typically 127.0.0.1 or the host machine's LAN IP).
    Returns True if we started a server, False if one was already running, or
    None if the bind failed (e.g. port held by another non-traffic-server).
    """
    if _probe_traffic_server(host, port):
        return False

    server = TrafficServer("0.0.0.0", port)
    bind_error = []

    def _serve():
        try:
            server.serve_forever()
        except OSError as exc:
            bind_error.append(exc)

    thread = threading.Thread(target=_serve, daemon=True, name="auto-traffic-server")
    thread.start()

    # Wait briefly for the listen socket to come up.
    for _ in range(60):
        if bind_error:
            print(f"Auto-start of traffic server failed: {bind_error[0]}")
            return None
        if _probe_traffic_server(host, port, timeout=0.2):
            print(f"Auto-started traffic server on 0.0.0.0:{port}")
            return True
        time.sleep(0.05)
    return True


def _find_neighbour(grid_snapshot, self_id, target_gx, target_gy):
    for jid, info in grid_snapshot.items():
        if jid == self_id:
            continue
        if not info.get("connected", True):
            continue
        gp = info.get("grid_position") or [None, None]
        if len(gp) >= 2 and gp[0] == target_gx and gp[1] == target_gy:
            return jid
    return None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the real-time traffic light simulation.")
    parser.add_argument("--network", action="store_true", help="Connect this simulation to a central traffic server.")
    parser.add_argument("--server-host", default="127.0.0.1", help="Traffic server hostname or IP address.")
    parser.add_argument("--server-port", type=int, default=8765, help="Traffic server TCP port.")
    parser.add_argument("--junction-id", default="junction-1", help="Unique ID for this simulated junction.")
    parser.add_argument("--grid-x", type=int, default=0, help="X position of this junction in the virtual city grid.")
    parser.add_argument("--grid-y", type=int, default=0, help="Y position of this junction in the virtual city grid.")
    parser.add_argument("--skip-setup", action="store_true", help="Skip the pre-launch setup screen and use the CLI flags directly.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    window_dimensions, window, renderer = create_window()
    window_width, window_height = window_dimensions

    # Show the pre-simulation setup screen so the user can pick offline/LAN
    # mode and their slot in the 4x4 city grid. CLI flags seed the defaults
    # and --skip-setup bypasses the screen entirely.
    if args.skip_setup:
        settings = {
            "network": args.network,
            "server_host": args.server_host,
            "server_port": args.server_port,
            "junction_id": args.junction_id,
            "grid_x": args.grid_x,
            "grid_y": args.grid_y,
        }
    else:
        settings = run_setup_screen(window, renderer, window_dimensions, initial={
            "network_enabled": args.network,
            "server_host": args.server_host,
            "server_port": args.server_port,
            "junction_id": args.junction_id,
            "grid_x": args.grid_x,
            "grid_y": args.grid_y,
        })
        if settings is None:
            import sdl3 as _sdl3
            _sdl3.SDL_DestroyRenderer(renderer)
            _sdl3.SDL_DestroyWindow(window)
            _sdl3.SDL_Quit()
            return

    args.network = settings["network"]
    args.server_host = settings["server_host"]
    args.server_port = settings["server_port"]
    args.junction_id = settings["junction_id"]
    args.grid_x = settings["grid_x"]
    args.grid_y = settings["grid_y"]

    # Create the drawing function for the junction with all methods and attributes saved for it to access
    draw_scene = create_junction_renderer(window_dimensions)

    # Camera and zoom details
    camera_x, camera_y,camera_speed = 0, 0, 5
    zoom, min_zoom, max_zoom, zoom_speed = 1.0, 0.25, 2.0, 0.01

    # Enables alpha values for colour transparency when drawing
    sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

    framerate = 60
    frametime_sec = 1 / framerate
    frametime_msec = math.floor(1000/ framerate)
    global_time = 0

    # Spawn one car group per direction at the start
    direction_modules = [north, east, south, west]
    for mod in direction_modules:
        mod.spawn_car()

    last_spawn_time = 0

    last_dynamic_update = 0
    last_network_update = time.monotonic() - NETWORK_UPDATE_INTERVAL
    street_light_state = ['red', 'red', 'red', 'red']
    all_cars = []

    network_client = None
    if args.network:
        # If no traffic server is reachable on the chosen host:port, host one
        # in this process so the first LAN junction to launch acts as the hub.
        _ensure_traffic_server(args.server_host, args.server_port)
        network_client = TrafficNetworkClient(
            args.junction_id,
            host=args.server_host,
            port=args.server_port,
            grid_x=args.grid_x,
            grid_y=args.grid_y,
        )
        network_client.start()

    event = sdl3.SDL_Event()
    running = True

    try:
        while running:
            # Process events
            while sdl3.SDL_PollEvent(ctypes.byref(event)):
                if event.type == sdl3.SDL_EVENT_QUIT:
                    running = False
                elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
                    gui.handle_mouse_click(event.button.x, event.button.y)

            # Get keyboard state and update camera
            keys = sdl3.SDL_GetKeyboardState(None)
            camera_x, camera_y, zoom = update_camera_from_input(
                keys, camera_x, camera_y, zoom,
                camera_speed, zoom_speed, min_zoom, max_zoom,
                window_width, window_height
            )

            # Read GUI state
            gui_state = gui.get_state()

            if gui_state["running"]:
                # Apply light mode logic
                if gui_state["light_mode"] == "automatic":
                    clear_manual_override()
                    if global_time - last_dynamic_update >= 1.0:
                        update_dynamic_timings(
                            north.get_queue_length(),
                            east.get_queue_length(),
                            south.get_queue_length(),
                            west.get_queue_length(),
                            base_green=gui_state["cycle_duration"]
                        )
                        last_dynamic_update = global_time
                else:
                    set_manual_override(gui_state["manual_direction"])

                # Spawn a new car group at a random edge every SPAWN_INTERVAL seconds.
                # Skip any edge that has a connected neighbour — those cars come in
                # via handoff instead. Also skip if that edge has no room.
                if global_time - last_spawn_time >= SPAWN_INTERVAL:
                    spawn_pool = direction_modules
                    if network_client is not None:
                        grid = network_client.get_snapshot().get("grid", {})
                        spawn_pool = [
                            m for m in direction_modules
                            if _find_neighbour(
                                grid, args.junction_id,
                                args.grid_x + _SPAWN_FEEDER[m][0],
                                args.grid_y + _SPAWN_FEEDER[m][1],
                            ) is None
                        ]
                    if spawn_pool:
                        mod = random.choice(spawn_pool)
                        if mod.can_accept_car():
                            mod.spawn_car()
                    last_spawn_time = global_time

                # Check the current street light colour and pass it to be drawn
                street_light_state = change_street_light_colour(keys, global_time)

                # Check junction occupancy from each direction's current car state
                # Uses passed_through + distance, no 1-frame delay
                n_in = north.has_cars_in_junction()
                e_in = east.has_cars_in_junction()
                s_in = south.has_cars_in_junction()
                w_in = west.has_cars_in_junction()

                # A direction is blocked if ANY other direction has cars in the junction
                n_blocked = e_in or s_in or w_in
                e_blocked = n_in or s_in or w_in
                s_blocked = n_in or e_in or w_in
                w_blocked = n_in or e_in or s_in

                # Check the current cars states
                north_cars_states = north.change_states_of_cars(global_time, street_light_state, n_blocked)
                east_cars_states = east.change_states_of_carsE(global_time, street_light_state, e_blocked)
                west_cars_states = west.change_states_of_carsW(global_time, street_light_state, w_blocked)
                south_cars_states = south.change_states_of_carsS(global_time, street_light_state, s_blocked)

                all_cars = north_cars_states + east_cars_states + west_cars_states + south_cars_states

                # --- Outgoing car handoffs: cars that just left this junction's world ---
                if network_client is not None:
                    snapshot = network_client.get_snapshot()
                    grid = snapshot.get("grid", {})
                    for mod in direction_modules:
                        for exit_info in mod.drain_exits():
                            route = _HANDOFF_ROUTES.get(exit_info["edge"])
                            if route is None:
                                continue
                            (dx, dy), _recv_attr = route
                            target_id = _find_neighbour(
                                grid, args.junction_id,
                                args.grid_x + dx, args.grid_y + dy,
                            )
                            if target_id is None:
                                continue
                            network_client.send_car_handoff(
                                target_id,
                                exit_info["edge"],
                                exit_info["speed"],
                                exit_info["color"],
                                exit_info["body"],
                            )
                else:
                    for mod in direction_modules:
                        mod.drain_exits()

                # --- Incoming car handoffs: spawn cars sent from neighbours ---
                if network_client is not None:
                    for handoff in network_client.drain_handoffs():
                        route = _HANDOFF_ROUTES.get(handoff.get("edge"))
                        if route is None:
                            continue
                        _, recv_attr = route
                        target_mod = _MODULE_BY_NAME.get(recv_attr)
                        if target_mod is None:
                            continue
                        target_mod.inject_car(
                            handoff.get("speed"),
                            handoff.get("color"),
                            handoff.get("body"),
                        )

                # Advance time
                global_time += frametime_sec

            current_wall_time = time.monotonic()
            if network_client is not None and current_wall_time - last_network_update >= NETWORK_UPDATE_INTERVAL:
                queues = {
                    "north": north.get_queue_length(),
                    "east": east.get_queue_length(),
                    "south": south.get_queue_length(),
                    "west": west.get_queue_length(),
                }
                network_client.update_junction_state({
                    "running": gui_state["running"],
                    "light_mode": gui_state["light_mode"],
                    "manual_direction": gui_state["manual_direction"],
                    "cycle_duration": gui_state["cycle_duration"],
                    "lights": {
                        "west": street_light_state[0],
                        "east": street_light_state[1],
                        "south": street_light_state[2],
                        "north": street_light_state[3],
                    },
                    "queues": queues,
                    "cars_visible": len(all_cars),
                    "cars": all_cars,
                })
                snapshot = network_client.get_snapshot()
                gui.set_network_status({
                    "junction_id": args.junction_id,
                    "grid_position": [args.grid_x, args.grid_y],
                    "status": snapshot["status"],
                    "last_error": snapshot["last_error"],
                    "peer_count": snapshot["peer_count"],
                    "grid": snapshot.get("grid", {}),
                })
                last_network_update = current_wall_time

            # Build peer list from the latest grid snapshot so each window renders
            # the whole connected city, not just its own junction.
            peers = None
            own_label = args.junction_id if network_client is not None else None
            if network_client is not None:
                grid = network_client.get_snapshot().get("grid", {})
                peers = []
                for jid, info in grid.items():
                    if jid == args.junction_id:
                        continue
                    gp = info.get("grid_position") or [0, 0]
                    if len(gp) < 2:
                        continue
                    payload = info.get("payload") or {}
                    lights_dict = payload.get("lights") or {}
                    peer_lights = [
                        lights_dict.get("west", "red"),
                        lights_dict.get("east", "red"),
                        lights_dict.get("south", "red"),
                        lights_dict.get("north", "red"),
                    ]
                    peers.append({
                        "dx": int(gp[0]) - args.grid_x,
                        "dy": int(gp[1]) - args.grid_y,
                        "lights": peer_lights,
                        "cars": payload.get("cars") or [],
                        "label": jid,
                    })

            # Draw the junction with current camera, zoom and street light colour.
            draw_scene(renderer, camera_x, camera_y, zoom, street_light_state, all_cars,
                       peers=peers, own_label=own_label, junction_spacing=JUNCTION_GRID_SPACING)

            # Draw GUI overlay on top
            gui.draw_gui(renderer)

            # Present frame
            sdl3.SDL_RenderPresent(renderer)

            # Simple delay to maintain ~60 FPS (16ms per frame)
            sdl3.SDL_Delay(frametime_msec)
    finally:
        if network_client is not None:
            network_client.stop()

        # Clean up resources
        sdl3.SDL_DestroyRenderer(renderer)
        sdl3.SDL_DestroyWindow(window)
        sdl3.SDL_Quit()

if __name__ == "__main__":
    main()
