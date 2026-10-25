from collections import deque
from dataclasses import dataclass

import numpy as np


ACTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


@dataclass
class Grid:
    walls: np.ndarray

    start: tuple[int, int]

    goal: tuple[int, int]

    def __post_init__(self):
        self.walls = np.asarray(self.walls, dtype=bool).copy()
        if self.walls.ndim != 2 or min(self.walls.shape) < 2:
            raise ValueError("Grid must be two-dimensional and at least 2 by 2.")
        for point in (self.start, self.goal):
            if not self.open(point):
                raise ValueError("Start and goal must be inside the grid on open cells.")
        if self.start == self.goal:
            raise ValueError("Start and goal must be distinct.")

    def open(self, point):
        r, c = point
        return 0 <= r < self.walls.shape[0] and 0 <= c < self.walls.shape[1] and not self.walls[r, c]

    def shortest_path(self):
        """Exact BFS reference for unit-cost moves; never used to select RL actions."""
        parents = {self.start: None}
        queue = deque([self.start])
        while queue:
            point = queue.popleft()
            if point == self.goal:
                path = []
                while point is not None:
                    path.append(point)
                    point = parents[point]
                return path[::-1]
            for dr, dc in ACTIONS:
                nxt = (point[0] + dr, point[1] + dc)
                if self.open(nxt) and nxt not in parents:
                    parents[nxt] = point
                    queue.append(nxt)
        return None

    @classmethod
    def from_text(cls, text):
        rows = text.strip().splitlines()
        if not rows or len({len(row) for row in rows}) != 1:
            raise ValueError("Map rows must have equal lengths.")
        if any(ch not in ".#SG" for row in rows for ch in row):
            raise ValueError("Map supports only '.', '#', 'S', and 'G'.")
        starts = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "S"]
        goals = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "G"]
        if len(starts) != 1 or len(goals) != 1:
            raise ValueError("Map must contain exactly one S and one G.")
        return cls(np.array([[ch == "#" for ch in row] for row in rows]), starts[0], goals[0])
