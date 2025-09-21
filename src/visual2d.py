import matplotlib.pyplot as plt
from matplotlib import animation
from src.model import count_cats, count_prey
from itertools import product

try:
    # just for type checking; to avoid circular import, string comparison is more robust
    from .agents import Cat, Prey
except Exception:
    Cat = type("Cat", (), {})
    Prey = type("Prey", (), {})

def _get_positions(model):
    # return (cats_x, cats_y, prey_x, prey_y) four lists for scatter plot.
    cats_x, cats_y, prey_x, prey_y = [], [], [], []
    for a in model.agents:
        if not hasattr(a, "pos") or a.pos is None:
            continue
        x, y = a.pos
        # notice: y=0 is at the bottom in Matplotlib by default, but at the top in Mesa's MultiGrid
        if isinstance(a, Cat):
            cats_x.append(x + 0.5)
            cats_y.append(y + 0.5)
        elif isinstance(a, Prey):
            prey_x.append(x + 0.5)
            prey_y.append(y + 0.5)
    return cats_x, cats_y, prey_x, prey_y

def animate_grid(model, steps=200, interval_ms=150, figsize=(6, 6), title="Feral Cats vs Prey (2D Grid)"):
    # model: 2D grid model instance
    # steps: number of frames
    # interval_ms: delay between frames in milliseconds
    w, h = model.width, model.height

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # set y=0 on the top

    # draw background based on vegitation
    for x in range(w):
        for y in range(h):
            v = getattr(model, "vegetation", None)
            if v is not None:
                val = v[x, y]
                if val == 1:
                    ax.add_patch(plt.Rectangle((x, y), 1, 1, color="lightgreen", alpha=0.3))
                elif val == 2:
                    ax.add_patch(plt.Rectangle((x, y), 1, 1, color="mediumseagreen", alpha=0.3))
                elif val == 3:
                    ax.add_patch(plt.Rectangle((x, y), 1, 1, color="forestgreen", alpha=0.3))
                elif val == 4:
                    ax.add_patch(plt.Rectangle((x, y), 1, 1, color="darkgreen", alpha=0.3))


    for x in range(w + 1):
        ax.axvline(x, lw=0.5, alpha=0.3)
    for y in range(h + 1):
        ax.axhline(y, lw=0.5, alpha=0.3)

    # initialize scatters and text box
    cats_scatter = ax.scatter([], [], marker="s") 
    prey_scatter = ax.scatter([], [], marker="o")

    text_box = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top")


    def init():
        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])
        text_box.set_text("Step: 0")
        return cats_scatter, prey_scatter, text_box

    # evolve for each frame
    def update(frame):
        # forward one step
        if model.running:
            model.step()

        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])

        # statistics
        n_cats = count_cats(model)
        n_prey = count_prey(model)
        pred_events = getattr(model, "predation_events_this_step", 0)
        text_box.set_text(f"Step: {frame+1}\nCats: {n_cats}  Prey: {n_prey}\nPredationEvents: {pred_events}")

        return cats_scatter, prey_scatter, text_box

    anim = animation.FuncAnimation(
        fig, update, init_func=init, frames=steps, interval=interval_ms, blit=False, repeat=False
    )
    plt.tight_layout()
    return fig, anim