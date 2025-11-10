import curses
from inventory import inventory, add_to_inv

all_merge = ["Sword: 5 wood 5 iron", "Shield: 5 wood 5 iron", "Axe: 5 wood 5 iron", "Radon: 40 wood 40 iron 500 coins"]

def update(stdscr, inv, inv_len, coins):
    stdscr.addstr(0,0,"Available items:")
    for i in range(inv_len):
        inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(i+1, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, f"Coins: {coins}")
    stdscr.addstr(inv_len+3, 0, "m:merge | b:build | q:exit")

def build_(stdscr, inv, inv_len):
    
    pass

def merge_items(stdscr, inv, inv_len, coins):
    selected_items = []
    stdscr.clear()
    for i in range(len(all_merge)):
        stdscr.add(i, 0, all_merge[i])
    while True:
        key = stdscr.getch()
        if key == ord('a'):
            item = inventory(stdscr, inv)
            if item:
                selected_items.append(item)
        elif key == ord('d'):
            deleted = selected_items.pop()

def run_forge(stdscr, inv, coins):
    inv_len = len(inv)
    stdscr.clear()
    update(stdscr, inv, inv_len, coins)
    while True:
        key = stdscr.getch()

        if key == ord('q'):
            return None
        elif key == ord('b'):
            build_(stdscr, inv, inv_len, coins)
        elif key == ord('m'):
            merge_items(stdscr, inv, inv_len, coins)

        update(stdscr, inv, inv_len, coins)


def start_forge(stdscr, inv, coins):
    stdscr.clear()
    stdscr.addstr(1,0,"Enter forge? (y/n)")
    key = stdscr.getch()
    if key == ord('y'):
        run_forge(stdscr, inv, coins)
    else:
        pass
    return inv, coins