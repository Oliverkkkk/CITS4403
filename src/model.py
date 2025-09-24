from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from .agents import Cat, Prey
import numpy as np


class FeralCatModel(Model):
    """
    Minimum runable ABM
    MultiGrid & RandomActivation
    Rule: both cat and prey randomly move; if in same cell, try to hunt once with given probability
    """
    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        n_cats: int = 5,
        n_prey: int = 20,
        predation_base: float = 0.2,
        predation_coef: float = 0.1,
        seed: int | None = None,
        prey_flee_prob: float = 0.4
    ):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.predation_base = predation_base
        self.predation_coef = predation_coef
        prey_flee_prob: float = 0.4
        self.running = True

        self.river = np.zeros((width, height), dtype=bool)
        thickness = 2
        cx = width // 2
        x0, x1 = max(0, cx - thickness // 2), min(width, cx + (thickness + 1) // 2)
        for y in range(height):
            rx = int(cx + 2 * np.sin(2 * np.pi * y / max(1, height)))
            half = thickness // 2
            xL = max(0, rx - half)
            xR = min(width, rx + (thickness + 1) // 2)
            self.river[xL:xR, y] = True

        gap_len = max(3, height // 6)
        gap_center = height // 3
        g0 = max(0, gap_center - gap_len // 2)
        g1 = min(height, g0 + gap_len)
        self.river[x0-1:x1+1, g0:g1] = False

        self.vegetation = np.random.choice([0,1,2,3,4], size=(width, height), p=[0.4, 0.2,0.15,0.15, 0.1])
        self.prey_trail = np.full((width, height), 5, dtype=int)

        # place prey
        for i in range(n_prey):
            while True:
                x, y = self.random.randrange(width), self.random.randrange(height)
                if not self.river[x, y]:
                    a = Prey(self)
                    self.grid.place_agent(a, (x, y))
                    break

        # place cats
        for i in range(n_cats):
            while True:
                x, y = self.random.randrange(width), self.random.randrange(height)
                if not self.river[x, y]:
                    a = Cat(self)
                    self.grid.place_agent(a, (x, y))
                    break

        self.datacollector = DataCollector(
            model_reporters={
                "Cats": count_cats,
                "Prey": count_prey,
                "PredationEvents": lambda m: getattr(m, "predation_events_this_step", 0),
            }
        )

    def refresh_cat_scent(self, radius: int = 2):
        """用当前所有存活猫的位置，生成'气味'布尔图（Chebyshev距离<=radius 即有气味）。"""
        import numpy as np
        w, h = self.width, self.height

        # 初始化/清空 cat_scent
        if not hasattr(self, "cat_scent") or getattr(self, "cat_scent").shape != (w, h):
            self.cat_scent = np.zeros((w, h), dtype=np.uint8)
        else:
            self.cat_scent.fill(0)

        self.cat_positions = []
        for a in self.agents:
            # 只考虑存活的猫
            if isinstance(a, Cat) and getattr(a, "alive", True) and getattr(a, "pos", None) is not None:
                cx, cy = a.pos
                self.cat_positions.append((cx, cy))
                x0, x1 = max(0, cx - radius), min(w - 1, cx + radius)
                y0, y1 = max(0, cy - radius), min(h - 1, cy + radius)
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        if max(abs(x - cx), abs(y - cy)) <= radius:  # Chebyshev 距离
                            self.cat_scent[x, y] = 1

    def is_blocked(self, pos):
        x, y = pos
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return bool(self.river[x, y])

    def step(self):
        self.predation_events_this_step = 0
        self.refresh_cat_scent(radius=2)
        self.prey_trail = np.minimum(self.prey_trail + 1, 5)

        self.agents.shuffle_do("step")
        if hasattr(self, "vegetation") and self.vegetation is not None:
            v = self.vegetation
            if hasattr(self, "river") and self.river is not None:
                mask = (v > 0) & (np.random.rand(*v.shape) < 0.4)
                v[mask] += 1
            else:
                v[v > 0] += 1
            np.minimum(v, 4, out=v)
        self.datacollector.collect(self)

        # if no prey left, stop the model
        if not any(isinstance(a, Prey) for a in self.agents):
            self.running = False

    def predation_prob_at(self, pos: tuple[int, int]) -> float:
        veg = getattr(self, "vegetation", None)
        v = 0
        if veg is not None:
            x, y = pos
            v = int(veg[x, y])
        p = self.predation_base + self.predation_coef * v
        return p

def count_cats(model):
    return sum(isinstance(a, Cat) and getattr(a, "alive", True) for a in model.agents)

def count_prey(model: "FeralCatModel"):
    return sum(isinstance(a, Prey) for a in model.agents)
