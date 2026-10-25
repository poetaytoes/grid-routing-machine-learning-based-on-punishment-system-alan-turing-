"""Inspectable tabular Q-learning for the Learning Machine coursework."""
from dataclasses import asdict, dataclass
import math
import random

from .environment import Grid

ACTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
ACTION_NAMES = ("Up", "Right", "Down", "Left")
MAPS = {
    "grid5": "S....\n.XXX.\n...X.\n.X...\n...XG",
    "grid8": "S..X....\nXX.X.XX.\n...X....\n.XXXXX.X\n.......X\n.XXXXX.X\n.....X..\nXXXX...G",
    "blocked": "S....\nXXXXX\n.....\n.....\n....G",
}


@dataclass
class Settings:
    grid: str = "grid5"
    episodes: int = 500
    seed: int = 42
    goal: float = 10
    invalid: float = -5
    step: float = -1
    alpha: float = .2
    gamma: float = .95

    def validate(self):
        if self.grid not in MAPS:
            raise ValueError("Unknown grid")
        if type(self.episodes) is not int or not 1 <= self.episodes <= 5000:
            raise ValueError("Episodes must be an integer from 1 to 5000")
        if type(self.seed) is not int or not 0 <= self.seed <= 1000000:
            raise ValueError("Seed must be an integer from 0 to 1000000")
        for field in ("goal", "invalid", "step", "alpha", "gamma"):
            value = getattr(self, field)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Rewards and learning parameters must be finite numbers")
        if not 0 < self.goal <= 100 or not -100 <= self.invalid <= -5 or not -5 <= self.step < 0:
            raise ValueError("Goal must be positive, invalid move <= -5, ordinary step negative")
        if not 0 < self.alpha <= 1 or not 0 <= self.gamma < 1:
            raise ValueError("Require 0 < alpha <= 1 and 0 <= gamma < 1")


def transition(grid, position, action, settings):
    if type(action) is not int or action not in range(4):
        raise ValueError("Action must be 0, 1, 2 or 3")
    dr, dc = ACTIONS[action]
    nxt = (position[0] + dr, position[1] + dc)
    if not grid.open(nxt):
        return position, settings.invalid, False, True
    goal = nxt == grid.goal
    return nxt, settings.goal if goal else settings.step, goal, False


def update(q, state, action, reward, nxt, terminal, alpha, gamma):
    old = q[state][action]
    future = 0.0 if terminal else max(q[nxt])
    target = reward + gamma * future
    q[state][action] += alpha * (target - old)
    return {"q_before": old, "future": future, "target": target, "q_after": q[state][action]}


class Lesson:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.settings.validate()
        self.grid = Grid.from_text(MAPS[self.settings.grid].replace("X", "#"))
        self.size = len(self.grid.walls)
        self.reference = self.grid.shortest_path()
        self.q = [[0.0] * 4 for _ in range(self.size ** 2)]
        self.rng = random.Random(self.settings.seed)
        self.limit = 4 * self.size ** 2
        self.history, self.checkpoints = [], []
        self.episode = 0
        self.status = "ready" if self.reference else "UNSOLVABLE"
        self.before = self.evaluate()
        self.checkpoints.append({"episode": 0, **self.before})
        self.first_episode = None
        self.last_episode = None
        self.last_update = None
        self.reset_episode()

    def index(self, position):
        return position[0] * self.size + position[1]

    def reset_episode(self):
        self.position = self.grid.start
        self.path, self.events = [self.position], []
        self.total, self.errors = 0.0, 0
        self.epsilon = max(.05, 1 - .95 * self.episode / max(1, self.settings.episodes * .8))

    def evaluate(self):
        if self.reference is None:
            return {"status": "UNSOLVABLE", "success": False, "path": [], "attempted_path": [],
                    "steps": 0, "reward": 0, "optimal": False, "source": "exact_reachability"}
        position = self.grid.start
        path, seen, score = [position], {position}, 0.0
        for step in range(1, self.limit + 1):
            action = max(range(4), key=lambda a: self.q[self.index(position)][a])
            position, reward, done, _ = transition(self.grid, position, action, self.settings)
            score += reward
            path.append(position)
            if done:
                assert path[0] == self.grid.start and path[-1] == self.grid.goal
                assert len(set(path)) == len(path)
                return {"status": "SOLVED", "success": True, "path": path, "attempted_path": path,
                        "steps": step, "reward": score, "optimal": step == len(self.reference)-1,
                        "source": "q_policy"}
            if position in seen:
                break
            seen.add(position)
        return {"status": "AGENT_FAILED", "success": False, "path": [], "attempted_path": path,
                "steps": step, "reward": score, "optimal": False, "source": "q_policy"}

    def advance(self, count=1):
        if type(count) is not int or not 1 <= count <= 500:
            raise ValueError("Step count must be from 1 to 500")
        if self.status in ("complete", "UNSOLVABLE"):
            return
        self.status = "learning"
        for _ in range(count):
            if self.episode >= self.settings.episodes:
                break
            if self.last_episode is not None and len(self.history) == self.episode and self.position is None:
                self.reset_episode()
            state = self.index(self.position)
            exploring = self.rng.random() < self.epsilon
            if exploring:
                action = self.rng.randrange(4)
            else:
                best = max(self.q[state])
                action = self.rng.choice([a for a in range(4) if self.q[state][a] == best])
            previous = self.position
            nxt, reward, terminal, invalid = transition(self.grid, previous, action, self.settings)
            details = update(self.q, state, action, reward, self.index(nxt), terminal,
                             self.settings.alpha, self.settings.gamma)
            self.position = nxt
            self.total += reward
            self.errors += int(invalid)
            self.path.append(nxt)
            event = {"step": len(self.events)+1, "state": previous, "action": ACTION_NAMES[action],
                     "next_state": nxt, "reward": reward, "total_reward": self.total, "invalid": invalid,
                     "terminal": terminal, "exploring": exploring, "epsilon": self.epsilon, **details}
            self.events.append(event)
            self.last_update = event
            truncated = len(self.events) >= self.limit and not terminal
            if terminal or truncated:
                self.episode += 1
                record = {"episode": self.episode, "reward": self.total, "steps": len(self.events),
                          "steps_to_goal": len(self.events) if terminal else None, "success": terminal,
                          "errors": self.errors, "epsilon": self.epsilon, "truncated": truncated}
                self.history.append(record)
                self.last_episode = {**record, "path": self.path[:], "events": self.events[:]}
                if self.first_episode is None:
                    self.first_episode = self.last_episode
                if self.episode % 25 == 0 or self.episode == self.settings.episodes:
                    self.checkpoints.append({"episode": self.episode, **self.evaluate()})
                self.position = None
                if self.episode == self.settings.episodes:
                    self.status = "complete"
                    break

    def snapshot(self):
        return {"settings": asdict(self.settings), "map": MAPS[self.settings.grid], "status": self.status,
                "episode": self.episode, "epsilon": self.epsilon, "max_steps": self.limit,
                "optimal_steps": len(self.reference)-1 if self.reference else None,
                "position": self.position or self.path[-1], "path": self.path,
                "last_update": self.last_update, "history": self.history, "q": self.q,
                "before": self.before, "after": self.evaluate(), "first_episode": self.first_episode,
                "last_episode": self.last_episode, "checkpoints": self.checkpoints,
                "scorer_report": {"status": "UNSOLVABLE", "source": "exact_reachability", "score": 0}
                    if self.reference is None else None}
