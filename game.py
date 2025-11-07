import curses
import sys
import json
import math

def add_coins(coins):
    coins += 10
    return coins

def get_item():
    pass

def inventory(stdscr, inv):
    stdscr.clear()
    c = 0
    inv_len = len(inv)
    for i in range(inv_len):
        if i == c:
            inv_text = f"> {inv[i][0]}: {inv[i][1]}"
        else:
            inv_text = f"{inv[i][0]}: {inv[i][1]}"
        stdscr.addstr(i, 0, inv_text)
    stdscr.addstr(inv_len+1, 0, "j/k:scroll | i:exit")
    while True:
        key = stdscr.getch()

        # Navigate
        if key == ord('j'):
            c -= 1
            if c < 0: c = 0
        elif key == ord('k'):
            c += 1
            if c > inv_len-1: c = inv_len-1
       
        # Exit inventory
        elif key == ord('i'):
            stdscr.clear()
            break
        
        stdscr.clear()
        for i in range(inv_len):
            if i == c:
                inv_text = f"> {inv[i][0]}: {inv[i][1]}"
            else:
                inv_text = f"{inv[i][0]}: {inv[i][1]}"
            stdscr.addstr(i, 0, inv_text)
        stdscr.addstr(inv_len+1, 0, "j/k:scroll | i:exit")

def add_to_inv(stdscr, item, inv):
    inv.append(item)
    return inv

def change_grid(deltax, deltay, x, y, prevx, prevy, grid_id, grid, gamefile):
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

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, cleared=False):
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
    stdscr.addstr(grid_size[1]+5,0,"wasd:move | q:quit | i:inventory")
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
    prevx, prevy = -1,-1
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins)

    while True:
        clear_grid = False
        key = stdscr.getch()
        
        # Movement
        if key == ord('w'):
            if y > 0:
                prevx, prevy = x, y
                y -= 1
            elif y <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, -1, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
        elif key == ord('s'):
            if y < grid_size[1]-1:
                prevx, prevy = x, y
                y += 1
            elif y >= grid_size[1]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, 1, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
        elif key == ord('a'):
            if x > 0:
                prevx, prevy =x, y
                x -= 1
            elif x <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, 0, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True
        elif key == ord('d'):
            if x < grid_size[0]-1:
                prevx, prevy = x, y
                x += 1
            elif x >= grid_size[0]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, 0, x, y, prevx, prevy, grid_id, grid, gamefile)
                clear_grid = True

        # Inventory Menu
        elif key == ord('i'):
            inventory(stdscr, inv)

        # Exit
        elif key == ord('q'):
            gamefile["grids"][grid_id] = grid
            gamefile["curr_grid"] = grid_id
            gamefile["player"] = [x,y]
            gamefile["inventory"] = inv
            gamefile["coins"] = coins
            with open("grids.json", "w") as f:
                json.dump(gamefile, f)
            sys.exit(0)
       
        if grid[y][x] == "o":
            coins = add_coins(coins)
            clear_grid = True
        elif grid[y][x] == "?":
            item = get_item()
            inv = add_to_inv(stdscr, item, inv)
        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, cleared=clear_grid)

curses.wrapper(main)
