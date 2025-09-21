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
        predation_prob: float = 0.35,
        seed: int | None = None,
    ):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.predation_prob = float(predation_prob)
        self.grid = MultiGrid(width, height, torus=False)
        self.running = True

        self.vegetation = np.random.choice([0,1,2,3,4], size=(width, height), p=[0.4, 0.2,0.15,0.15, 0.1])
        self.prey_trail = np.full((width, height), 5, dtype=int)

        # place prey
        for i in range(n_prey):
            prey = Prey(self)
            x, y = self.random.randrange(width), self.random.randrange(height)
            self.grid.place_agent(prey, (x, y))

        # place cats
        for i in range(n_cats):
            cat = Cat(self)
            x, y = self.random.randrange(width), self.random.randrange(height)
            self.grid.place_agent(cat, (x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "Cats": count_cats,
                "Prey": count_prey,
                "PredationEvents": lambda m: getattr(m, "predation_events_this_step", 0),
            }
        )

    def step(self):
        self.predation_events_this_step = 0
        self.prey_trail = np.minimum(self.prey_trail + 1, 5)

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        # if no prey left, stop the model
        if not any(isinstance(a, Prey) for a in self.agents):
            self.running = False

def count_cats(model):
    return sum(isinstance(a, Cat) and getattr(a, "alive", True) for a in model.agents)

def count_prey(model: "FeralCatModel"):
    return sum(isinstance(a, Prey) for a in model.agents)
