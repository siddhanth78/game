import curses

def update_inv(stdscr, inv, inv_len, sel, essentials):
    stdscr.clear()
    j = 0
    for i in inv:
        if i in essentials:
            itext = f"{i}: {inv[i]} - E"
        else:
            itext = f"{i}: {inv[i]}"
        if i == sel:
            inv_text = f"> {itext}"
        else:
            inv_text = f"{itext}"
        stdscr.addstr(j, 0, inv_text)
        j += 1
    stdscr.addstr(inv_len+1, 0, "j/k/up/down:scroll | i:exit")

def inventory(stdscr, inv, essentials):
    c = 0
    inv_len = len(inv)
    inv_items = list(inv.keys())
    update_inv(stdscr, inv, inv_len, inv_items[c], essentials)
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
            add_to_essentials(essentials, inv_items, c)

        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            return inv_items[c], inv[inv_items[c]]
       
        # Exit inventory
        elif key == ord('i'):
            stdscr.clear()
            return essentials

        update_inv(stdscr, inv, inv_len, inv_items[c], essentials)

def add_to_inv(item, inv, add_=1):
    if item in inv:
        inv[item] += add_
    else:
        inv[item] = add_
    return inv

def add_to_essentials(essentials, inv_items, c):
    if len(essentials) == 3:
        essentials.pop(0)
    essentials.append(inv_items[c])
    return essentials