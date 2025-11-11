import curses
from inventory import add_to_inv

all_merge = [
             "0. Sword: 20 Wood | 20 Iron | 50 coins",
             "1. Shield: 20 Wood | 20 Iron | 50 coins",
             "2. Big Sword: 100 Wood | 100 Iron | 2 Sword | 200 coins",
             "3. Big Shield: 100 Wood | 100 Iron | 2 Shield | 200 coins",
             "4. Epic Sword: 300 Wood | 300 Iron | 5 Sword | 1 Big Sword | 1 Radon | 500 coins",
             "5. Epic Shield: 300 Wood | 300 Iron | 5 Shield | 1 Big Shield | 1 Radon | 500 coins",
             "6. Godly Sword: 1000 Wood | 1000 Iron | 15 Big Sword | 3 Epic Sword | 5 Radon | 1500 coins",
             "7. Godly Shield: 1000 Wood | 1000 Iron | 15 Big Shield | 3 Epic Shield | 5 Radon | 1500 coins"]

all_build = [
    "0. Wood mill: 300 Wood | 100 Iron | 200 coins",
    "1. Iron mill: 300 Iron | 100 Wood | 200 coins",
    "2. Mill lot: 200 Wood | 200 Iron | 500 coins",
    "3. Big mill lot: 300 Wood | 300 Iron | 1000 coins"
]

def update(stdscr, inv, inv_len, coins):
    stdscr.clear()
    stdscr.addstr(0,0,"Available items:")
    for i in range(inv_len):
        inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(i+1, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, f"Coins: {coins}")
    stdscr.addstr(inv_len+3, 0, "a:armory | b:build | q:exit")

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

def check_purchase(selected_items, selected_items_quant, total_req, inv, reqcoins, coins):
    check_items = []
    if selected_items == []:
        return "No items", inv, coins
    if reqcoins > coins:
        return "Insufficient resources", inv, coins
    for k,v in total_req.items():
        if v != 0:
            check_items.append(k)
    for i in inv:
        if i[0] in total_req:
            if i[1] < total_req[i[0]]:
                return "Insufficient resources", inv, coins
    for k in check_items:
        for i in range(len(inv)):
            if k == inv[i][0]:
                inv[i][1] -= total_req[inv[i][0]]
                break
    inv = [i for i in inv if i[1]>0]
    for s, sq in zip(selected_items, selected_items_quant):
        s = s.strip()
        inv = add_to_inv(s, inv, sq)
    coins -= reqcoins
    return "Purchased!", inv, coins

