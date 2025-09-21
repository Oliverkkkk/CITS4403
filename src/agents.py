from mesa import Agent

class Prey(Agent):
    def __init__(self, model):
        super().__init__(model)

    def get_smile(self):
        pass

    # only random move, no reproduction, no cat avoidance
    def step(self):
        grid = self.model.grid
        # Moore neighborhood (including center), step size=1
        neighborhood = grid.get_neighborhood(self.pos, moore=True, include_center=True, radius=1)
        #get vegetation information
        vegetation = getattr(self.model, "vegetation", None)
        if vegetation is not None:
            weights = []
            for (x, y) in neighborhood:
                if x < 0 or x >= self.model.width or y < 0 or y >= self.model.height:
                    weights.append(1)
                else:
                    veg_val = vegetation[x, y]
                    weights.append(1 + veg_val)
            # move to grid with higher vegetation
            dest = self.model.random.choices(neighborhood, weights=weights, k=1)[0]
        else:
            dest = self.model.random.choice(neighborhood)
        grid.move_agent(self, dest)
        #left trail
        x, y = self.pos
        if hasattr(self.model, "prey_trail"):
            self.model.prey_trail[x, y] = 1


class Cat(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 3
        self.counter = 0
        self.alive = True

    def spread_smile(self):
        pass

    def step(self):
        if not self.alive:
            return

        grid = self.model.grid

        for _ in range(self.energy):
            # move: Moore neighborhood, step size=1
            neighborhood = grid.get_neighborhood(self.pos, moore=True, include_center=True, radius=1)
            dest = None
            trail = getattr(self.model, "prey_trail", None)
            if trail is not None:
                weights = []
                for (x, y) in neighborhood:
                    v = int(trail[x, y])
                    w = max(6 - v, 1)
                    weights.append(w)
                dest = self.model.random.choices(neighborhood, weights=weights, k=1)[0]
            else:
                dest = self.random.choice(neighborhood)

            grid.move_agent(self, dest)

            # prey: check the cell after move
            cellmates = grid.get_cell_list_contents([self.pos])
            prey_here = [a for a in cellmates if isinstance(a, Prey)]

            if prey_here:
                # select one prey to attempt predation (once per step)
                target = self.model.random.choice(prey_here)
                if self.model.random.random() < self.model.predation_prob:
                    # successful predation
                    target.remove()
                    self.model.predation_events_this_step += 1

                    self.energy = min(self.energy + 1, 3)
                    self.counter = 0
        # Add energy limitation
        self.counter += 1
        if self.counter >= 15:
            self.energy -= 1
            self.counter = 0

        if self.energy <= 0:
            grid.remove_agent(self)
            self.alive = False

