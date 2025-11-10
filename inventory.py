import curses

def update_inv(stdscr, inv, inv_len, c):
    stdscr.clear()
    for i in range(inv_len):
        if i == c:
            inv_text = f"> {inv[i][0]}: {inv[i][1]}"
        else:
            inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(i, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, "j/k/up/down:scroll | i:exit")

def inventory(stdscr, inv):
    c = 0
    inv_len = len(inv)
    update_inv(stdscr, inv, inv_len, c)
    while True:
        key = stdscr.getch()

        # Navigate
        if key == ord('j') or key == curses.KEY_UP:
            c -= 1
            if c < 0: c = 0
        elif key == ord('k') or key == curses.KEY_DOWN:
            c += 1
            if c > inv_len-1: c = inv_len-1

        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            return inv[c][0], inv[c][1]
       
        # Exit inventory
        elif key == ord('i'):
            stdscr.clear()
            break

        update_inv(stdscr, inv, inv_len, c)

def add_to_inv(item, inv, add_=1):
    for i in range(len(inv)):
        if item in inv[i]:
            inv[i][1] += add_
            return inv
    inv.append([item, add_])
    return inv