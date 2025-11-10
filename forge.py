import curses
from inventory import inventory, add_to_inv
from collections import defaultdict

all_merge = ["0. Radon: 40 Wood | 40 Iron | 10 potion | 100 coins",
             "1. Sword: 5 Wood | 5 Iron | 10 coins",
             "2. Shield: 5 Wood | 5 Iron | 10 coins",
             "3. Axe: 5 Wood | 5 Iron | 10 coins",
             "4. Big Sword: 10 Wood | 10 Iron | 2 Sword | 20 coins",
             "5. Big Shield: 10 Wood | 10 Iron | 2 Shield | 20 coins",
             "6. Epic Sword: 30 Wood | 30 Iron | 5 Sword | 1 Big Sword | 1 Radon | 50 coins",
             "7. Epic Shield: 30 Wood | 30 Iron | 5 Shield | 1 Big Shield | 1 Radon | 50 coins",
             "8. Godly Sword: 100 Wood | 100 Iron | 15 Sword | 3 Epic Sword | 5 Radon | 150 coins",
             "9. Godly Shield: 100 Wood | 100 Iron | 15 Shield | 3 Epic Shield | 5 Radon | 150 coins"]

all_build = [
    "0. Wood mill: 30 Wood 10 Iron 20 coins",
    "1. Iron mill: 30 Iron 10 Wood 20 coins",
]

def update(stdscr, inv, inv_len, coins):
    stdscr.clear()
    stdscr.addstr(0,0,"Available items:")
    for i in range(inv_len):
        inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(i+1, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, f"Coins: {coins}")
    stdscr.addstr(inv_len+3, 0, "a:armory | b:build | q:exit")

def build_(stdscr, inv, inv_len, coins):
    return inv, coins

def update_merge(stdscr, inv, coins, sel_len, selected_items, selected_items_quant, c, total_req, reqcoins, status = ""):
    stdscr.clear()
    
    # First: Print all_merge
    for i in range(len(all_merge)):
        stdscr.addstr(i, 0, all_merge[i])

    gap1 = len(all_merge) + 1
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
    stdscr.addstr(gap3 + 1, 0, "0-9:add item | d:delete item | m/n/right/left:increase/decrease | j/k/up/down:scroll | enter:purchase | q:exit")
    stdscr.addstr(gap3 + 2, 0, status)

def check_purchase(selected_items, selected_items_quant, total_req, inv, reqcoins, coins):
    check_items = []
    if selected_items == []:
        return "No items"
    if reqcoins > coins:
        return "Insufficient resources"
    for k,v in total_req.items():
        if v != 0:
            check_items.append(k)
    for i in inv:
        if i[1] < total_req[i[0]]:
            return "Insufficient resources"
    for k in check_items:
        for i in range(len(inv)):
            if k in inv[i]:
                inv[i][1] -= total_req[inv[i][0]]
                break
    for s, sq in zip(selected_items, selected_items_quant):
        s = s.strip()
        inv = add_to_inv(s, inv, sq)
    coins -= reqcoins
    return "Purchased!", inv, coins

def merge_items(stdscr, inv, coins):
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
    update_merge(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins)
    while True:
        status = ""
        key = stdscr.getch()

        # Add/delete
        if key >= ord('0') and key <= ord('9'):
            sitem = all_merge[int(chr(key))].split(":")[0].split(".")[1]
            sreq = all_merge[int(chr(key))].split(":")[1].strip().split(" | ")
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
            for m in range(len(all_merge)):
                if deleted in all_merge[m]:
                    selreq = all_merge[m].split(":")[1].strip().split(" | ")
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
            for m in range(len(all_merge)):
                if selected_items[c] in all_merge[m]:
                    selreq = all_merge[m].split(":")[1].strip().split(" | ")
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
            for m in range(len(all_merge)):
                if selected_items[c] in all_merge[m]:
                    selreq = all_merge[m].split(":")[1].strip().split(" | ")
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
                        reqcoins += int(sr.split(" ")[0])
        
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
        
        update_merge(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins, status)

def run_forge(stdscr, inv, coins):
    update(stdscr, inv, len(inv), coins)
    while True:
        key = stdscr.getch()

        if key == ord('q'):
            return inv, coins
        elif key == ord('b'):
            inv, coins = build_(stdscr, inv, len(inv), coins)
        elif key == ord('a'):
            inv, coins = merge_items(stdscr, inv, coins)

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