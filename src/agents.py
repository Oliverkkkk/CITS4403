from mesa import Agent

class Prey(Agent):
    def __init__(self, model,sex=None):
        super().__init__(model)
        if sex in ("F","M"):
            self.sex = sex
        else:
            p_f = getattr(self.model, "prey_female_ratio", 0.5)
            self.sex = "F" if self.model.random.random() < p_f else "M"

        self.since_repro = 0

    def get_smile(self):
        pass

    # only random move, no reproduction, no cat avoidance
    def step(self):
        grid = self.model.grid
        # Moore neighborhood (including center), step size=1
        neighborhood = grid.get_neighborhood(self.pos, moore=True, include_center=True, radius=1)
        valid = [p for p in neighborhood if not self.model.is_blocked(p)]
        #cat scent
        cat_positions = getattr(self.model, "cat_positions", [])
        cat_scent = getattr(self.model, "cat_scent", None)
        curr_pos = self.pos
        vegetation = getattr(self.model, "vegetation", None)

        def cheb(p, q):
            return max(abs(p[0] - q[0]), abs(p[1] - q[1]))
        sensed = (cat_scent is not None and cat_scent[curr_pos[0], curr_pos[1]] == 1)

        dest = None
        flee_prob = self.model.prey_flee_prob

        if sensed and self.model.random.random() < flee_prob and cat_positions:
            # 3A) 逃跑模式：从候选里选“离最近猫更远”的格子（最大化最近猫距离）
            best_d = -1
            best_positions = []
            for pos in neighborhood:
                d = min(cheb(pos, c) for c in cat_positions)  # 与最近猫的距离
                if d > best_d:
                    best_d = d
                    best_positions = [pos]
                elif d == best_d:
                    best_positions.append(pos)
            dest = self.model.random.choice(best_positions)
            x, y = self.pos
            if vegetation is not None:
                x, y = self.pos
                if vegetation[x, y] > 0:
                    vegetation[x, y] = max(1, vegetation[x, y] - 1)
            if hasattr(self.model, "prey_trail"):
                self.model.prey_trail[x, y] = 1
            self.since_repro += 1
        else:
            # get vegetation information
            vegetation = getattr(self.model, "vegetation", None)
            if vegetation is not None:
                weights = []
                for (x, y) in valid:
                    if x < 0 or x >= self.model.width or y < 0 or y >= self.model.height:
                        weights.append(1)
                    else:
                        veg_val = vegetation[x, y]
                        weights.append(1 + veg_val)
                # move to grid with higher vegetation
                dest = self.model.random.choices(valid, weights=weights, k=1)[0]
            else:
                dest = self.model.random.choice(valid)
            grid.move_agent(self, dest)
            # left trail
            x, y = self.pos
            if hasattr(self.model, "prey_trail"):
                self.model.prey_trail[x, y] = 1
            self.since_repro += 1

            if vegetation is not None:
                x, y = self.pos
                if vegetation[x, y] > 0:
                    vegetation[x, y] = max(1, vegetation[x, y] - 2)

            # Check Reproduction conditions
            # gender
            if self.sex != "F":
                return
            # vegetation
            if vegetation is None or vegetation[x, y] <= 2:
                return
            neigh_no_center = grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1)
            agents_near = grid.get_cell_list_contents(neigh_no_center)
            male_nearby = any(isinstance(a, Prey) and getattr(a, "sex", None) == "M" for a in agents_near)
            # any male nearby
            if not male_nearby:
                return
            # time from last reproduce
            if self.since_repro < 30:
                return

            n_offspring = self.model.random.randint(0, 2)
            spawn_pos = self.pos
            for _ in range(n_offspring):
                baby_sex = "F" if self.model.random.random() < getattr(self.model, "prey_female_ratio", 0.5) else "M"
                baby = Prey(self.model, sex=baby_sex)
                grid.place_agent(baby, spawn_pos)

                # 可选：足迹置为“刚经过”
                if hasattr(self.model, "prey_trail"):
                    bx, by = spawn_pos
                    self.model.prey_trail[bx, by] = 1

            # 成功繁衍后重置冷却
            self.since_repro = 0




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
            valid = [p for p in neighborhood if not self.model.is_blocked(p)]
            trail = getattr(self.model, "prey_trail", None)
            if trail is not None:
                weights = []
                for (x, y) in valid:
                    v = int(trail[x, y])
                    w = max(6 - v, 1)
                    weights.append(w)
                dest = self.model.random.choices(valid, weights=weights, k=1)[0]
            else:
                dest = self.random.choice(valid)

            grid.move_agent(self, dest)

            # prey: check the cell after move
            cellmates = grid.get_cell_list_contents([self.pos])
            prey_here = [a for a in cellmates if isinstance(a, Prey)]

            if prey_here:
                # select one prey to attempt predation (once per step)
                target = self.model.random.choice(prey_here)
                prob = self.model.predation_prob_at(self.pos)
                if self.model.random.random() < prob:
                    # successful predation
                    target.remove()
                    self.model.predation_events_this_step += 1
                    self.model.predation_events_total += 1

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

