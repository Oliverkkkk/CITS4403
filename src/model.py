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
        width: int,
        height: int,
        n_cats: int,
        n_prey: int,
        predation_base: float,
        predation_coef: float,
        prey_flee_prob: float,
        seed: int | None = None,
        vegetation=None,
        river=None,
    ):
        super().__init__(seed=seed)

        # vegetation is a 2D array of int (0-4), same size as map
        if vegetation is not None:
            V = np.array(vegetation, dtype=np.int16)
            assert V.ndim == 2, "vegetation should be a 2D array"
            np.clip(V, 0, 4, out=V)
            self.width, self.height = V.shape
        else:
            self.width, self.height = width, height

        # use size determined above
        self.grid = MultiGrid(self.width, self.height, torus=False)

        self.predation_base = predation_base
        self.predation_coef = predation_coef
        self.prey_flee_prob = prey_flee_prob
        self.running = True
        self.predation_events_total = 0

        # --- river ---
        if river is not None:
            R = np.array(river, dtype=bool)
            assert R.shape == (self.width, self.height), "river should be same as map"
            self.river = R
        else:
            self.river = np.zeros((self.width, self.height), dtype=bool)
            thickness = 2
            cx = self.width // 2
            x0, x1 = max(0, cx - thickness // 2), min(self.width, cx + (thickness + 1) // 2)
            for y in range(self.height):
                rx = int(cx + 2 * np.sin(2 * np.pi * y / max(1, self.height)))
                half = thickness // 2
                xL = max(0, rx - half)
                xR = min(self.width, rx + (thickness + 1) // 2)
                self.river[xL:xR, y] = True
            gap_len = max(3, self.height // 6)
            gap_center = self.height // 3
            g0 = max(0, gap_center - gap_len // 2)
            g1 = min(self.height, g0 + gap_len)
            self.river[x0 - 1:x1 + 1, g0:g1] = False

        # --- vegetation ---
        if vegetation is not None:
            self.vegetation = V
        else:
            self.vegetation = np.random.choice(
                [0, 1, 2, 3, 4],
                size=(self.width, self.height),
                p=[0.4, 0.2, 0.15, 0.15, 0.1]
            )

       # trail 1-5, 1 means just visited, 5 means long ago
        self.prey_trail = np.full((self.width, self.height), 5, dtype=int)

        # place prey
        for _ in range(n_prey):
            while True:
                x, y = self.random.randrange(self.width), self.random.randrange(self.height)
                if not self.river[x, y]:
                    a = Prey(self)
                    self.grid.place_agent(a, (x, y))
                    break

        # place cats
        for _ in range(n_cats):
            while True:
                x, y = self.random.randrange(self.width), self.random.randrange(self.height)
                if not self.river[x, y]:
                    a = Cat(self)
                    self.grid.place_agent(a, (x, y))
                    break

        self.datacollector = DataCollector(
            model_reporters={
                "Cats": count_cats,
                "Prey": count_prey,
                "predation_events_this_step": lambda m: getattr(m, "predation_events_this_step", 0),
                "predation_events_total": lambda m: m.predation_events_total,
            }
        )

    def refresh_cat_scent(self, radius: int = 2):
        """
        Generate a 'scent' Boolean graph using the current positions of all surviving cats 
        (Chebyshev distance<=radius indicates scent)。
        """
        w, h = self.width, self.height

        if not hasattr(self, "cat_scent") or getattr(self, "cat_scent").shape != (w, h):
            self.cat_scent = np.zeros((w, h), dtype=np.uint8)
        else:
            self.cat_scent.fill(0)

        self.cat_positions = []
        for a in self.agents:
            if isinstance(a, Cat) and getattr(a, "alive", True) and getattr(a, "pos", None) is not None:
                cx, cy = a.pos
                self.cat_positions.append((cx, cy))
                x0, x1 = max(0, cx - radius), min(w - 1, cx + radius)
                y0, y1 = max(0, cy - radius), min(h - 1, cy + radius)
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        if max(abs(x - cx), abs(y - cy)) <= radius:
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

        # plant regrow: each cell has independent 0.5 prob to regrow if veg>0 and not river; cap at 4
        if hasattr(self, "vegetation") and self.vegetation is not None:
            v = self.vegetation
            rand_mask = (np.random.rand(self.width, self.height) < 0.5)
            regen_mask = (v > 0) & (~self.river) & rand_mask
            v[regen_mask] += 1
            np.minimum(v, 4, out=v)

        self.datacollector.collect(self)

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
