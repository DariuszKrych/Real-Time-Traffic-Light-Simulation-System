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
3. Go to the directory where the `conda-lock.yml` file is.  
4. run `conda-lock install --name GAPT_Env conda-lock.yml` to create the environment.

## Environment Setup Details
Conda lock has been used to ensure identical frozen versions of libraries are used by everyone
to ensure no environment incompatibilities arise in the future.  
The conda lock was created with `conda-lock -f environment.yml -p win-64 -p linux-64 -p osx-64 -p osx-arm64` on 24/02/2026.  

The `environment.yml` which was used is:  
name: CIS2108_GAPT_Env  
channels:  
&nbsp;&nbsp;&nbsp;\- conda-forge  
dependencies:  
&nbsp;&nbsp;&nbsp;\- python=3.12  
&nbsp;&nbsp;&nbsp;\- sdl3
