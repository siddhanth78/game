import curses
import sys
import json
import math
import random
from inventory import add_to_inv, inventory
from settlement import (
    initialize_settlement_system, check_settler_interactions, update_all_settlers,
    serialize_settlement_data, deserialize_settlement_data, House, create_settler
)

def add_coins(coins):
    coins += random.randint(10, 30)
    return coins

def place_house(stdscr, eq, houses, settlers, grid_id, grid, grid_size, inv):
    flag = 0
    for i in range(2, grid_size[1]-2):
        for j in range(2, grid_size[0]-2):
            if grid[i][j] == " ":
                x,y = j,i
                flag = 1
                break
        if flag == 1:
            break
    prevx, prevy = -1,-1

    stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    grid[y][x] = 'X'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1, 0, "|")
        stdscr.addstr(i+1, grid_size[0]+1, "|")
        for j in range(grid_size[0]):
            stdscr.addstr(0, j+1, "-")
            stdscr.addstr(grid_size[1]+1, j+1, "-")
            stdscr.addstr(i+1, j+1, grid[i][j])
    stdscr.addstr(grid_size[1]+3, 0, f"Grid: {((int(grid_id)-1)%3)+1}, {math.floor((int(grid_id)-1)/3)+1}")
    stdscr.addstr(grid_size[1]+5, 0, "wasd/arrows:move | q:cancel | enter:place house")
    stdscr.refresh()

    while True:
        key = stdscr.getch()

        if key == ord('w') or key == curses.KEY_UP:
            if y > 1:
                prevx, prevy = x, y
                y -= 1
            elif y <= 1:
                y = 1
        elif key == ord('s') or key == curses.KEY_DOWN:
            if y < grid_size[1]-2:
                prevx, prevy = x, y
                y += 1
            elif y >= grid_size[1]-2:
                y = grid_size[1]-2
        elif key == ord('a') or key == curses.KEY_LEFT:
            if x > 1:
                prevx, prevy = x, y
                x -= 1
            elif x <= 1:
                x = 1
        elif key == ord('d') or key == curses.KEY_RIGHT:
            if x < grid_size[0]-2:
                prevx, prevy = x, y
                x += 1
            elif x >= grid_size[0]-2:
                x = grid_size[0]-2
        elif key == ord('q'):
            grid[y][x] = " "
            return houses, settlers, inv, grid
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            grid[y][x] = "H"
            
            # Create new house
            house = House(x, y, grid_id)
            if grid_id not in houses:
                houses[grid_id] = []
            houses[grid_id].append(house)
            settler_count = len(settlers)
            num_settlers = random.randint(1, 2)
            
            for _ in range(num_settlers):
                if len(settlers) < 30:
                    settler = create_settler(house, settler_count)
                    settlers[settler.settler_id] = settler
                    house.add_settler(settler.settler_id)
                    settler_count += 1
            inv[eq] -= 1
            if eq in inv and inv[eq] <= 0:
                del inv[eq]
            return houses, settlers, inv, grid
        
        if grid[y][x] == "o":
            x = prevx
            y = prevy
        elif grid[y][x] == "?":
            x = prevx
            y = prevy
        elif grid[y][x] == "T":
            x = prevx
            y = prevy
        elif grid[y][x] == "*":
            x = prevx
            y = prevy
        elif grid[y][x] == "m" or grid[y][x] == "M":
            x = prevx
            y = prevy
        elif grid[y][x] == "F":
            x = prevx
            y = prevy
        elif grid[y][x] == "0":
            x = prevx
            y = prevy
        elif grid[y][x] == "s":
            x = prevx
            y = prevy
        elif grid[y][x] == "V":
            x = prevx
            y = prevy
        elif grid[y][x] == "H":
            x = prevx
            y = prevy

        if prevx >= 0 and prevy >= 0:
            grid[prevy][prevx] = ' '
        grid[y][x] = 'X'
        for i in range(grid_size[1]):
            stdscr.addstr(i+1, 0, "|")
            stdscr.addstr(i+1, grid_size[0]+1, "|")
            for j in range(grid_size[0]):
                stdscr.addstr(0, j+1, "-")
                stdscr.addstr(grid_size[1]+1, j+1, "-")
                stdscr.addstr(i+1, j+1, grid[i][j])
        stdscr.addstr(grid_size[1]+3, 0, f"Grid: {((int(grid_id)-1)%3)+1}, {math.floor((int(grid_id)-1)/3)+1}")
        stdscr.addstr(grid_size[1]+5, 0, "wasd/arrows:move | q:cancel | enter:place house")
        stdscr.refresh()

