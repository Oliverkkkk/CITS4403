# FeralCats Inc.

<p align="center">
  <b>Feral Cats and Small Mammals: Modeling Predation Risk Shaped by Scent Mark Diffusion</b>
</p>

<p align="center">
  <i>Agent-Based Framework • Trend plots • Evolving visulization • Valuable insights</i>
</p>

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- pip
- Git

### Setup & Installation

1. **Clone the repository**

```bash
git clone https://github.com/Oliverkkkk/CITS4403.git
cd CITS4403
```

2. **Create and activate a virtual environment**

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate

# For macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the application**

Interactive GUI entry:
```bash
# Run from project root
python run.py # GUI entry point for the Feral Cats ABM.
```

Quick entry:
```bash
# Run from project root
# Default: 
python run_mini.py
# Custom:
python run_mini.py --steps 200 --cats 10 --prey 50 --width 30 --height 30 --p 0.4 --seed 123
```
