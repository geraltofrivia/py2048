import numpy as np
from py2048.engine import Grid

class TestGridShifts:

    def test_proc_rows(self):
        """
            We set the state for a row and see if the row is changed as expected
        :return:
        """
        grid = Grid()

        inputs = [
            [0, 0, 0, 0],
            [2, 4, 0, 0],
            [4, 2, 2, 0],
            [2, 0, 2, 0],
            [2, 2, 2, 2],
            [0, 2, 0, 0],
            [0, 2, 2, 0],
            [0, 2, 0, 2],
            [2, 0, 2, 2]
        ]

        outputs = [
            [0, 0, 0, 0],
            [2, 4, 0, 0],
            [4, 4, 0, 0],
            [4, 0, 0, 0],
            [4, 4, 0, 0],
            [2, 0, 0, 0],
            [4, 0, 0, 0],
            [4, 0, 0, 0],
            [4, 2, 0, 0]
        ]

        for _inp, _op in zip(inputs, outputs):
            _inp = np.array(_inp)
            _op = np.array(_op)

            assert np.all(_op == grid._proc_row_(_inp)), f"INPUT:         {_inp}," \
                                                         f"\nOUTPUT:        {_op}," \
                                                         f"\nACTUAL OUTPUT: {grid._proc_row_(_inp)}"


class TestGridConsistency:
    ...


class TestGridInits:
    ...