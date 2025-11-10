def update_merge(stdscr, inv, coins, sel_len, selected_items, selected_items_quant, c, total_req, reqcoins, catalogue, status = ""):
    stdscr.clear()
    
    # First: Print catalogue
    for i in range(len(catalogue)):
        stdscr.addstr(i, 0, catalogue[i])

    gap1 = len(catalogue) + 1
    stdscr.addstr(gap1, 0, "Available items:")
    inv_len = len(inv)
    for i in range(inv_len):
        inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(gap1 + 1 + i, 0, inv_text)
    stdscr.addstr(gap1 + 1 + inv_len, 0, f"Coins: {coins}")

    gap2 = gap1 + 1 + inv_len + 2
    stdscr.addstr(gap2, 0, "Selected:")
    for i in range(sel_len):
        stext = f'{selected_items[i]}: {selected_items_quant[i]}'
        if i == c:
            sel_text = f"> {stext}"
        else:
            sel_text = f"{stext}"
        stdscr.addstr(gap2 + 1 + i, 0, sel_text)

    gap3 = gap2 + 1 + sel_len + 1
    reqtext = " | ".join(f"{k}: {v}" for k,v in total_req.items()) + f" | Coins: {reqcoins}"
    stdscr.addstr(gap3, 0, reqtext)
    stdscr.addstr(gap3 + 2, 0, "0-9:add item | d:delete item | m/n/right/left:increase/decrease | j/k/up/down:scroll | enter:purchase | q:exit")
    stdscr.addstr(gap3 + 3, 0, status)