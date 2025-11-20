import curses
import json
import sys

def load_art():
    with open("item_art.json", "r") as file:
        art = json.load(file)
    return art

def load_inventory(stdscr, inv_grid):
    stdscr.erase()
    for i in range(len(inv_grid)):
        for j in range(len(inv_grid[0])):
            stdscr.addstr(i, j, inv_grid[i][j])
    stdscr.refresh()

def update(stdscr, display, place, status, items, curr, inv):
    stdscr.erase()
    c = 0
    for i in range(len(display)):
        for j in range(len(display[0])):
            stdscr.addstr(i, j, display[i][j])
        if c <= len(items)-1:
            if c == curr:
                disp_inv_text = f"> {items[c]}: Lvl {inv[items[c]]["level"]}"
            else:
                disp_inv_text = f"{items[c]}: Lvl {inv[items[c]]["level"]}"
            stdscr.addstr(i, j+5, disp_inv_text)
        c += 1
    if place == True:
        stdscr.addstr(len(display)+2, 0, "Place item")
    if status != "":
        stdscr.addstr(len(display)+3, 0, status)
    stdscr.refresh()


def check_fit(display, top_left, bottom_right):
    for i in range(top_left[1], bottom_right[1]+1):
        for j in range(top_left[0], bottom_right[0]+1):
            if display[i][j] not in [".", "+"]:
                display[i][j] = "X"
            else:
                display[i][j] = "+"
    return display

def add_to_inventory(inv_grid, display, top_left, bottom_right, inv, item, art):
    if any("X" in row for row in display) == True:
        return inv_grid, display, "Couldn't place item"
    elif "anchors" in inv[item]:
        return inv_grid, display, "Item already placed"
    else:
        inv[item]["anchors"] = [top_left, bottom_right]
        a,b = 0,0
        for i in range(top_left[1], bottom_right[1]+1):
            for j in range(top_left[0], bottom_right[0]+1):
                inv_grid[i][j] = art[item][b][a]
                a += 1
            b += 1
            a = 0
    
        return inv_grid, [row[:] for row in inv_grid], "Placed item"


def open_inventory(stdscr, inv, inv_grid):
    stdscr.clear()
    art = load_art()
    c = 0
    items = list(inv.keys())
    item = items[c]
    height = len(art[items[c]])
    width = len(art[items[c]][0])
    top_left = [0,0]
    bottom_right = [width-1, height-1]
    display = [row[:] for row in inv_grid]
    load_inventory(stdscr, inv_grid)
    place = False
    status = ""

    curses.noecho()
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            return inv, inv_grid
        elif key == ord('j') or key == curses.KEY_UP:
            if place == True:
                if top_left[1]-1 >= 0:
                    display[bottom_right[1]][top_left[0]: bottom_right[0]+1] = [row[:] for row in inv_grid][bottom_right[1]][top_left[0]: bottom_right[0]+1]
                    top_left[1] -= 1
                    bottom_right[1] -= 1
                display = check_fit(display, top_left, bottom_right)
            else:
                c -= 1
                if c < 0:
                    c = 0
                item = items[c]
                height = len(art[items[c]])
                width = len(art[items[c]][0])
                top_left = [0,0]
                bottom_right = [width-1, height-1]
        elif key == ord('k') or key == curses.KEY_DOWN:
            if place == True:
                if top_left[1]+1 <= len(inv_grid)-1:
                    display[top_left[1]][top_left[0]: bottom_right[0]+1] = [row[:] for row in inv_grid][top_left[1]][top_left[0]: bottom_right[0]+1]
                    top_left[1] += 1
                    bottom_right[1] += 1
                display = check_fit(display, top_left, bottom_right)
            else:
                c += 1
                if c > len(inv)-1:
                    c = len(inv)-1
                item = items[c]
                height = len(art[items[c]])
                width = len(art[items[c]][0])
                top_left = [0,0]
                bottom_right = [width-1, height-1]
        elif key == ord('a') or key == curses.KEY_LEFT:
            if place == True:
                if top_left[0]-1 >= 0:
                    temp_grid = [row[:] for row in inv_grid]
                    for i in range(top_left[1], bottom_right[1]+1):
                        display[i][bottom_right[0]] = temp_grid[i][bottom_right[0]]
                    top_left[0] -= 1
                    bottom_right[0] -= 1
                display = check_fit(display, top_left, bottom_right)
        elif key == ord('d') or key == curses.KEY_RIGHT:
            if place == True:
                if top_left[0]+1 <= len(inv_grid[0])-1:
                    temp_grid = [row[:] for row in inv_grid]
                    for i in range(top_left[1], bottom_right[1]+1):
                        display[i][top_left[0]] = temp_grid[i][top_left[0]]
                    top_left[0] += 1
                    bottom_right[0] += 1
                display = check_fit(display, top_left, bottom_right)
        elif key == ord('p'):
            place = not place
            if place == True:
                display = check_fit(display, top_left, bottom_right)
            else:
                display = [row[:] for row in inv_grid]
        elif key == ord('m'):
            move = not move
            if place == True:
                display = check_fit(display, top_left, bottom_right)
            else:
                display = [row[:] for row in inv_grid]
        elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
            if place == True:
                inv_grid, display, status = add_to_inventory(inv_grid, display, top_left, bottom_right, inv, item, art)
                if status == "Placed item":
                    place = False
        update(stdscr, display, place, status, items, c, inv)

if __name__ == "__main__":
    curses.wrapper(open_inventory)