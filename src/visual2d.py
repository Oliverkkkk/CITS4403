import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.lines import Line2D
from src.model import count_cats, count_prey

try:
    # just for type checking; to avoid circular import, string comparison is more robust
    from .agents import Cat, Prey
except Exception:
    Cat = type("Cat", (), {})
    Prey = type("Prey", (), {})


def _get_positions(model):
    """
    Return (cats_x, cats_y, prey_x, prey_y) four lists for scatter plot.
    注意：Matplotlib 默认 y=0 在底部，而 Mesa MultiGrid 的 (0,0) 在左上；
    这里用 ax.invert_yaxis() 处理视觉坐标，无需翻转值。
    """
    cats_x, cats_y, prey_x, prey_y = [], [], [], []
    for a in model.agents:
        if not hasattr(a, "pos") or a.pos is None:
            continue
        x, y = a.pos
        if isinstance(a, Cat):
            cats_x.append(x + 0.5)
            cats_y.append(y + 0.5)
        elif isinstance(a, Prey):
            prey_x.append(x + 0.5)
            prey_y.append(y + 0.5)
    return cats_x, cats_y, prey_x, prey_y


def animate_grid(
    model,
    steps,
    interval_ms,
    figsize=(6, 6),
    title="Feral Cats vs Prey (2D Grid)",
    on_finished=None
):
    """
    2D 动画：支持植被底图、河流遮罩、猫/猎物散点、统计文本框；
    现在新增“猫气味范围”的红色描边层（切比雪夫距离 <= 2 的格子）。
    """
    w, h = model.width, model.height

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=False)
    ax.set_title(title)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # y=0 在上

    # ===== 背景格子：每个格子一个矩形 patch，并缓存句柄 =====
    cell_patches = {}   # {(x,y): Rectangle}

    def veg_val2color(v):
        # 0=空地（浅灰）；1..4 用不同绿色/不透明度
        if v <= 0:
            return (0.9, 0.9, 0.9, 1.0)
        palette = {
            1: (0.56, 0.93, 0.56, 0.6),  # lightgreen
            2: (0.24, 0.70, 0.44, 0.6),  # mediumseagreen
            3: (0.13, 0.55, 0.13, 0.7),  # forestgreen
            4: (0.00, 0.39, 0.00, 0.8),  # darkgreen
        }
        return palette.get(int(v), (0.00, 0.39, 0.00, 0.8))

    v = getattr(model, "vegetation", None)
    for x in range(w):
        for y in range(h):
            rect = plt.Rectangle((x, y), 1, 1, linewidth=0, zorder=0)  # 背景层 zorder=0
            ax.add_patch(rect)
            cell_patches[(x, y)] = rect
            if v is not None:
                rect.set_facecolor(veg_val2color(v[x, y]))
            else:
                rect.set_facecolor((0.9, 0.9, 0.9, 1.0))  # 无植被信息时灰色

    # ===== 河流图层（只初始化一次），位于背景之上 =====
    river_patches = []
    if hasattr(model, "river") and model.river is not None:
        for rx in range(w):
            for ry in range(h):
                if model.river[rx, ry]:
                    rrect = plt.Rectangle((rx, ry), 1, 1, color="deepskyblue",
                                          alpha=1.0, linewidth=0, zorder=1)
                    ax.add_patch(rrect)
                    river_patches.append(rrect)

    # ===== 气味描边层：为每个格子预置红色空心方块，默认隐藏 =====
    scent_patches = {}   # {(x,y): Rectangle}
    for x in range(w):
        for y in range(h):
            srect = plt.Rectangle(
                (x, y), 1, 1,
                fill=False,
                linewidth=1.5,
                edgecolor="red",
                alpha=0.9,
                visible=False,     # 初始隐藏
                zorder=2           # 盖在背景与河流之上，不遮挡散点（散点 zorder=3）
            )
            ax.add_patch(srect)
            scent_patches[(x, y)] = srect

    # 网格线（可选）：降低存在感
    for gx in range(w + 1):
        ax.axvline(gx, lw=0.5, alpha=0.25, zorder=2)
    for gy in range(h + 1):
        ax.axhline(gy, lw=0.5, alpha=0.25, zorder=2)

    # ===== agent scatters & text box（给散点更高的 zorder）=====
    cats_scatter = ax.scatter([], [], marker="s", c="tab:red", zorder=3)
    prey_scatter = ax.scatter([], [], marker="o", c="tab:blue", zorder=3)
    text_box = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", zorder=4)

    # 图例
    legend_elems = [
        Line2D([0], [0], marker='s', linestyle='None', markerfacecolor='tab:red',
               markersize=6, label='Cats'),
        Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='tab:blue',
               markersize=6, label='Prey'),
    ]
    legend = ax.legend(
        handles=legend_elems,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=len(legend_elems),
        columnspacing=1.2,
        handletextpad=0.3,
        borderaxespad=0.,
        frameon=True, fancybox=True, framealpha=0.1
    )

    def _apply_scent_visibility():
        """
        根据 model.cat_scent 显示/隐藏红色描边。
        需要模型每步已调用 refresh_cat_scent(radius=2)。
        """
        scent = getattr(model, "cat_scent", None)
        if scent is not None:
            for (x, y), srect in scent_patches.items():
                srect.set_visible(bool(scent[x, y]))
        else:
            for srect in scent_patches.values():
                srect.set_visible(False)

    def init():
        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])
        text_box.set_text("Step: 0")

        # 初始化气味描边
        _apply_scent_visibility()

        # 返回所有被修改的 artists（不启用 blit 时也安全）
        return (
            tuple(cell_patches.values())
            + tuple(scent_patches.values())
            + (cats_scatter, prey_scatter, text_box)
        )

    def update(frame):
        # 推进一帧（model.step() 内部会刷新 cat_scent/vegetation 等）
        if model.running:
            model.step()

        # 更新底图颜色（植被变化）
        v2 = getattr(model, "vegetation", None)
        if v2 is not None:
            for (x, y), rect in cell_patches.items():
                rect.set_facecolor(veg_val2color(v2[x, y]))

        # 更新气味描边
        _apply_scent_visibility()

        # 更新散点位置与统计
        cx, cy, px, py = _get_positions(model)
        cats_scatter.set_offsets(list(zip(cx, cy)) if cx else [])
        prey_scatter.set_offsets(list(zip(px, py)) if px else [])

        n_cats = count_cats(model)
        n_prey = count_prey(model)
        pred_events = getattr(model, "predation_events_this_step", 0)
        pred_events_total = getattr(model, "predation_events_total", 0)
        text_box.set_text(
            f"Step: {frame+1}\n"
            f"Cats: {n_cats}\n"
            f"Prey: {n_prey}\n"
            f"PredationEvents: {pred_events}\n"
            f"PredationEventsTotal: {pred_events_total}"
        )

        if (frame + 1) >= steps and callable(on_finished):
            on_finished()

        return (
            tuple(cell_patches.values())
            + tuple(scent_patches.values())
            + (cats_scatter, prey_scatter, text_box)
        )

    anim = animation.FuncAnimation(
        fig, update, init_func=init,
        frames=steps, interval=interval_ms,
        blit=False, repeat=False
    )
    plt.tight_layout()
    return fig, anim
