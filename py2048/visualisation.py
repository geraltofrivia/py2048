""" Here are utils for visualisation of the grid and the game """
from abc import ABC
from typing import Optional, Callable
from math import log10, floor
import numpy as np

from .utils import mutstr


class Theme(ABC):

    def __init__(
            self,
            ver: str = '',
            hor: str = '',
            pad: str = '',
            topleftcorner: str = '',
            toprightcorner: str = '',
            bottomleftcorner: str = '',
            bottomrightcorner: str = '',
            bottominter: str = '',
            topinter: str = '',
            rightinter: str = '',
            leftinter: str = '',
            fourwayinter: str = ''
    ):
        self.hor = hor  # horizontal
        self.ver = ver  # vertical mark
        self.pad = pad  # empty space

        # Optional stuff

        # the four corners
        self.topleftcorner = topleftcorner
        self.toprightcorner = toprightcorner
        self.bottomleftcorner = bottomleftcorner
        self.bottomrightcorner = bottomrightcorner

        # Other intersections
        self.leftinter = leftinter
        self.rightinter = rightinter
        self.topinter = topinter
        self.bottominter = bottominter
        self.fourwayinter = fourwayinter

        assert bool(self.hor) and bool(self.ver) and bool(self.pad)

    def hline(self, length: int) -> str:
        """
            Does not account for cross-line intersections
            Returns a  '├────────┤'
        """
        if length < 3:
            raise ValueError(f"Length is too short: {length}. Must be at least 3 character long.")

        if self.leftinter and self.rightinter:
            default = self.leftinter + (self.hor * (length - 2)) + self.rightinter
        else:
            default = self.hor * length

        return default

    def top(self, length: int) -> str:
        """
            Does not account for cross-line intersections
            Returns a  '╭────────╮'
        """
        if length < 3:
            raise ValueError(f"Length is too short: {length}. Must be at least 3 character long.")

        if self.topleftcorner and self.toprightcorner:
            return self.topleftcorner + (self.hor * (length - 2)) + self.toprightcorner
        else:
            return self.hor * length

    def bottom(self, length) -> str:
        """
            Does not account for cross-line intersections
            Returns a '╰────────╯'
        """
        if length < 3:
            raise ValueError(f"Length is too short: {length}. Must be at least 3 character long.")

        if self.bottomleftcorner and self.bottomrightcorner:
            return self.bottomleftcorner + (self.hor * (length - 2)) + self.bottomrightcorner
        else:
            return self.hor * length

    def empty(self, celllen: int, numcells: int):
        """ Returns a │   │   │   │ """
        return self.ver + self.ver.join([self.pad * celllen for _ in range(numcells)]) + self.ver

    def intersect(self, current: str, prev_sent: Optional[str] = None, next_sent: Optional[str] = None) -> str:
        """
        Give me previous and next rows (if you have them) and we will replace the self.hor in current line with
            top intersects or bottom intersects or fourway intersects if needed.

        E.g. if
        current:    '├────────┤'
        next:       '    │  │  '

        result:     '├───┴──┴─┤'

        This only modifies those chars which are initially a self.hor so we don't overwrite any content character
        """
        if not (self.topinter and self.bottominter and self.fourwayinter):
            return current

        prev_sent = ' ' * len(current) if not prev_sent else prev_sent
        next_sent = ' ' * len(current) if not next_sent else next_sent
        if not len(current) == len(prev_sent):
            raise ValueError(f"Unequal length of previous and current string. Len current: {len(current)}. "
                             f"Len prev: {len(prev_sent)}")
        if not len(current) == len(next_sent):
            raise ValueError(f"Unequal length of next and current string. Len next: {len(next_sent)}. "
                             f"Len current: {len(current)}.")

        intersections = current[::]
        for i, (char, char_p, char_n) in enumerate(zip(current, prev_sent, next_sent)):
            if char != self.hor: continue
            if char_p in [self.ver, self.topinter] and char_n in [self.ver, self.bottominter]:
                current = mutstr(current, i, self.fourwayinter)
            elif char_p in [self.ver, self.topinter]:
                current = mutstr(current, i, self.bottominter)
            elif char_n in [self.ver, self.bottominter]:
                current = mutstr(current, i, self.topinter)
            else:
                ...
        return current


class Rounded(Theme):

    def __init__(self):
        super().__init__(
            ver='│',
            hor='─',
            pad=' ',
            topleftcorner='╭',
            toprightcorner='╮',
            bottomleftcorner='╰',
            bottomrightcorner='╯',
            bottominter='┴',
            topinter='┬',
            rightinter='┤',
            leftinter='├',
            fourwayinter='┼'
        )


class VisualizeGrid:

    def __init__(
            self,
            theme: str = 'Rounded',
            pad_hor: int = 1,
            pad_ver: int = 0,
            align='center'):

        if theme.lower() == 'rounded':
            self.theme: Theme = Rounded()
        else:
            raise ValueError(f'Unrecognized theme string.')

        if align.lower() == 'left':
            self.align: Callable = str.rjust
        elif align.lower() == 'right':
            self.align: Callable = str.ljust
        elif align.lower() == 'center':
            self.align: Callable = str.center
        else:
            raise ValueError(f"Unrecognized align string: {align}. Expected 'left', 'right', or 'center'.")

        self.pad_hor: int = pad_hor
        self.pad_ver: int = pad_ver

    def _make_row_(self, row: np.ndarray, val_len: int):
        # return self.ver + self.ver.join([self.pad*celllen for _ in range(numcells)]) + self.ver
        # noinspection PyArgumentList
        row = [self.align(str(num), val_len, self.theme.pad) for num in row]
        return self.theme.ver + self.theme.ver.join([self.theme.pad + cellval + self.theme.pad for cellval in row]) + \
               self.theme.ver

    def __call__(self, grid):
        """ Give it an initialized grid """
        val_len = grid.maxchar
        cell_len = val_len + (2 * self.pad_hor)

        # left border + all cell content + cell borders + right border
        row_len = 1 + (grid.dim * cell_len) + (grid.dim - 1) + 1

        # Let's start
        quarry = [self.theme.top(row_len)]
        for rowid in range(grid.dim):
            quarry += [self.theme.empty(cell_len, grid.dim) for _ in range(self.pad_ver)]
            quarry += [self._make_row_(grid.grid[rowid], val_len)]
            quarry += [self.theme.empty(cell_len, grid.dim) for _ in range(self.pad_ver)]
            if not rowid == grid.dim-1:
                quarry += [self.theme.hline(row_len)]
        quarry += [self.theme.bottom(row_len)]

        # Now to manage intersections
        quarry[0] = self.theme.intersect(quarry[0], next_sent=quarry[1])
        for i in range(1, len(quarry)-1):
            quarry[i] = self.theme.intersect(quarry[i], prev_sent=quarry[i-1], next_sent=quarry[i+1])
        quarry[-1] = self.theme.intersect(quarry[-1], prev_sent=quarry[i-2])

        return '\n'.join(quarry)

    def game_over(self, grid):

        ...
