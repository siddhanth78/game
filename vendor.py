import curses
from inventory import add_to_inv
import math

depths_goods = [
    "0. Radon: 1000 coins",
    "1. Potion: 200 coins",
    "2. Super Seed: 5 Radon"
]

settlements_goods = [
    "0. House: 500 Wood | 500 Iron | 50 Spark",
    "1. Garden: 10 Potion | 20 Spark | 5 Super Seed",
    "2. Ore Shaft: 10 Potion | 20 Spark | 5 Super Seed"
]

def update_vendor(stdscr, inv, coins, sel_len, selected_items, selected_items_quant, c, total_req, reqcoins, catalogue, status = ""):
    stdscr.clear()

    for i in range(len(catalogue)):
        stdscr.addstr(i, 0, catalogue[i])

    gap1 = len(catalogue) + 1
    stdscr.addstr(gap1, 0, "Available items:")
    inv_len = len(inv)
    j = 0
    for i in inv:
        inv_text = f"{i}: {inv[i]}"
        stdscr.addstr(j+1+gap1, 0, inv_text)
        j += 1
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
        if i in total_req:
            if inv[i] < total_req[i]:
                return "Insufficient resources", inv, coins
    for k in check_items:
        inv[k] -= total_req[k]
        if inv[k] <= 0:
            del inv[k]
    for s, sq in zip(selected_items, selected_items_quant):
        s = s.strip()
        inv = add_to_inv(s, inv, sq)
    coins -= reqcoins
    return "Purchased!", inv, coins

def vendor_shop(stdscr, inv, coins, loc):
    selected_items = []
    selected_items_quant = []
    c = 0
    reqcoins = 0
    total_req = {
        "Potion": 0,
        "Radon": 0,
        "Wood": 0,
        "Iron": 0,
        "Spark": 0,
        "Super Seed": 0
    }
    if loc == "depths":
        all_goods = depths_goods
    elif loc == "settlements":
        all_goods = settlements_goods

    update_vendor(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins, all_goods)
    while True:
        status = ""
        key = stdscr.getch()

        # Add/delete
        if key >= ord('0') and key <= ord('9'):
            if int(chr(key)) > len(all_goods)-1:
                continue
            sitem = all_goods[int(chr(key))].split(":")[0].split(".")[1]
            sreq = all_goods[int(chr(key))].split(":")[1].strip().split(" | ")
            if sitem not in selected_items:
                selected_items.append(sitem)
                selected_items_quant.append(1)
                for sr in sreq:
                    if "Potion" in sr:
                        total_req["Potion"] += int(sr.split(" ")[0])
                    elif "Radon" in sr:
                        total_req["Radon"] += int(sr.split(" ")[0])
                    elif "Wood" in sr:
                        total_req["Wood"] += int(sr.split(" ")[0])
                    elif "Iron" in sr:
                        total_req["Iron"] += int(sr.split(" ")[0])
                    elif "Spark" in sr:
                        total_req["Spark"] += int(sr.split(" ")[0])
                    elif "Super Seed" in sr:
                        total_req["Super Seed"] += int(sr.split(" ")[0])
                    elif "coins" in sr:
                        reqcoins += int(sr.split(" ")[0])

        elif key == ord('d') and selected_items != []:
            deleted = selected_items.pop(c)
            del_q = selected_items_quant.pop(c)
            for m in range(len(all_goods)):
                if deleted in all_goods[m]:
                    selreq = all_goods[m].split(":")[1].strip().split(" | ")
                    break
            for sr in selreq:
                if "Potion" in sr:
                    total_req["Potion"] -= int(sr.split(" ")[0])*del_q
                elif "Radon" in sr:
                    total_req["Radon"] -= int(sr.split(" ")[0])*del_q
                elif "Wood" in sr:
                    total_req["Wood"] -= int(sr.split(" ")[0])*del_q
                elif "Iron" in sr:
                    total_req["Iron"] -= int(sr.split(" ")[0])*del_q
                elif "Spark" in sr:
                    total_req["Spark"] -= int(sr.split(" ")[0])*del_q
                elif "Super Seed" in sr:
                    total_req["Super Seed"] -= int(sr.split(" ")[0])*del_q
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
            for m in range(len(all_goods)):
                if selected_items[c] in all_goods[m]:
                    selreq = all_goods[m].split(":")[1].strip().split(" | ")
                    break
            for sr in selreq:
                if "Potion" in sr:
                    total_req["Potion"] += int(sr.split(" ")[0])
                elif "Radon" in sr:
                    total_req["Radon"] += int(sr.split(" ")[0])
                elif "Wood" in sr:
                    total_req["Wood"] += int(sr.split(" ")[0])
                elif "Iron" in sr:
                    total_req["Iron"] += int(sr.split(" ")[0])
                elif "Spark" in sr:
                    total_req["Spark"] += int(sr.split(" ")[0])
                elif "Super Seed" in sr:
                    total_req["Super Seed"] += int(sr.split(" ")[0])
                elif "coins" in sr:
                    reqcoins += int(sr.split(" ")[0])
        elif (key == ord('n') or key == curses.KEY_LEFT) and selected_items != []:
            flag = 0
            selected_items_quant[c] -= 1
            if selected_items_quant[c] < 1:
                selected_items_quant[c] = 1
                flag = 1
            for m in range(len(all_goods)):
                if selected_items[c] in all_goods[m]:
                    selreq = all_goods[m].split(":")[1].strip().split(" | ")
                    break
            if flag == 0:
                for sr in selreq:
                    if "Potion" in sr:
                        total_req["Potion"] -= int(sr.split(" ")[0])
                    elif "Radon" in sr:
                        total_req["Radon"] -= int(sr.split(" ")[0])
                    elif "Wood" in sr:
                        total_req["Wood"] -= int(sr.split(" ")[0])
                    elif "Iron" in sr:
                        total_req["Iron"] -= int(sr.split(" ")[0])
                    elif "Spark" in sr:
                        total_req["Spark"] -= int(sr.split(" ")[0])
                    elif "Super Seed" in sr:
                        total_req["Super Seed"] -= int(sr.split(" ")[0])
                    elif "coins" in sr:
                        reqcoins -= int(sr.split(" ")[0])
        
        # Select
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            status, inv, coins = check_purchase(selected_items, selected_items_quant, total_req, inv, reqcoins, coins)
            selected_items = []
            selected_items_quant = []
            c = 0
            total_req = {
                "Potion": 0,
                "Radon": 0,
                "Wood": 0,
                "Iron": 0,
                "Spark": 0,
                "Super Seed": 0
            }
            reqcoins = 0

        # Exit
        elif key == ord('q'):
            return inv, coins
        
        update_vendor(stdscr, inv, coins, len(selected_items), selected_items, selected_items_quant, c, total_req, reqcoins, all_goods, status)

def start_vendor(stdscr, inv, coins, loc="depths"):
    inv, coins = vendor_shop(stdscr, inv, coins, loc)
    return inv, coins