def get_item():
    chance = random.random()
    item = None
    if 0 <= chance < 0.20:
        item = "Wood"
    elif 0.20 <= chance < 0.40:
        item = "Iron"
    elif 0.40 <= chance < 0.50:
        item = "Potion"
    elif 0.50 <= chance < 0.55:
        item = "Sword"
    elif 0.55 <= chance < 0.60:
        item = "Shield"
    elif 0.60 <= chance < 0.605:
        item = "Radon"
    elif 0.7 <= chance < 0.85:
        item = "Fuel"
    elif 0.89 <= chance < 0.9:
        item = "Super Seed"
    else:
        item = ""
    return item

def change_grid(deltax, deltay, x, y, prevx, prevy, grid_id, grid, gamefile):
    prevgridsize = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]

    new_grid_num = int(grid_id) + deltax + (deltay * 3)  # 3x3 grid layout

    # Boundary checks for 3x3 grid (1-9)
    if (int(grid_id) % 3 == 1 and deltax < 0) or (int(grid_id) % 3 == 0 and deltax > 0):
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile
    if (int(grid_id) in [1, 2, 3] and deltay < 0) or (int(grid_id) in [7, 8, 9] and deltay > 0):
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile
    
    # Check if new grid exists
    if new_grid_num < 1 or new_grid_num > 9:
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile

    new_grid_id = str(new_grid_num)
    new_grid = gamefile["grids"][new_grid_id]
    new_grid_size = [len(new_grid[0]), len(new_grid)]

    if deltax > 0:
        new_x = 0
        new_y = min(max(0, y), new_grid_size[1] - 1)
    elif deltax < 0:
        new_x = new_grid_size[0] - 1
        new_y = min(max(0, y), new_grid_size[1] - 1)
    elif deltay > 0:
        new_y = 0
        new_x = min(max(0, x), new_grid_size[0] - 1)
    elif deltay < 0:
        new_y = new_grid_size[1] - 1
        new_x = min(max(0, x), new_grid_size[0] - 1)

    grid[y][x] = ' '
    gamefile["grids"][grid_id] = grid
    
    # Switch to new grid
    grid_id = new_grid_id
    grid = new_grid
    grid_size = new_grid_size

    # Add scattered '?' symbols
    if random.random() <= 0.1:
        num_question_marks = random.randint(2, 5)
        for _ in range(num_question_marks):
            attempts = 0
            while attempts < 100:
                qx = random.randint(1, grid_size[0] - 2)
                qy = random.randint(1, grid_size[1] - 2)
                if grid[qy][qx] == ' ':
                    grid[qy][qx] = '?'
                    break
                attempts += 1
    
    # Add coin bunches
    if random.random() <= 0.1:
        total_o_target = random.randint(3, 6)
        placed_o = 0
        num_bunches = random.randint(2, 4)
        
        for bunch_num in range(num_bunches):
            if placed_o >= total_o_target:
                break
                
            remaining_o = total_o_target - placed_o
            remaining_bunches = num_bunches - bunch_num
            
            min_bunch = max(1, remaining_o // remaining_bunches - 3)
            max_bunch = min(15, remaining_o + 5)
            if min_bunch > max_bunch:
                min_bunch = max_bunch
            bunch_size = random.randint(min_bunch, max_bunch)
            
            if grid_size[0] <= 4 or grid_size[1] <= 4:
                continue
            center_x = random.randint(2, grid_size[0] - 3)
            center_y = random.randint(2, grid_size[1] - 3)
        
            for _ in range(bunch_size):
                if placed_o >= total_o_target:
                    break
                    
                attempts = 0
                while attempts < 50:
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 3)
                    ox = center_x + offset_x
                    oy = center_y + offset_y
                    
                    if 1 <= ox < grid_size[0] - 1 and 1 <= oy < grid_size[1] - 1:
                        if grid[oy][ox] == ' ':
                            grid[oy][ox] = 'o'
                            placed_o += 1
                            break
                    
                    attempts += 1 

    return new_x, new_y, -1, -1, grid_id, grid, grid_size, gamefile

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, atk, armor, health, houses={}, settlers={}, cleared=False, got_item=None, equipped="", combat_log=None):
    if cleared:
        stdscr.clear()

    if prevx >= 0 and prevy >= 0 and (prevx != x or prevy != y):
        if 0 <= prevy < len(grid) and 0 <= prevx < len(grid[0]):
            grid[prevy][prevx] = ' '

    display_grid = [row[:] for row in grid]

    if 0 <= y < len(display_grid) and 0 <= x < len(display_grid[0]):
        display_grid[y][x] = '0'

    # Add settlers to display
    for settler in settlers.values():
        if settler.grid_id == grid_id:
            if 0 <= settler.y < len(display_grid) and 0 <= settler.x < len(display_grid[0]):
                display_grid[settler.y][settler.x] = settler.get_symbol()

    # Add houses to display
    if grid_id in houses:
        for house in houses[grid_id]:
            if 0 <= house.y < len(display_grid) and 0 <= house.x < len(display_grid[0]):
                display_grid[house.y][house.x] = 'H'

    for i in range(grid_size[1]):
        stdscr.addstr(i+1, 0, "|")
        stdscr.addstr(i+1, grid_size[0]+1, "|")
        for j in range(grid_size[0]):
            stdscr.addstr(0, j+1, "-")
            stdscr.addstr(grid_size[1]+1, j+1, "-")
            stdscr.addstr(i+1, j+1, display_grid[i][j])
    
    stdscr.addstr(grid_size[1]+3, 0, f"Grid: {((int(grid_id)-1)%3)+1}, {math.floor((int(grid_id)-1)/3)+1}")
    stdscr.addstr(grid_size[1]+4, 0, f"Coins: {coins}")
    stdscr.addstr(grid_size[1]+5, 0, f"Equipped: {equipped}")
    stdscr.addstr(grid_size[1]+6, 0, f"Atk: {atk} | Health: {health} | Armor: {armor}")
    
    # Show settlement info
    settler_count = len([s for s in settlers.values() if s.grid_id == grid_id])
    house_count = len(houses.get(grid_id, []))
    stdscr.addstr(grid_size[1]+7, 0, f"Settlers: {settler_count} | Houses: {house_count}")

    stdscr.addstr(grid_size[1]+8, 0, "wasd/arrows:move | q:quit | i:inventory | enter:action | j/k:switch equipped")
    
    if got_item:
        stdscr.addstr(grid_size[1]+9, 0, f"{got_item} has been acquired!")
    
    if combat_log:
        for i, log_entry in enumerate(combat_log):
            if i < 3:
                stdscr.addstr(grid_size[1]+10+i, 0, log_entry[:80])
    
    stdscr.refresh()

