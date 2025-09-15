# RelayCalc

RelayCalc is a small Python utility for calculating basic overcurrent relay
settings and creating a job-aid report.

## Features
- Reads equipment data from a CSV file (columns: `Line_ID`, `Voltage_kV`,
  `Current_A`, `Transformer_MVA`).
- Computes simple overcurrent relay pickups (`Pickup = 1.2 * Current_A`).
- Simulates a short-circuit with fault current equal to ten times the normal
  current and calculates the relay trip time using an I²t constant of 10,000.
- Stores results in a SQLite database (`relaycalc.db`).
- Plots current versus time curves with Matplotlib.
- Generates a PDF report using ReportLab containing the data table and plot.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

## Usage
```bash
python relaycalc.py input.csv output.pdf
```
This creates `output.pdf` and stores results in `relaycalc.db`.

## Example CSV
```
Line_ID,Voltage_kV,Current_A,Transformer_MVA
Line1,115,200,50
Line2,230,400,100
```
