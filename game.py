import curses
import sys
import json
import math
import random
from inventory import add_to_inv, inventory
from forge import start_forge


def add_coins(coins):
    coins += 10
    return coins

def generate_item():
    chance = random.random()
    item = None
    if 0 <= chance <= 0.15:
        item = "Potion"
    elif 0.15 < chance <= 0.555:
        item = "Wood"
    elif 0.555 < chance <= 0.995:
        item = "Iron"
    elif 0.995 < chance <= 1:
        item = "Radon"

    return item

def get_item():
    item = generate_item()
    return item

def change_grid(deltax, deltay, x, y, prevx, prevy, grid_id, grid, gamefile, forge):
    prevgridsize = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]

    if (int(grid_id)%5 == 1 and deltax < 0) or (int(grid_id)%5 == 0 and deltax > 0):
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile
    if (int(grid_id) in [1,2,3,4,5] and deltay < 0) or (int(grid_id) in [16,17,18,19,20] and deltay > 0):
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile
 
    grid[y][x] = ' '
    gamefile["grids"][grid_id] = grid
    grid_id = str(int(grid_id)+deltax+(deltay*5))
    grid = gamefile["grids"][grid_id]
    grid_size = [len(grid[0]), len(grid)]

    if forge["loc"] == grid_id and forge["state"] == "Undiscovered":
        forge["gridx"] = ((int(grid_id)-1)%5)+1
        forge["gridy"] = math.floor((int(grid_id)-1)/5)+1
        forge["state"] = "Discovered"

    # Add scattered '?' symbols (around 5)
    if random.random() <= 0.1:
        num_question_marks = random.randint(2, 5)  # Around 5 ? symbols
        for _ in range(num_question_marks):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = '?'
                    break
                attempts += 1
    
    if random.random() <= 0.1:
        # Add bunches of 'o' (around 6 total)
        total_o_target = random.randint(3, 6)  # Around 6 o symbols
        placed_o = 0

        # Create 2-4 bunches to reach the target
        num_bunches = random.randint(2, 4)
        for bunch_num in range(num_bunches):
            if placed_o >= total_o_target:
                break
                
            # Simple bunch size calculation
            remaining_o = total_o_target - placed_o
            remaining_bunches = num_bunches - bunch_num
            
            # Ensure we have a reasonable bunch size
            min_bunch = max(1, remaining_o // remaining_bunches - 3)
            max_bunch = min(15, remaining_o + 5)
            bunch_size = random.randint(min_bunch, max_bunch)
            
            # Choose center position (avoiding borders)
            center_x = random.randint(2, grid_size[0] - 3)
            center_y = random.randint(2, grid_size[1] - 3)
        
            # Create clustered bunch around center
            for _ in range(bunch_size):
                if placed_o >= total_o_target:
                    break
                    
                attempts = 0
                while attempts < 50:  # Prevent infinite loops
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 3)
                    x = center_x + offset_x
                    y = center_y + offset_y
                    
                    # Ensure within safe bounds (not on borders)
                    if 1 <= x < grid_size[0] - 1 and 1 <= y < grid_size[1] - 1:
                        if grid[y][x] == ' ':  # Only place if cell is empty
                            grid[y][x] = 'o'
                            placed_o += 1
                            break
                    
                    attempts += 1 

    prevx, prevy = x, y

    if deltax > 0:
        x = 0
    elif deltax < 0:
        x = grid_size[0]-1
    elif deltay > 0:
        y = 0
    elif deltay < 0:
        y = grid_size[1]-1
    
    if prevx > grid_size[0]-1 and deltay != 0:
        x = grid_size[0]-1
    if prevy > grid_size[1]-1 and deltax != 0:
        y = grid_size[1]-1
    prevx, prevy = -1, -1
    return x, y, prevx, prevy, grid_id, grid, grid_size, gamefile

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, cleared=False, got_item=None):
    if cleared == True:
        stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    grid[y][x] = '0'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1,0,"|")
        stdscr.addstr(i+1,grid_size[0]+1,"|")
        for j in range(grid_size[0]):
            stdscr.addstr(0,j+1,"-")
            stdscr.addstr(grid_size[1]+1,j+1,"-")
            stdscr.addstr(i+1,j+1,grid[i][j])
    stdscr.addstr(grid_size[1]+3,0,f"Grid: {((int(grid_id)-1)%5)+1}, {math.floor((int(grid_id)-1)/5)+1}")
    stdscr.addstr(grid_size[1]+4,0,f"Coins: {coins}")
    stdscr.addstr(grid_size[1]+7,0,"wasd/arrows:move | q:quit | i:inventory")
    if forge["state"] == "Discovered":
        stdscr.addstr(grid_size[1]+5,0, f'Forge: {forge["gridx"]}, {forge["gridy"]}')
    if got_item:
        stdscr.addstr(grid_size[1]+8,0,f"{got_item} has been acquired!")
    stdscr.refresh()

def main(stdscr):

    with open("grids.json", "r") as file:
        gamefile = json.load(file)

    grid_id = gamefile["curr_grid"]
    grid_size = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]
    grid = gamefile["grids"][grid_id]
    inv = gamefile["inventory"]

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    x,y = gamefile["player"]
    coins = gamefile["coins"]
    forge = gamefile["forge"]
    prevx, prevy = -1,-1
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge)
    item = None

    while True:
        clear_grid = False
        key = stdscr.getch()
        
        # Movement
        if key == ord('w') or key == curses.KEY_UP:
            if y > 0:
                prevx, prevy = x, y
                y -= 1
            elif y <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, -1, x, y, prevx, prevy, grid_id, grid, gamefile, forge)
                clear_grid = True
        elif key == ord('s') or key == curses.KEY_DOWN:
            if y < grid_size[1]-1:
                prevx, prevy = x, y
                y += 1
            elif y >= grid_size[1]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, 1, x, y, prevx, prevy, grid_id, grid, gamefile, forge)
                clear_grid = True
        elif key == ord('a') or key == curses.KEY_LEFT:
            if x > 0:
                prevx, prevy =x, y
                x -= 1
            elif x <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge)
                clear_grid = True
        elif key == ord('d') or key == curses.KEY_RIGHT:
            if x < grid_size[0]-1:
                prevx, prevy = x, y
                x += 1
            elif x >= grid_size[0]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge)
                clear_grid = True

        # Inventory Menu
        elif key == ord('i'):
            inventory(stdscr, inv)
            clear_grid = True

        # Exit
        elif key == ord('q'):
            gamefile["grids"][grid_id] = grid
            gamefile["curr_grid"] = grid_id
            gamefile["player"] = [x,y]
            gamefile["inventory"] = inv
            gamefile["coins"] = coins
            gamefile["forge"] = forge
            with open("grids.json", "w") as f:
                json.dump(gamefile, f)
            sys.exit(0)
       
        if grid[y][x] == "o":
            coins = add_coins(coins)
            clear_grid = True
        elif grid[y][x] == "?":
            item = get_item()
            inv = add_to_inv(item, inv)
            clear_grid = True
        elif grid[y][x] == "F":
            x = prevx
            y = prevy
            inv, coins = start_forge(stdscr, inv, coins)
            clear_grid = True
        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, cleared=clear_grid, got_item=item)
        if item:
            item = None

curses.wrapper(main)
