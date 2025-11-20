import curses
from inventory import open_inventory, add_to_inventory
import sys
import json

def main(stdscr):
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    with open("player_inv.json", "r") as file:
        pl_inv = json.load(file)

    inv_grid = pl_inv["inventory_grid"]
    inv=pl_inv["inventory"]

    stdscr.clear()

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            pl_inv["inventory_grid"] = inv_grid
            pl_inv["inventory"] = inv
            with open("player_inv.json", "w") as file:
                json.dump(pl_inv, file, indent=2)
            sys.exit(0)
        elif key == ord('i'):
            inv, inv_grid = open_inventory(stdscr, inv, inv_grid)

if __name__ == "__main__":
    curses.wrapper(main)