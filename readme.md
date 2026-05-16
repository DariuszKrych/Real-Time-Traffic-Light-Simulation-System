# Real-Time Traffic Light Simulation System

A real-time, four-way junction traffic simulation written in Python with SDL3. Cars approach the intersection from the north, east, south, and west arms under an eight-phase traffic light cycle, with optional LAN multiplayer that stitches multiple junctions into one shared city grid and hands cars between them as they drive off the world edge.

Built for the **CIS2108 Group Assigned Practical Task (GAPT)** under the supervision of **Prof. Clyde Meli**.

---

## Authors

| Name |
|------|
| Christian Peter Scerri |
| Dariusz Krych |
| Justin Grech |
| Nathan Micallef |

---

## Features

- Four-way junction with left-turn, straight-through, and right-turn paths per arm
- Eight-phase traffic light cycle (`N_GREEN → N_ORANGE → E_GREEN → E_ORANGE → S_GREEN → S_ORANGE → W_GREEN → W_ORANGE`)
- **Automatic mode** with dynamic green-time allocation proportional to per-arm queue length
- **Manual mode** for directly picking which arm is green
- Per-car timing model with stop-line obedience, cross-arm junction occupancy blocking, and emergent queueing via front-to-back car-spacing constraints
- Pan-and-zoom 2D camera (WASD + Q/E)
- Pre-launch setup screen for choosing offline vs. LAN mode and selecting a slot in the 4×3 city grid
- Optional LAN mode with a central TCP traffic server, live peer-state broadcasts, car handoffs between junctions, and an on-screen city-grid minimap
- Reproducible single-file release artifacts: Linux AppImage (`x86_64`) and Windows `.exe`, built automatically by GitHub Actions on tag push

---

## Quick Start

### Option 1 — Pre-Built Releases

Download the latest release from the [Releases](../../releases) page:

| Platform | File |
|----------|------|
| Linux (any distro, glibc ≥ 2.35) | `TrafficSim-x86_64.AppImage` |
| Windows | `TrafficSim.exe` |

**Linux:**
```bash
chmod +x TrafficSim-x86_64.AppImage
./TrafficSim-x86_64.AppImage
```
If you get a FUSE error on Ubuntu 24.04+, either install `libfuse2` (`sudo apt install libfuse2`) or run with `--appimage-extract-and-run`.

**Windows:** double-click `TrafficSim.exe`. Windows SmartScreen may prompt on first launch because the binary is unsigned.

### Option 2 — Run From Source

Requires Python 3.12 and the conda environment described below.

```bash
python run.py
```

---

## Environment Setup

The repository uses [`conda-lock`](https://github.com/conda/conda-lock) to pin every dependency to an exact, reproducible version across Windows, Linux, and macOS (Intel and Apple Silicon).

```bash
# Install conda-lock once
conda install -c conda-forge conda-lock

# From the repo root
conda-lock install --name GAPT_Env conda-lock.yml
conda activate GAPT_Env
```

### Underlying `environment.yml`

```yaml
name: CIS2108_GAPT_Env
channels:
  - conda-forge
dependencies:
  - python=3.12
  - sdl3
  - pip
  - pip:
      - PySDL3
```

The lock file was generated with:
```bash
conda-lock -f environment.yml -p win-64 -p linux-64 -p osx-64 -p osx-arm64
```
on 24/02/2026.

`PySDL3` is the Python binding over the SDL3 C library and provides the windowing, rendering, and input primitives the simulation builds on.

---

## Running The Simulation

### Standalone (offline)

```bash
python run.py
```

The setup screen appears first; pick **Offline** and press **Start**.

To skip the setup screen entirely:
```bash
python run.py --skip-setup
```

### LAN / Multi-Junction Mode

A central traffic server brokers state between all participating junction clients.

**Option A — auto-host:** the first client launched in LAN mode starts the server inside its own process on `0.0.0.0` and acts as the hub. Subsequent clients connect to its LAN IP.

**Option B — dedicated server:** run the server explicitly in its own terminal:
```bash
python -m src.traffic_server --host 0.0.0.0 --port 8765
```

Then start one or more junction clients, either via the setup screen or directly:
```bash
python run.py --network --junction-id A1 --grid-x 0 --grid-y 0
python run.py --network --junction-id B1 --grid-x 1 --grid-y 0 --server-host 192.168.1.42
```

Each client simulates its own junction locally and publishes its state (light colours, queue lengths, visible cars, grid position) to the server 20× per second. The server rebroadcasts a full `grid_state` snapshot to every client so each window can render the entire connected city, and relays per-car handoff messages between neighbouring junctions when cars drive off the world boundary.

---

## Controls

### In-Simulation

| Action | Input |
|--------|-------|
| Pan camera | `W` `A` `S` `D` |
| Zoom in / out | `Q` / `E` |
| Start / Stop simulation | On-screen panel |
| Toggle automatic vs. manual lights | On-screen panel |
| Adjust cycle duration | `+0.5` / `-0.5` buttons |
| Choose manual green direction | North / East / South / West buttons (manual mode only) |

### Setup Screen

Text fields are editable with the keyboard; the 4×3 grid is clickable. In LAN mode, slots already claimed by other live junctions are shown as taken and cannot be selected.

---

## Command-Line Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--network` | off | Connect to a traffic server |
| `--server-host` | `127.0.0.1` | Server hostname or IP |
| `--server-port` | `8765` | Server TCP port |
| `--junction-id` | `junction-1` | Unique ID for this client |
| `--grid-x` | `0` | This junction's X slot in the city grid |
| `--grid-y` | `0` | This junction's Y slot in the city grid |
| `--skip-setup` | off | Bypass the setup screen and use the CLI flags directly |

These flags also seed the default values shown on the setup screen, so they double as both shortcuts and presets.

---

## Building Release Binaries

The repository ships two build scripts plus a GitHub Actions workflow that produces both binaries on every `v*` tag push and attaches them to a GitHub release.

### Linux AppImage

Build host requirements: Python 3.10+, `wget`, and (for running the resulting AppImage) `libfuse2`. For maximum cross-distro compatibility, build on Ubuntu 22.04 LTS (glibc 2.35).

```bash
bash build/build_linux.sh
```

Output: `dist/TrafficSim-x86_64.AppImage`

### Windows EXE

Build host requirements: Python 3.10+ on `PATH`. Run from a `cmd` or PowerShell prompt:

```bat
build\build_windows.bat
```

Output: `dist\TrafficSim.exe`

---

## Project Structure

```
.
├── run.py                          # Entry point
├── src/
│   ├── main.py                     # Main loop, orchestration, CLI parsing
│   ├── light_logic.py              # Eight-phase state machine + dynamic timing
│   ├── render.py                   # SDL3 drawing pipeline and camera
│   ├── gui.py                      # In-simulation control panel
│   ├── setup_gui.py                # Pre-launch setup screen
│   ├── network.py                  # TCP client (TrafficNetworkClient)
│   ├── traffic_server.py           # TCP hub (TrafficServer)
│   ├── package.json                # Car-body polygon templates
│   └── cars/
│       ├── north.py                # North-arm car module
│       ├── east.py                 # East-arm car module
│       ├── south.py                # South-arm car module
│       └── west.py                 # West-arm car module
├── build/
│   ├── build_linux.sh              # AppImage build script
│   ├── build_windows.bat           # Windows EXE build script
│   └── icon.png                    # Application icon
├── conda-lock.yml                  # Pinned cross-platform dependencies
└── readme.md
```

---
