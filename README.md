# DRTSMini-Project-2
Distributed Real-Time Systems Mini Project 2 Repository

## Installation

Create and activate a virtual environment, then install the project dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

## Usage

Run the simulator through `main.py` and select a test case with `--test-case`.
You can also change the simulation window with `--max-simulation-time`.

The default values are:

- `--test-case test_cases/test_case_0`
- `--max-simulation-time 1000`

Examples:

```bash
python main.py
python main.py --test-case test_cases/test_case_1
python main.py --test-case test_cases/test_case_2 --max-simulation-time 2000
python main.py --test-case test_cases/test_case_3 --max-simulation-time 5000
```

Each test case folder must contain `streams.json`, `routes.json`, and `topology.json`.


# Workload distribution

## Person 1 — Flora
- Parsing and making data structures

## Person 2 — Armand
- Data visualization

## Person 3 — Ivan
- Port with queues

## Person 4 — Boti
- Simulation network

## Person 5 — Sushant
- Network node (switch / starting point / end point)

## Person 6 — Balazs
- Analysis

## Whoever finishes
- Help out with bigger tasks
- Implement optional project extension
