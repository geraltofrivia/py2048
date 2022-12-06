""" The curses interface for the game """
import numpy as np
import curses
import time
import atexit
import curses
from curses.textpad import Textbox, rectangle

# Local imports
try:
    import _pathfix
except ImportError:
    from . import _pathfix
from engine import Game, CONFIG


def draw_menu(stdscr):
    inp = 0

    # Create game
    game = Game()

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)

    # Loop where inp is the last character pressed
    while inp != ord('q'):

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Load game snippet
        if inp == ord('l') or inp == ord('L'):

            # A new screen opens
            stdscr.clear()
            stdscr.refresh()

            # Collect some loadgame candidates
            info = game.get_loadgame_candidates()
            stdscr.addstr(0, 0, info)
            stdscr.addstr(CONFIG.max_loadgame_candidates+3, 0, "Enter loadgame name: (hit Ctrl-G to send)")
            editwin = curses.newwin(1, 30, CONFIG.max_loadgame_candidates+5 + 1, 1)
            rectangle(stdscr, CONFIG.max_loadgame_candidates+5, 0, CONFIG.max_loadgame_candidates+5 + 5 + 1, 1 + 30 + 1)
            # stdscr.refresh()

            box = Textbox(editwin)

            # Let the user edit until Ctrl-G is struck.
            box.edit()

            # Get resulting contents
            message = box.gather().strip()

            # We have collected the message, and now can invoke the command
            res = game.command(ord('l'), arg_b=message)
            if res == 4:

                stdscr.refresh()

                # draw another box telling that it didn't work
                # rectangle(stdscr, 1, 0, 5 + 1, 1 + 30 + 1)
                raise AssertionError
                stdscr.clear()
                stdscr.addstr(2, 2, f"Tried to load {message} but couldn't.\nPress any key to continue.")
                _ = stdscr.getch()

            stdscr.clear()

        else:

            game, status = game.command(inp)

            # Declaration of strings
            # title = "Curses example"[:width-1]
            # subtitle = "Written by Clay McLeod"[:width-1]
            # keystr = "Last key pressed: {}".format(k)[:width-1]
            statusbarstr = game.get_statusbar_message(width - 1)
            game_grid = game.grid.__repr__()

        # if k == 0:
        #     keystr = "No key press detected..."[:width-1]
        #
        # # Centering calculations
        # start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        # start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
        # start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
        # start_y = int((height // 2) - 2)

        # Rendering some text
        # whstr = "Width: {},\n Height: {}".format(width, height)
        stdscr.addstr(0, 0, game_grid, curses.color_pair(1))

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        # stdscr.addstr(height-1, len(statusbarstr), "|" * (10))
        # stdscr.addstr(height-1, len(statusbarstr), "|" * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        # stdscr.addstr(start_y, start_x_title, title)

        # Turning off attributes for title
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

        # # Print rest of text
        # stdscr.addstr(start_y + 1, start_x_subtitle, subtitle)
        # stdscr.addstr(start_y + 3, (width // 2) - 2, '-' * 4)
        # stdscr.addstr(start_y + 5, start_x_keystr, keystr)
        # stdscr.move(cursor_y, cursor_x)

        # Refresh the screen
        stdscr.refresh()

        # time.sleep(1)
        #
        # # Render status bar
        # stdscr.attron(curses.color_pair(4))
        # stdscr.addstr(height-1, 0, statusbarstr)
        # stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        # stdscr.attroff(curses.color_pair(4))

        # Wait for next input
        inp = stdscr.getch()


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    # Game()
    main()