def merge_items(stdscr, inv, coins, catalogue):
    selected_items = []
    selected_items_quant = []
    c = 0
    reqcoins = 0
    total_req = {
        "Wood": 0,
        "Iron": 0,
        "Potion": 0,
        "Radon": 0,
        "Sword": 0,
        "Shield": 0,
        "Axe": 0,
        "Big Sword": 0,
        "Big Shield": 0,
        "Epic Sword": 0,
        "Epic Shield": 0,
    }
    update_merge(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins, catalogue)
    while True:
        status = ""
        key = stdscr.getch()

        # Add/delete
        if key >= ord('0') and key <= ord('9'):
            if int(chr(key)) > len(catalogue)-1:
                continue
            sitem = catalogue[int(chr(key))].split(":")[0].split(".")[1]
            sreq = catalogue[int(chr(key))].split(":")[1].strip().split(" | ")
            if sitem not in selected_items:
                selected_items.append(sitem)
                selected_items_quant.append(1)
                for sr in sreq:
                    if "Wood" in sr:
                        total_req["Wood"] += int(sr.split(" ")[0])
                    elif "Iron" in sr:
                        total_req["Iron"] += int(sr.split(" ")[0])
                    elif "Potion" in sr:
                        total_req["Potion"] += int(sr.split(" ")[0])
                    elif "Radon" in sr:
                        total_req["Radon"] += int(sr.split(" ")[0])
                    elif "Big Sword" in sr:
                        total_req["Big Sword"] += int(sr.split(" ")[0])
                    elif "Big Shield" in sr:
                        total_req["Big Shield"] += int(sr.split(" ")[0])
                    elif "Epic Sword" in sr:
                        total_req["Epic Sword"] += int(sr.split(" ")[0])
                    elif "Epic Shield" in sr:
                        total_req["Epic Shield"] += int(sr.split(" ")[0])
                    elif "Sword" in sr:
                        total_req["Sword"] += int(sr.split(" ")[0])
                    elif "Shield" in sr:
                        total_req["Shield"] += int(sr.split(" ")[0])
                    elif "Axe" in sr:
                        total_req["Axe"] += int(sr.split(" ")[0])
                    elif "coins" in sr:
                        reqcoins += int(sr.split(" ")[0])

        elif key == ord('d') and selected_items != []:
            deleted = selected_items.pop(c)
            del_q = selected_items_quant.pop(c)
            for m in range(len(catalogue)):
                if deleted in catalogue[m]:
                    selreq = catalogue[m].split(":")[1].strip().split(" | ")
                    break
            for sr in selreq:
                if "Wood" in sr:
                    total_req["Wood"] -= int(sr.split(" ")[0])*del_q
                elif "Iron" in sr:
                    total_req["Iron"] -= int(sr.split(" ")[0])*del_q
                elif "Potion" in sr:
                    total_req["Potion"] -= int(sr.split(" ")[0])*del_q
                elif "Radon" in sr:
                    total_req["Radon"] -= int(sr.split(" ")[0])*del_q
                elif "Big Sword" in sr:
                    total_req["Big Sword"] -= int(sr.split(" ")[0])*del_q
                elif "Big Shield" in sr:
                    total_req["Big Shield"] -= int(sr.split(" ")[0])*del_q
                elif "Epic Sword" in sr:
                    total_req["Epic Sword"] -= int(sr.split(" ")[0])*del_q
                elif "Epic Shield" in sr:
                    total_req["Epic Shield"] -= int(sr.split(" ")[0])*del_q
                elif "Sword" in sr:
                    total_req["Sword"] -= int(sr.split(" ")[0])*del_q
                elif "Shield" in sr:
                    total_req["Shield"] -= int(sr.split(" ")[0])*del_q
                elif "Axe" in sr:
                    total_req["Axe"] -= int(sr.split(" ")[0])*del_q
                elif "coins" in sr:
                    reqcoins -= int(sr.split(" ")[0])*del_q
            if c >= len(selected_items):
                c = len(selected_items)-1
        
        # Navigate
        elif key == ord('j') or key == curses.KEY_UP:
            c -= 1
            if c < 0: c = 0
        elif key == ord('k') or key == curses.KEY_DOWN:
            c += 1
            if c > len(selected_items)-1: c = len(selected_items)-1

        # Regulate
        elif (key == ord('m') or key == curses.KEY_RIGHT) and selected_items != []:
            selected_items_quant[c] += 1
            for m in range(len(catalogue)):
                if selected_items[c] in catalogue[m]:
                    selreq = catalogue[m].split(":")[1].strip().split(" | ")
                    break
            for sr in selreq:
                if "Wood" in sr:
                    total_req["Wood"] += int(sr.split(" ")[0])
                elif "Iron" in sr:
                    total_req["Iron"] += int(sr.split(" ")[0])
                elif "Potion" in sr:
                    total_req["Potion"] += int(sr.split(" ")[0])
                elif "Radon" in sr:
                    total_req["Radon"] += int(sr.split(" ")[0])
                elif "Big Sword" in sr:
                    total_req["Big Sword"] += int(sr.split(" ")[0])
                elif "Big Shield" in sr:
                    total_req["Big Shield"] += int(sr.split(" ")[0])
                elif "Epic Sword" in sr:
                    total_req["Epic Sword"] += int(sr.split(" ")[0])
                elif "Epic Shield" in sr:
                    total_req["Epic Shield"] += int(sr.split(" ")[0])
                elif "Sword" in sr:
                    total_req["Sword"] += int(sr.split(" ")[0])
                elif "Shield" in sr:
                    total_req["Shield"] += int(sr.split(" ")[0])
                elif "Axe" in sr:
                    total_req["Axe"] += int(sr.split(" ")[0])
                elif "coins" in sr:
                    reqcoins += int(sr.split(" ")[0])
        elif (key == ord('n') or key == curses.KEY_LEFT) and selected_items != []:
            flag = 0
            selected_items_quant[c] -= 1
            if selected_items_quant[c] < 1:
                selected_items_quant[c] = 1
                flag = 1
            for m in range(len(catalogue)):
                if selected_items[c] in catalogue[m]:
                    selreq = catalogue[m].split(":")[1].strip().split(" | ")
                    break
            if flag == 0:
                for sr in selreq:
                    if "Wood" in sr:
                        total_req["Wood"] -= int(sr.split(" ")[0])
                    elif "Iron" in sr:
                        total_req["Iron"] -= int(sr.split(" ")[0])
                    elif "Potion" in sr:
                        total_req["Potion"] -= int(sr.split(" ")[0])
                    elif "Radon" in sr:
                        total_req["Radon"] -= int(sr.split(" ")[0])
                    elif "Big Sword" in sr:
                        total_req["Big Sword"] -= int(sr.split(" ")[0])
                    elif "Big Shield" in sr:
                        total_req["Big Shield"] -= int(sr.split(" ")[0])
                    elif "Epic Sword" in sr:
                        total_req["Epic Sword"] -= int(sr.split(" ")[0])
                    elif "Epic Shield" in sr:
                        total_req["Epic Shield"] -= int(sr.split(" ")[0])
                    elif "Sword" in sr:
                        total_req["Sword"] -= int(sr.split(" ")[0])
                    elif "Shield" in sr:
                        total_req["Shield"] -= int(sr.split(" ")[0])
                    elif "Axe" in sr:
                        total_req["Axe"] -= int(sr.split(" ")[0])
                    elif "coins" in sr:
                        reqcoins -= int(sr.split(" ")[0])
        
        # Select
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            status, inv, coins = check_purchase(selected_items, selected_items_quant, total_req, inv, reqcoins, coins)
            selected_items = []
            selected_items_quant = []
            c = 0
            total_req = {
                "Wood": 0,
                "Iron": 0,
                "Potion": 0,
                "Radon": 0,
                "Sword": 0,
                "Shield": 0,
                "Axe": 0,
                "Big Sword": 0,
                "Big Shield": 0,
                "Epic Sword": 0,
                "Epic Shield": 0,
            }
            reqcoins = 0

        # Exit
        elif key == ord('q'):
            return inv, coins
        
        update_merge(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins, catalogue, status)

def run_forge(stdscr, inv, coins):
    update(stdscr, inv, len(inv), coins)
    while True:
        key = stdscr.getch()

        if key == ord('q'):
            return inv, coins
        elif key == ord('b'):
            inv, coins = merge_items(stdscr, inv, coins, all_build)
        elif key == ord('a'):
            inv, coins = merge_items(stdscr, inv, coins, all_merge)

        update(stdscr, inv, len(inv), coins)


def start_forge(stdscr, inv, coins):
    stdscr.clear()
    stdscr.addstr(1,0,"Enter forge? (y/n)")
    key = stdscr.getch()
    if key == ord('y'):
        inv, coins = run_forge(stdscr, inv, coins)
    else:
        pass
    return inv, coins