class Player:
    def __init__(self, health):
        self.health = health

def start_settlements(stdscr, inv, essentials, health, coins, equipped):
    try:
        with open("settlements.json", "r") as file:
            gamefile = json.load(file)
    except FileNotFoundError:
        # Generate settlements if file doesn't exist
        import gen_settlements
        gen_settlements.generate_settlements()
        with open("settlements.json", "r") as file:
            gamefile = json.load(file)

    grid_id = gamefile["curr_grid"]
    grid_size = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]
    grid = gamefile["grids"][grid_id]

    # Initialize settlement system
    if "settlements" in gamefile and gamefile["settlements"]:
        houses, settlers = deserialize_settlement_data(gamefile["settlements"])
    else:
        houses, settlers = initialize_settlement_system(gamefile)

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    x, y = 0, 0
    prevx, prevy = -1, -1
    
    if equipped == "Sword":
        atk = 10
    elif equipped == "Big Sword":
        atk = 50
    elif equipped == "Epic Sword":
        atk = 200
    elif equipped == "Godly Sword":
        atk = 500
    elif equipped == "Axe":
        atk = 5
    else:
        atk = 1

    if "Godly Shield" in essentials:
        armor = 100
    elif "Epic Shield" in essentials:
        armor = 50
    elif "Big Shield" in essentials:
        armor = 20
    elif "Shield" in essentials:
        armor = 5
    else:
        armor = 0

    player = Player(health)
    combat_log = None
    
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, atk, armor, player.health, houses, settlers, equipped=equipped, cleared=True)
    item = None
    ec = 0

    while True:
        clear_grid = False
        key = stdscr.getch()
        
        # Movement
        moved = False
        if key == ord('w') or key == curses.KEY_UP:
            if y > 0:
                prevx, prevy = x, y
                y -= 1
                moved = True
            elif y <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, -1, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
                moved = True

        elif key == ord('s') or key == curses.KEY_DOWN:
            if y < grid_size[1]-1:
                prevx, prevy = x, y
                y += 1
                moved = True
            elif y >= grid_size[1]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, 1, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
                moved = True

        elif key == ord('a') or key == curses.KEY_LEFT:
            if x > 0:
                prevx, prevy = x, y
                x -= 1
                moved = True
            elif x <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, 0, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
                moved = True

        elif key == ord('d') or key == curses.KEY_RIGHT:
            if x < grid_size[0]-1:
                prevx, prevy = x, y
                x += 1
                moved = True
            elif x >= grid_size[0]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, 0, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
                moved = True

        # Check for settler interactions after movement
        if moved:
            settler_result = check_settler_interactions(settlers, grid_id, x, y)
            if settler_result.get("interaction", False):
                combat_log = settler_result.get("log", [])
                
                # Handle gifts
                if "gift" in settler_result:
                    gift = settler_result["gift"]
                    inv = add_to_inv(gift["item"], inv, gift["amount"])
                    combat_log.append(f"Received {gift['amount']} {gift['item']}!")
                
                # Handle vendor interaction
                if settler_result.get("open_vendor", False):
                    combat_log.append("Vendor interaction - coming soon!")
                
                clear_grid = True
            else:
                combat_log = None

        # Inventory Menu
        elif key == ord('i'):
            if inv != []:
                resp = inventory(stdscr, inv, essentials)
                if resp != None:
                    if type(resp) == list:
                        essentials = resp
                    else:
                        equipped, _ = resp
                clear_grid = True
        elif key == ord('j') and essentials != []:
            ec += 1
            if ec > len(essentials)-1: 
                ec = len(essentials)-1
            equipped = essentials[ec]
            clear_grid = True
        elif key == ord('k') and essentials != []:
            ec -= 1
            if ec < 0: 
                ec = 0
            equipped = essentials[ec]
            clear_grid = True

        # Exit
        elif key == ord('q'):
            grid[y][x] = ' '
            gamefile["grids"][grid_id] = grid
            gamefile["curr_grid"] = grid_id
            gamefile["settlements"] = serialize_settlement_data(houses, settlers)
            
            with open("settlements.json", "w") as f:
                json.dump(gamefile, f, indent=2)

            return inv, essentials, player.health, coins, equipped
       
        # Handle grid interactions
        if grid[y][x] == "o":
            coins = add_coins(coins)
            clear_grid = True
        elif grid[y][x] == "?":
            item = get_item()
            if item != "":
                if item in ["Wood", "Iron"]:
                    add_ = random.randint(2, 5)
                else:
                    add_ = 1
                inv = add_to_inv(item, inv, add_)
                clear_grid = True
            else:
                item = None
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            if equipped == "Pickaxe":
                Fuelprob = random.random()
                if 0.9 <= Fuelprob < 0.905:
                    item = "Fuel"
                    inv = add_to_inv("Fuel", inv, random.randint(3, 10))
                elif 0.5 <= Fuelprob < 0.501:
                    item = "Super Seed"
                    inv = add_to_inv("Super Seed", inv, random.randint(3, 10))
                else:
                    item = None
                    clear_grid = True
            elif equipped == "House":
                houses, settlers, inv, grid = place_house(stdscr, equipped, houses, settlers, grid_id, grid, grid_size, inv)
                essentials = [e for e in essentials if e in inv]
                if equipped not in inv:
                    equipped = ""
                clear_grid = True
            elif equipped == "Potion":
                if "Potion" in inv and inv["Potion"] > 0:
                    inv["Potion"] -= 1
                    player.health += 10
                    if player.health > 300:
                        player.health = 300
                    if inv["Potion"] <= 0:
                        del inv["Potion"]
                        equipped = ""
                    essentials = [e for e in essentials if e in inv]
                    clear_grid = True
        elif grid[y][x] == "T":
            if equipped == "Axe":
                inv = add_to_inv("Wood", inv, random.randint(2, 10))
                item = "Wood"
                grid[y][x] = " "
            x = prevx
            y = prevy
        elif grid[y][x] == "*":
            if equipped == "Pickaxe":
                inv = add_to_inv("Iron", inv, random.randint(2, 10))
                item = "Iron"
                grid[y][x] = " "
            x = prevx
            y = prevy
        elif grid[y][x] == "H":
            x = prevx
            y = prevy

        # Update equipment stats
        if equipped == "Sword":
            atk = 10
        elif equipped == "Big Sword":
            atk = 50
        elif equipped == "Epic Sword":
            atk = 200
        elif equipped == "Godly Sword":
            atk = 500
        elif equipped == "Axe":
            atk = 5
        else:
            atk = 1

        if "Godly Shield" in essentials:
            armor = 100
        elif "Epic Shield" in essentials:
            armor = 50
        elif "Big Shield" in essentials:
            armor = 20
        elif "Shield" in essentials:
            armor = 5
        else:
            armor = 0

        # Update settlers AI
        update_all_settlers(settlers, gamefile)

        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, atk, armor, player.health, houses, settlers, cleared=clear_grid, got_item=item, equipped=equipped, combat_log=combat_log)
        if item:
            item = None

if __name__ == "__main__":
    curses.wrapper(start_settlements)