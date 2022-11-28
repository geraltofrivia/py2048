""" Here be dataclasses we need """
import numpy as np

from visualisation import VisualizeGrid

class Grid:
    def __init__(self, dim: int = 4, spawns: int = 1):
        """
            Grid is the fundamental thing we want to have. It is a size x size matrix.
            We have four functions: up, down, left, right which simulate movements etc
        :param dim: the size of the grid. a 2048 grid is usually `4`
        :param spawns: how many new blocks are added at each iteration
        """
        self.grid: np.ndarray = np.zeros((dim, dim), dtype=int)
        self._spawn_freq: int = spawns
        self.dim: int = dim
        self.score: int = 0
        self.viz = VisualizeGrid(align='center')

    @property
    def max(self):
        return self.grid.max()

    def spawn(self, n):
        ...

    def up(self):
        ...

    def down(self):
        ...

    def left(self):
        ...

    def right(self):
        ...

    def __repr__(self) -> str:

        header = f'A {self.dim}x{self.dim} array. '
        # Add a right aligned score?
        body = self.viz(self)

        return header + '\n' + body


if __name__ == '__main__':

    g = Grid()
    print(g)