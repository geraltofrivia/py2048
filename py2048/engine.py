""" Here be dataclasses we need """
import json
import curses
import random
import numpy as np
from pathlib import Path
from typing import Optional, Callable, List
from random_username.generate import generate_username

from visualisation import VisualizeGrid
from utils import FancyDict, NoFreeCells, nparr_to_dict, dict_to_nparr, UnknownSessionID, VisualisationError

CONFIG = FancyDict(**{
    'seed': 42,
    'savedir': Path('./saves')
})

random.seed(CONFIG.seed)
np.random.seed(CONFIG.seed)

ASCII = FancyDict(**{
    's': 115,
    'S': 83,
    'q': 113,
    'Q': 81,
    'l': 107,
    'L': 76,
    'n': 110,
    'N': 78,
    'h': 104,
    'H': 72,
})
ARROWS = {curses.KEY_UP: '↑', curses.KEY_DOWN: '↓', curses.KEY_LEFT: '←', curses.KEY_RIGHT: '→'}


def generate_biased_two_four():
    return 4 if np.random.default_rng().uniform(0, 1) > 0.8 else 2


def generate_uniform_two_four():
    return 4 if np.random.default_rng().uniform(0, 1) > 0.5 else 2


class Grid:
    def __init__(self, dim: int = 4, spawns: int = 1, numgen: Optional[Callable] = None, debug: bool = False):
        """
            Grid is the fundamental thing we want to have. It is a size x size matrix.
            We have four functions: up, down, left, right which simulate movements etc
        :param dim: the size of the grid. a 2048 grid is usually `4`
        :param spawns: how many new blocks are added at each iteration
        :numgen a callable that generates a number to populate the grid. If unspecified, we
        """
        self.vals: np.ndarray = np.zeros((dim, dim), dtype=np.int32)
        self._old_vals: np.ndarray = np.zeros((dim, dim), dtype=np.int32)
        self._spawn_freq: int = spawns
        self.dim: int = dim
        self._debug = debug

        self.numgen: Callable = numgen if numgen else generate_biased_two_four

        # The lib used to visualise the grid
        self.viz: VisualizeGrid = VisualizeGrid(align='center')

        # Init the game
        self.spawn(2)

    def serialise(self) -> dict:
        # To make a nice json thing
        return {
            'vals': nparr_to_dict(self.vals),
            'numgen': self.numgen.__name__,
            'spawns': self._spawn_freq,
            'dim': self.dim
        }

    @classmethod
    def de_serialize(cls, data: dict) -> 'Grid':
        # To make a nice json thing into an object
        numgen = locals()[data['numgen']]
        grid = Grid(dim=data['dim'], spawns=data['spawns'], numgen=numgen)
        vals = dict_to_nparr(data['vals'])
        grid.set_vals(vals)
        return grid

    @property
    def max(self) -> int:
        return self.vals.max()

    @property
    def maxchar(self):
        return max(5, len(str(self.max)))

    def set_vals(self, mat: np.ndarray):
        if not self.vals.shape == mat.shape or not self.vals.dtype == mat.dtype:
            raise ValueError(f"Either the matrix shape: {mat.shape} is not expected i.e.: {self.vals.shape}, "
                             f"or the dtype: {mat.dtype} is not expected i.e.: {self.vals.dtype}")

        self.vals = mat

    @property
    def is_stuck(self) -> bool:
        return (self.vals == self._old_vals).all()

    @property
    def is_over(self) -> bool:
        return (self.vals != 0).all()

    def spawn(self, n=-1):

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
                    slideto += 1
            else:
                # ZERO VALUE: do nothing, don't even move the slider
                ...

        return row

    @staticmethod
    def _merge_row_(row: np.ndarray) -> (np.ndarray, List[int]):
        merges = []

        # Merge: if you find some consecutive cells, merge them. you should do the slide thing again afterwards.
        for i, curr in enumerate(row[:-1]):
            if row[i] == row[i + 1] != 0:
                row[i] += row[i + 1]
                merges.append(row[i])  # the new cell so if we merged 2+2 = 4, we note 4
                row[i + 1] = 0

        return row, merges

    def _proc_row_(self, row: np.ndarray) -> (np.ndarray, List[int]):
        """ Run a shift and merge operation till arrays don't change. This assumes a row is undergoing the 'left' op """
        if self._debug:
            print('-------------------- AT START --------------------')
            print(row)
        row = self._shift_row_(row)
        if self._debug:
            print('-------------------- AFTER FIRST SHIFT --------------------')
            print(row)
        row, merges = self._merge_row_(row)
        if self._debug:
            print('-------------------- AFTER MERGE --------------------', merges)
            print(row)
        row = self._shift_row_(row)
        if self._debug:
            print('-------------------- AFTER SECOND SHIFT --------------------')
            print(row)
            print('-------------------- END END --------------------')

        return row, merges

    def up(self) -> List[int]:

        # overwrite old_val mat by current val mat
        self._old_vals = np.copy(self.vals)

        # Go over each column and treat it as a row; add it back as a column
        merges = []
        for i in range(self.dim):
            op =  self._proc_row_(self.vals[:, i])
            self.vals[:, i] = op[0]
            merges += op[1]


        return merges

    def down(self) -> List[int]:

        # overwrite old_val mat by current val mat
        self._old_vals = np.copy(self.vals)

        # Go over each column and treat it as a row; invert it; add it back as a column after inverting the output
        merges = []
        for i in range(self.dim):
            op =  self._proc_row_(self.vals[:, i][::-1])
            self.vals[:, i] = op[0][::-1]
            merges += op[1]

        return merges

    def left(self) -> List[int]:

        # overwrite old_val mat by current val mat
        self._old_vals = np.copy(self.vals)

        # Go over each row and simply pass to the proc row
        merges = []
        for i, row in enumerate(self.vals):
            op =  self._proc_row_(row)
            self.vals[i] = op[0]
            merges += op[1]

        return merges

    def right(self) -> List[int]:

        # overwrite old_val mat by current val mat
        self._old_vals = np.copy(self.vals)

        # Go over each row and simply pass to the proc row but inverted; and invert the output also
        merges = []
        for i, row in enumerate(self.vals):
            op =  self._proc_row_(row[::-1])
            self.vals[i] = op[0][::-1]
            merges += op[1]

        return merges

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

    def __init__(self, grid: Optional[Grid] = None, history: Optional[List[int]] = None, score: Optional[int] = None,
                 session_id: str = None, debug: bool = False):

        # All the state variables
        self.grid = Grid(debug=debug) if not grid else grid
        self.history: List[int] = [] if not history else history
        self.score = 0 if not score else score
        self.session_id = self._gen_session_id_() if not session_id else session_id
        self.message = ''  # This message is updated at commands, and is queried as needed for the UI

        # Shortcut to the visualization thing
        self.viz = self.grid.viz

    def get_statusbar_message(self, width: int) -> str:
        """
            Left aligned: 8d score | instruction: press h for help |
            Right aligned: 8long history (←↑→↓ | session ID)
            Width: whitespace padding

            If the combined length of left and right text is less than width; we only keep the left.
            If width is even less than left width; raise assertion

            TODO: add curses formatting support here
        :return: str
        """
        left = f"{self.score:8d} | {self.message if self.message else 'Press h for help.'}"
        history = ' '.join([ARROWS[direction] for direction in self.history[:-15:-1]][::-1])
        right = f"{history} | {self.session_id}"

        if len(left) + len(right) > width:
            # Render only left
            if len(left) > width:
                raise VisualisationError(f"Width too narrow for statusbar. Must be at least {len(left)}. Is {width}.")
            pad = ' '*(width - len(left))
            return left + pad
        else:
            pad = ' '*(width - len(left) - len(right))
            return left + pad + right

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
        return save_fnm.stem

    @classmethod
    def _newgame_(cls) -> 'Game':
        """ Return a new object of this class (or something) """
        return Game()

    def command(self, arg_a: int, arg_b: Optional[str] = None) -> ('Game', int):
        """
            The commands are passed here almost raw.

            The function called to interact with the grid.
            The possible commands we expect include:
                -> newgame (ASCII for 'n' or 'N')
                -> move directions (up/down/left/right) (ascii for arrows)
                -> load (with dir)
                -> save (ASCII for 's' or 'S')
                -> help (ASCII for 'h' or 'H')
        :return: status code:
            1. called save and save successful
            2. called save and save unsuccessful
            3. called load and load successful
            4. called load and load unsuccessful
            5. called newgame and newgame loaded
            6. called help and help message shown
            7. direction arrow given and it changed the state
            8. direction arrow given and it didnt change the state
            9. direction arrow given and game over | game was over when arrow was sent
            10. unknown command
        """

        self.message = ''

        # save
        if arg_a == ASCII.s or arg_a == ASCII.S:
            try:
                save_fname = self._save_()
                self.message = f'File saved to {save_fname}'
                return self, 1
            except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
                self.message = f'Save unsuccessful. {type(e)}: {e.args}.'
                return self, 2

        # load
        elif arg_a == ASCII.l or arg_a == ASCII.L:
            try:
                newgame_obj = self._load_(arg_b)
                newgame_obj.message = 'Just loaded from disk.'
                return newgame_obj, 3
            except (UnknownSessionID, ValueError) as e:
                self.message = f'Unable to load this session. {type(e)}: {e.args}.'
                return self, 4

        # newgame
        elif arg_a == ASCII.n or arg_a == ASCII.N:
            self.message = ''
            return self._newgame_(), 5

        elif arg_a == ASCII.h or arg_a == ASCII.H:
            self.message = 'Press s to save; n for newgame; l to load or q to quit.'
            return self, 6

        # direction: up or down or left or right
        elif arg_a in [curses.KEY_DOWN, curses.KEY_UP, curses.KEY_RIGHT, curses.KEY_LEFT]:

            """Stuff before invoking state change"""
            # See if the game is over, in which case send a game over message and dont move the grid.
            if self.grid.is_over:
                self.message = 'Game over. Press n for newgame or q to quit.'
                return self, 9

            """Invoking state change"""
            if arg_a == curses.KEY_UP:
                merges = self.grid.up()
            elif arg_a == curses.KEY_DOWN:
                merges = self.grid.down()
            elif arg_a == curses.KEY_LEFT:
                merges = self.grid.left()
            elif arg_a == curses.KEY_RIGHT:
                merges = self.grid.right()
            else:
                raise NotImplementedError("Code will never come here, this is only to calm PyCharm down.")

            """Post invoking state change"""

            self.history.append(arg_a)          # log the direction
            self.score += sum(merges)           # update score

            # Is it game over? (do the game over fn)
            if self.grid.is_over:
                self.message = 'Game over. Press n for newgame or q to quit.'
                return self, 9

            # See if something changed in the grid, if so, spawn
            if not self.grid.is_stuck:
                self.grid.spawn()               # spawn new values
                return self, 7
            else:
                self.message = 'No change. Try another direction ;)'
                return self, 8

        else:
            self.message = ''
            return self, 10

    def __del__(self):
        """
            Save the current game to disk if there is some activity in this session
            Do other things?
        :return:
        """
        if len(self.history) > 0:
            self._save_()

    def _save_(self) -> Path:
        """
            To dump the current game to disk
        :return:
        """

        # Prepare the entire saving thing
        save_dict = {
            'grid': self.grid.serialise(),
            'score': int(self.score),
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
        savename = CONFIG.savedir / f"{session_id}.json"

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
    g = Game(debug=True)
    print(g.grid)
    print(g.score)
    while True:

        cmd = input('Write your command here: ').strip().lower()
        if cmd == 'w':
            g.command(curses.KEY_UP)
        if cmd == 's':
            g.command(curses.KEY_DOWN)
        if cmd == 'a':
            g.command(curses.KEY_LEFT)
        if cmd == 'd':
            g.command(curses.KEY_RIGHT)
        if cmd == 'e':
            g.command(115)
        if cmd == 'q':
            break
            # g.command(113)
        print(g.grid)
        print(g.score)
    # print(g)
