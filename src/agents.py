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
        # Randomly pick a cell (allow multiple agents in one cell; MVP no cat avoidance)
        dest = self.model.random.choice(neighborhood)
        grid.move_agent(self, dest)


class Cat(Agent):
    def __init__(self, model):
        super().__init__(model)

    def spread_smile(self):
        pass

    def step(self):
        grid = self.model.grid

        for _ in range(3):
            # move: Moore neighborhood, step size=1
            neighborhood = grid.get_neighborhood(self.pos, moore=True, include_center=True, radius=1)
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
