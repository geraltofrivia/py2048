""" Here be dataclasses we need """
import numpy as np
from typing import Optional, Callable

from .visualisation import VisualizeGrid


def generate_biased_two_four():
    return 4 if np.random.default_rng().uniform(0,1) > 0.8 else 2


def generate_uniform_two_four():
    return 4 if np.random.default_rng().uniform(0,1) > 0.5 else 2


class Grid:
    def __init__(self, dim: int = 4, spawns: int = 1, numgen: Optional[Callable] = None):
        """
            Grid is the fundamental thing we want to have. It is a size x size matrix.
            We have four functions: up, down, left, right which simulate movements etc
        :param dim: the size of the grid. a 2048 grid is usually `4`
        :param spawns: how many new blocks are added at each iteration
        :numgen a callable that generates a number to populate the grid. If unspecified, we
        """
        self.state: np.ndarray = np.zeros((dim, dim), dtype=int)
        self._spawn_freq: int = spawns
        self.dim: int = dim
        self.score: int = 0

        self.numgen = numgen if numgen else generate_biased_two_four

        # The lib used to visualise the grid
        self.viz = VisualizeGrid(align='center')

        # Init the game
        self.spawn(2)

    @property
    def max(self) -> int:
        return self.state.max()

    @property
    def maxchar(self):
        return max(5, len(str(self.max)))

    def set_state(self, mat: np.ndarray):
        if not self.state.shape == mat.shape or not self.state.dtype == mat.dtype:
            raise ValueError(f"Either the matrix shape: {mat.shape} is not expected i.e.: {self.state.shape}, "
                             f"or the dtype: {mat.dtype} is not expected i.e.: {self.state.dtype}")

        self.state = mat

    def spawn(self, n):
        # choose n places from empty cells
        zeros_x, zeros_y = np.where(self.state == 0)
        inds = np.random.choice(np.arange(len(zeros_x)), n)
        insert_x = zeros_x[inds]
        insert_y = zeros_y[inds]

        # choose values to insert
        values = [self.numgen() for _ in range(n)]

        self.state[insert_x, insert_y] = values

        assert len(self.state.nonzero()[0]) == 2, self.__repr__()

    @staticmethod
    def _shift_row_(row: np.ndarray) -> np.ndarray:
        """ Slide all nonzero values over the zero values """

        # Shift: slide all nonzero values over the 'zero' values
        slideto = 0
        for i, elem in enumerate(row):
            if elem != 0:
                # NONZERO VALUE: slide the value to the appropriate position and make the current cell zero;
                # and increment the slideto pointer (in both cases)
                if i == slideto:
                    # slideto pointer is at this current position. Move the pointer to a next (future) position
                    slideto = i + 1
                else:
                    # We slid the value from this position so let's move the slideto pointer here
                    row[slideto] = elem
                    row[i] = 0
                    slideto = i
            else:
                # ZERO VALUE: do nothing, don't even move the slider
                ...

        return row

    @staticmethod
    def _merge_row_(row: np.ndarray) -> np.ndarray:

        # Merge: if you find some consecutive cells, merge them. you should do the slide thing again afterwards.
        for i, curr in enumerate(row[:-1]):
            if row[i] == row[i+1] != 0:
                row[i] += row[i+1]
                row[i+1] = 0

        return row

    def _proc_row_(self, row: np.ndarray) -> np.ndarray:
        """ Run a shift and merge operation till arrays don't change. This assumes a row is undergoing the 'left' op """

        row = self._shift_row_(row)
        row = self._merge_row_(row)
        row = self._shift_row_(row)
        return row

    def up(self):

        # Go over each column and treat it as a row; add it back as a column
        for i in range(self.dim):
            self.state[:,i] = self._proc_row_(self.state[:,i])

    def down(self):

        # Go over each column and treat it as a row; invert it; add it back as a column after inverting the output
        for i in range(self.dim):
            self.state[:, i] = self._proc_row_(self.state[:, i][::-1])[::-1]

    def left(self):

        # Go over each row and simply pass to the proc row
        for i, row in enumerate(self.state):
            self.state[i] = self._proc_row_(row)

    def right(self):

        # Go over each row and simply pass to the proc row but inverted; and invert the output also
        for i, row in enumerate(self.state):
            self.state[i] = self._proc_row_(row[::-1])[::-1]

    def __repr__(self) -> str:

        header = f'A {self.dim}x{self.dim} array. '
        # Add a right aligned score?
        body = self.viz(self)

        return header + '\n' + body


if __name__ == '__main__':

    g = Grid()
    print(g)