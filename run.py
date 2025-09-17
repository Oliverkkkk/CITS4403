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
from src.model import FeralCatModel
from src.visual2d import animate_grid


def main():
    parser = argparse.ArgumentParser(description="Feral Cats ABM Simulation")
    parser.add_argument("--steps", type=int, default=100, help="Number of steps to run")
    parser.add_argument("--cats", type=int, default=6, help="Number of cats")
    parser.add_argument("--prey", type=int, default=40, help="Number of prey")
    parser.add_argument("--width", type=int, default=25, help="Grid width")
    parser.add_argument("--height", type=int, default=25, help="Grid height")
    parser.add_argument("--p", type=float, default=0.35, help="Predation probability")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    # Initialize model
    model = FeralCatModel(
        width=args.width,
        height=args.height,
        n_cats=args.cats,
        n_prey=args.prey,
        predation_prob=args.p,
        seed=args.seed,
    )

    # Simulation
    for _ in range(args.steps):
        if not model.running:
            break
        model.step()

    # Print and plot results
    df = model.datacollector.get_model_vars_dataframe()
    print(df.tail())

    # Plot population over time
    ax = df[["Prey", "Cats"]].plot(figsize=(7, 4))
    ax.set_title("Population over time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")
    plt.show()

    # Plot predation events over time
    ax2 = df["PredationEvents"].plot(figsize=(7, 3))
    ax2.set_title("Predation events per step")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Events")
    plt.show()

    # Animate the grid
    fig, anim = animate_grid(model, steps=args.steps, interval_ms=120)
    plt.show()


if __name__ == "__main__":
    main()