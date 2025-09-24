"""
Entry point for the Feral Cats & Small Mammal Community ABM.
Run from project root:
    Default: 
    python run.py
    
    Custom:
    python run.py --steps 200 --cats 10 --prey 50 --width 30 --height 30 --p 0.4 --seed 123
"""

import argparse
import matplotlib.pyplot as plt
import matplotlib
import os, sys
from src.model import FeralCatModel
from src.visual2d import animate_grid


def main():
    # Initial statues
    parser = argparse.ArgumentParser(description="Feral Cats ABM Simulation")
    parser.add_argument("--steps", type=int, default=100, help="Number of steps to run")
    parser.add_argument("--cats", type=int, default=6, help="Number of cats")
    parser.add_argument("--prey", type=int, default=40, help="Number of prey")
    parser.add_argument("--width", type=int, default=25, help="Grid width")
    parser.add_argument("--height", type=int, default=25, help="Grid height")
    parser.add_argument("--pb", type=float, default=0.2, help="predation_base")
    parser.add_argument("--pc", type=float, default=0.1, help="predation_coef")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    # Initialize model
    model = FeralCatModel(
        width=args.width,
        height=args.height,
        n_cats=args.cats,
        n_prey=args.prey,
        predation_base=args.pb,
        predation_coef=args.pc,
        seed=args.seed,
    )

    model.datacollector.collect(model)

    # 2D-grid animation 
    fig, anim = animate_grid(model, steps=args.steps + 1, interval_ms=300)
    plt.show()

    df = model.datacollector.get_model_vars_dataframe().reset_index(drop=True)
    print(df.tail())

    # Plot population over time
    ax = df[["Prey", "Cats"]].plot(figsize=(7, 4))
    ax.set_title("Population over time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.show()

    # Plot predation events over time
    ax2 = df["PredationEvents"].plot(figsize=(7, 3))
    ax2.set_title("Predation events per step")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Events")
    plt.tight_layout()
    plt.show()

def select_backend(interactive=True):
    """
     Select a safe matplotlib backend across OSes.
    """
    # keep any pre-set backend in environment variable
    if os.environ.get("MPLBACKEND"):
        return
   
    # Agg in non-interactive mode
    if not interactive or os.environ.get("CI") or not sys.stdout.isatty():
        matplotlib.use("Agg", force=True)
        return
   
    # order in interactive mode: QtAgg, TkAgg, Agg
    candidates = (
        ["MacOSX", "QtAgg", "TkAgg", "Agg"] if sys.platform == "darwin"
        else ["QtAgg", "TkAgg", "Agg"]
    )
    for name in candidates:
        try:
            matplotlib.use(name, force=True)
            return
        except Exception:
            continue


if __name__ == "__main__":
    select_backend(interactive=True)
    main()