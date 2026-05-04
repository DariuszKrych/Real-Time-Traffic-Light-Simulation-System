# CIS2108 GAPT Project - SSL3/Python

## Project Supervisor
Prof. Clyde Meli

## Group Members
Christian Peter Scerri  
Dariusz Krych  
Justin Grech  
Nathan Micallef  

## Environment Setup
1. Download the `conda-lock.yml` from the repo.  
2. Go into the terminal/conda terminal.
3. Run `conda install -c conda-forge conda-lock`
4. Go to the directory where the `conda-lock.yml` file is.  
5. run `conda-lock install --name GAPT_Env conda-lock.yml` to create the environment.

## Environment Setup Details
Conda lock has been used to ensure identical frozen versions of libraries are used by everyone
to ensure no environment incompatibilities arise in the future.  
The conda lock was created with `conda-lock -f environment.yml -p win-64 -p linux-64 -p osx-64 -p osx-arm64` on 24/02/2026.

The PySDL3 wrapper allows usage of the sdl3 library for C++ in Python.

The `environment.yml` which was used is:  
name: CIS2108_GAPT_Env  
channels:  
&nbsp;&nbsp;\- conda-forge  
dependencies:  
&nbsp;&nbsp;\- python=3.12  
&nbsp;&nbsp;\- sdl3  
&nbsp;&nbsp;\- pip  
&nbsp;&nbsp;\- pip:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- PySDL3

## Running the Simulation

Run the standalone simulation with:

```bash
python run.py
```

## Networking Extension

Start the central traffic server in one terminal:

```bash
python -m src.traffic_server --host 127.0.0.1 --port 8765
```

Then start one or more junction clients in separate terminals:

```bash
python run.py --network --junction-id A1 --grid-x 0 --grid-y 0
python run.py --network --junction-id B1 --grid-x 1 --grid-y 0
```

Each client continues to simulate its own junction locally while publishing its
traffic light state, queue lengths, visible car count, and grid position to the
server. The server broadcasts the city-grid state back to all connected clients.
