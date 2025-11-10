import curses

def update_inv(stdscr, inv, inv_len, c, essentials):
    stdscr.clear()
    for i in range(inv_len):
        if inv[i][0] in essentials:
            itext = f"{inv[i][0]}: {inv[i][1]} - E"
        else:
            itext = f"{inv[i][0]}: {inv[i][1]}"
        if i == c:
            inv_text = f"> {itext}"
        else:
            inv_text = f"{itext}"
        stdscr.addstr(i, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, "j/k/up/down:scroll | i:exit")

def inventory(stdscr, inv, essentials):
    c = 0
    inv_len = len(inv)
    update_inv(stdscr, inv, inv_len, c, essentials)
    while True:
        key = stdscr.getch()

        # Navigate
        if key == ord('j') or key == curses.KEY_UP:
            c -= 1
            if c < 0: c = 0
        elif key == ord('k') or key == curses.KEY_DOWN:
            c += 1
            if c > inv_len-1: c = inv_len-1

        elif key == ord('e'):
            if len(essentials) < 3:
                add_to_essentials(essentials, inv, c)

        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            return inv[c][0], inv[c][1]
       
        # Exit inventory
        elif key == ord('i'):
            stdscr.clear()
            return essentials

        update_inv(stdscr, inv, inv_len, c, essentials)

def add_to_inv(item, inv, add_=1):
    for i in range(len(inv)):
        if item in inv[i]:
            inv[i][1] += add_
            return inv
    inv.append([item, add_])
    return inv

def add_to_essentials(essentials, inv, c):
    if len(essentials) == 3:
        essentials.pop(0)
    essentials.append(inv[c][0])
    return essentials