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

```bash
# Run from project root
# Default: 
python run.py
# Custom:
python run.py --steps 200 --cats 10 --prey 50 --width 30 --height 30 --p 0.4 --seed 123
```
<p>
  For now, it will generate two plots: <i>population over time</i> and <i>Predation events per step</i>.
</p>