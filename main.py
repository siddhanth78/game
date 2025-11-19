import curses
from inventory import open_inventory, add_to_inventory
import sys

def main(stdscr):
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0) 

    stdscr.clear()

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            sys.exit(0)
        elif key == ord('i'):
            inv = open_inventory(stdscr, inv)

if __name__ == "__main__":
    curses.wrapper(main)