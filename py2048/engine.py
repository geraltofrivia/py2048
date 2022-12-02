""" Here be dataclasses we need """
import json
import random
import numpy as np
from pathlib import Path
from typing import Optional, Callable, List
from random_username.generate import generate_username

from visualisation import VisualizeGrid
from utils import FancyDict, NoFreeCells, nparr_to_dict, dict_to_nparr, UnknownSessionID

CONFIG = FancyDict(**{
    'seed':42,
    'savedir': './saves'
})

random.seed(CONFIG.seed)
np.random.seed(CONFIG.seed)


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
        self.vals: np.ndarray = np.zeros((dim, dim), dtype=int)
        self._spawn_freq: int = spawns
        self.dim: int = dim
        self.score: int = 0

        self.numgen: Callable = numgen if numgen else generate_biased_two_four

        # The lib used to visualise the grid
        self.viz: VisualizeGrid = VisualizeGrid(align='center')

        # Init the game
        self._spawn_(2)

    def serialise(self) -> dict:
        # To make a nice json thing
        ...

    @classmethod
    def de_serialize(self, data: dict):
        # To make a nice json thing into an object
        ...

    @property
    def max(self) -> int:
        return self.vals.max()

    @property
    def maxchar(self):
        return max(5, len(str(self.max)))

    def set_state(self, mat: np.ndarray):
        if not self.vals.shape == mat.shape or not self.vals.dtype == mat.dtype:
            raise ValueError(f"Either the matrix shape: {mat.shape} is not expected i.e.: {self.vals.shape}, "
                             f"or the dtype: {mat.dtype} is not expected i.e.: {self.vals.dtype}")

        self.vals = mat

    @property
    def is_stuck(self) -> bool:
        return np.any(self.vals == 0)

    def _spawn_(self, n=-1):

        if n < 0:
            n = self._spawn_freq

        # choose n places from empty cells
        zeros_x, zeros_y = np.where(self.vals == 0)

        if len(zeros_x) < n:
            raise NoFreeCells(f"There are not enough free positions to spawn values into.")

        inds = np.random.choice(np.arange(len(zeros_x)), n)
        insert_x = zeros_x[inds]
        insert_y = zeros_y[inds]

        # choose values to insert
        values = [self.numgen() for _ in range(n)]

        self.vals[insert_x, insert_y] = values

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
            self.vals[:, i] = self._proc_row_(self.vals[:, i])

    def down(self):

        # Go over each column and treat it as a row; invert it; add it back as a column after inverting the output
        for i in range(self.dim):
            self.vals[:, i] = self._proc_row_(self.vals[:, i][::-1])[::-1]

    def left(self):

        # Go over each row and simply pass to the proc row
        for i, row in enumerate(self.vals):
            self.vals[i] = self._proc_row_(row)

    def right(self):

        # Go over each row and simply pass to the proc row but inverted; and invert the output also
        for i, row in enumerate(self.vals):
            self.vals[i] = self._proc_row_(row[::-1])[::-1]

    def __repr__(self) -> str:

        # Add a right aligned score?
        body = self.viz(self)

        return self.viz(self)


class Game:
    """
        This uses the grid to create an actual game.
        This takes care of the 'scoring' part. This takes care of game over state.
        This keeps histories of commands and history of states
    """
    def __init__(self, grid: Optional[Grid] = None, history: Optional[List[str]] = None, score: Optional[int] = None,
                 session_id: str = None):

        # All the state variables
        self.grid = Grid() if not grid else grid
        self.history: List[str] = [] if not history else history
        self.score = 0 if not score else score
        self.session_id = self._gen_session_id_() if not session_id else session_id

    @property
    def save_fname(self):
        return CONFIG.savedir / f"{self.session_id}.json"

    @staticmethod
    def _gen_session_id_():
        """ Gen a session ID and see if this is already saved to disk """

        # See if the main dir exists or not
        save_loc: Path = CONFIG.savedir
        save_loc.mkdir(exist_ok=True)

        # If we want a new file
        session_id = generate_username()[0]
        save_fnm = save_loc / (session_id + '.json')
        while save_fnm.exists():
            session_id = generate_username()[0]
            save_fnm = save_loc / (session_id + '.json')
        return save_fnm

    @classmethod
    def _newgame_(cls) -> 'Game':
        """ Return a new object of this class (or something) """
        return Game()

    def command(self, arg_a: str, arg_b: Optional[str] = None) -> ('Game', str):
        """
            The commands are passed here almost raw.

            The function called to interact with the grid.
            The possible commands we expect include:
                -> newgame
                -> move directions (up/down/left/right)
                -> load (with dir)
                -> save
        :param direction:
        :return:
        """

        # save
        if arg_a == 's':
            save_fname = self._save_()
            return self, f'File saved to {save_fname}'

        # load
        elif arg_a == 'l':
            try:
                newgame_obj = self._load_(arg_b)
            except (UnknownSessionID, ValueError) as e:
                self, f'Unable to load this session. {type(e)}: {e.args}'

        # newgame
        elif arg_a == 'n':
            return self._newgame_(), ''

        # direction: up or down or left or right
        elif arg_a in ['up']:
            # TODO: the core core logic comes here
            ...

    def _atexit_(self):
        """
            Save the current game to disk if there is some activity in this session
            Do other things?
        :return:
        """
        if len(self.history) > 0:
            print
            self._save_()

    def _save_(self) -> Path:
        """
            To dump the current game to disk
        :return:
        """

        # Prepare the entire saving thing
        save_dict = {
            'grid': self.grid.serialise(),
            'score': self.score,
            'history': self.history,
            'session_id': self.session_id
        }

        try:
            json.dump(save_dict, self.save_fname.open('w+'))
        except (TypeError, FileNotFoundError) as e:
            raise e

        return self.save_fname

    @classmethod
    def _load_(cls, session_id: str) -> 'Game':
        """
            Load things from a savefile (including history and state)
        :param savename:
        :return:
        """
        # Check if savename is just the filename or the entire dir, and ensure it is a proper path
        savename =  CONFIG.savedir / f"{session_id}.json"

        # Load the stuff
        try:
            saved_content = json.load(savename.open('r'))
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            raise UnknownSessionID(f"No session savefile found at {savename}.")

        if session_id != saved_content['session_id']:
            raise ValueError(f"Session ID differs from filename: {session_id} and "
                             f"the content inside: {saved_content['session_id']}. "
                             f"Something went terribly wrong.")

        # Make a grid obj
        grid: Grid = Grid.de_serialize(saved_content['grid'])

        # And now make a new self
        return Game(grid=grid, history=saved_content['history'],
                    score=saved_content['score'], session_id=saved_content['session_id'])


if __name__ == '__main__':

    g = Grid()
    print(g)