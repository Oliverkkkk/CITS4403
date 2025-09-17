import sys
from pathlib import Path

CUR = Path(__file__).resolve()
ROOT = CUR.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model import FeralCatModel 
import matplotlib.pyplot as plt    


def main():
    model = FeralCatModel(width=25, height=25, n_cats=6, n_prey=40, predation_prob=0.35, seed=42)

    # 100 steps
    for _ in range(100):
        if not model.running:
            break
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    print(df.tail())

    ax = df[["Prey", "Cats"]].plot(figsize=(7, 4))
    ax.set_title("Population over time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.show()

    ax2 = df["PredationEvents"].plot(figsize=(7, 3))
    ax2.set_title("Predation events per step")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Events")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()