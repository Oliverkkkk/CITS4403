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
    w, h = model.width, model.height

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # y=0 在上

    # ===== 新增：缓存每个格子的patch句柄 =====
    cell_patches = {}   # {(x,y): Rectangle}

    def veg_val2color(v):
        # 0=空地（浅灰）；1..4 用不同绿度，也可以只用alpha区分
        if v <= 0: return (0.9, 0.9, 0.9, 1.0)
        # 简单映射：v越大越深/越不透明
        # 你也可以按自己喜好改色板
        palette = {
            1: (0.56, 0.93, 0.56, 0.6),   # lightgreen
            2: (0.24, 0.70, 0.44, 0.6),   # mediumseagreen
            3: (0.13, 0.55, 0.13, 0.7),   # forestgreen
            4: (0.00, 0.39, 0.00, 0.8),   # darkgreen
        }
        return palette.get(int(v), (0.00, 0.39, 0.00, 0.8))

    # ===== 初始化背景：创建patch并保存句柄，而不是只画一次就丢掉 =====
    v = getattr(model, "vegetation", None)
    for x in range(w):
        for y in range(h):
            rect = plt.Rectangle((x, y), 1, 1, linewidth=0)
            ax.add_patch(rect)
            cell_patches[(x, y)] = rect
            if v is not None:
                rect.set_facecolor(veg_val2color(v[x, y]))
            else:
                rect.set_facecolor((0.9, 0.9, 0.9, 1.0))  # 无植被信息时灰色

    # ===== 河流图层（修正缩进与变量名冲突；且只初始化一次）=====
    river_patches = []
    if hasattr(model, "river") and model.river is not None:
        for rx in range(w):
            for ry in range(h):
                if model.river[rx, ry]:
                    rrect = plt.Rectangle((rx, ry), 1, 1, color="deepskyblue", alpha=1.0, linewidth=0)
                    ax.add_patch(rrect)
                    river_patches.append(rrect)

    # 网格线
    for gx in range(w + 1):
        ax.axvline(gx, lw=0.5, alpha=0.3)
    for gy in range(h + 1):
        ax.axhline(gy, lw=0.5, alpha=0.3)

    # 点图与文字
    cats_scatter = ax.scatter([], [], marker="s")
    prey_scatter = ax.scatter([], [], marker="o")
    text_box = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top")

    def init():
        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])
        text_box.set_text("Step: 0")
        return tuple(cell_patches.values()) + (cats_scatter, prey_scatter, text_box)

    def update(frame):
        # 推进一帧（这里会发生啃食与再生）
        if model.running:
            model.step()

        # === 关键：根据最新的 vegetation 更新每个格子的颜色 ===
        v = getattr(model, "vegetation", None)
        if v is not None:
            for (x, y), rect in cell_patches.items():
                rect.set_facecolor(veg_val2color(v[x, y]))

        # 更新散点位置与统计
        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])

        n_cats = count_cats(model)
        n_prey = count_prey(model)
        pred_events = getattr(model, "predation_events_this_step", 0)
        text_box.set_text(f"Step: {frame+1}\nCats: {n_cats}  Prey: {n_prey}\nPredationEvents: {pred_events}")

        # 返回所有被修改的 artists（不启用blit时也安全）
        return tuple(cell_patches.values()) + (cats_scatter, prey_scatter, text_box)

    anim = animation.FuncAnimation(
        fig, update, init_func=init, frames=steps, interval=interval_ms, blit=False, repeat=False
    )
    plt.tight_layout()
    return fig, anim
