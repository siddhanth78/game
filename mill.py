import curses
import math
from inventory import add_to_inv

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, cleared=False):
    if cleared == True:
        stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    grid[y][x] = 'X'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1,0,"|")
        stdscr.addstr(i+1,grid_size[0]+1,"|")
        for j in range(grid_size[0]):
            stdscr.addstr(0,j+1,"-")
            stdscr.addstr(grid_size[1]+1,j+1,"-")
            stdscr.addstr(i+1,j+1,grid[i][j])
    stdscr.addstr(grid_size[1]+3,0,f"Grid: {((int(grid_id)-1)%5)+1}, {math.floor((int(grid_id)-1)/5)+1}")
    stdscr.addstr(grid_size[1]+5,0,"wasd/arrows:move | q:quit | enter:place")
    stdscr.refresh()

def update_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills, cleared=False, status = ""):
    if cleared == True:
        stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    for a in all_mills:
        if a[0] == "Wood mill":
            grid[a[2]][a[1]] = "W"
        elif a[0] == "Iron mill":
            grid[a[2]][a[1]] = "I"
    grid[y][x] = '0'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1,0,"|")
        stdscr.addstr(i+1,grid_size[0]+1,"|")
        for j in range(grid_size[0]):
            stdscr.addstr(0,j+1,"-")
            stdscr.addstr(grid_size[1]+1,j+1,"-")
            stdscr.addstr(i+1,j+1,grid[i][j])
    stdscr.addstr(grid_size[1]+3,0,"wasd/arrows:move | q:quit | enter:place | j:fuel | k:super-seed")
    if status != "":
        stdscr.addstr(grid_size[1]+4,0,status)
    stdscr.refresh()

def update_place_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills, cleared=False):
    if cleared == True:
        stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    for a in all_mills:
        if a[0] == "Wood mill":
            grid[a[2]][a[1]] = "W"
        elif a[0] == "Iron mill":
            grid[a[2]][a[1]] = "I"
    grid[y][x] = 'X'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1,0,"|")
        stdscr.addstr(i+1,grid_size[0]+1,"|")
        for j in range(grid_size[0]):
            stdscr.addstr(0,j+1,"-")
            stdscr.addstr(grid_size[1]+1,j+1,"-")
            stdscr.addstr(i+1,j+1,grid[i][j])
    stdscr.addstr(grid_size[1]+3,0,"a/d/left/right:move | q:quit | n:place wood mill | m:place iron mill")
    stdscr.refresh()

def run_mill(stdscr, inv, coins, curr_mill):
    grid_size = curr_mill["size"]
    all_mills = curr_mill["all_mills"]
    x,y = 0,0
    prevx, prevy = -1,-1
    grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]
    status = ""
    update_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills, True)
    while True:
        clear_grid = False
        key = stdscr.getch()
        if key == ord('w') or key == curses.KEY_UP:
            if y > 0:
                prevx, prevy = x, y
                y -= 1
        elif key == ord('s') or key == curses.KEY_DOWN:
            if y < grid_size[1]-1:
                prevx, prevy = x, y
                y += 1
        elif key == ord('a') or key == curses.KEY_LEFT:
            if x > 0:
                prevx, prevy = x, y
                x -= 1
        elif key == ord('d') or key == curses.KEY_RIGHT:
            if x < grid_size[0]-1:
                prevx, prevy = x, y
                x += 1
        elif key == ord('j'):
            fuel_req = len(all_mills)*5
            wm = 0
            im = 0
            check = 0
            if all_mills == []:
                status = "No mills found"
            else:
                if "Fuel" in inv:
                    if inv["Fuel"] >= fuel_req:
                        inv["Fuel"] -= fuel_req
                        status = "Fueled! Wood/Iron has been acquired!"
                        check = 1
            if check == 1:
                for a in all_mills:
                    if a[0] == "Wood mill":
                        wm += 1
                    elif a[0] == "Iron mill":
                        im += 1
                inv = add_to_inv("Wood", inv, wm*10)
                inv = add_to_inv("Iron", inv, im*10)
            else:
                status = "Insufficient resources"
            clear_grid = True
        elif key == ord('k'):
            ss_req = math.ceil(len(all_mills)/2)
            wm = 0
            im = 0
            check = 0
            if all_mills == []:
                status = "No mills found"
            else:
                if "Super Seed" in inv:
                    if inv["Super Seed"] >= ss_req:
                        inv["Super Seed"] -= ss_req
                        status = "SUPER-SEEDED! Wood/Iron has been acquired!"
                        check = 1
            if check == 1:
                for a in all_mills:
                    if a[0] == "Wood mill":
                        wm += 1
                    elif a[0] == "Iron mill":
                        im += 1
                inv = add_to_inv("Wood", inv, wm*100)
                inv = add_to_inv("Iron", inv, im*100)
            else:
                status = "Insufficient resources"
            clear_grid = True
        elif key == ord('q'):
            return inv, coins, curr_mill
        
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            grid[y][x] = ' '
            x,y = 0,0
            prevx, prevy = -1,-1
            grid[y][x] = '0'
            all_mills, inv, grid =  place_mill_in_lot(stdscr, grid, grid_size, inv, all_mills)
            clear_grid = True

        if grid[y][x] == "W":
            x = prevx
            y = prevy
        elif grid[y][x] == "I":
            x = prevx
            y = prevy
        

        update_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills, cleared=clear_grid, status=status)
        status = ""

def start_mill(stdscr, inv, coins, curr_mill):
    stdscr.clear()
    stdscr.addstr(1,0,"Enter mill lot? (y/n)")
    key = stdscr.getch()
    if key == ord('y'):
        inv, coins, curr_mill = run_mill(stdscr, inv, coins, curr_mill)
    else:
        pass
    return inv, coins, curr_mill

def find_empty(grid, grid_size):
    empty = []
    for i in range(1, grid_size[1]-1):
        for j in range(1, grid_size[0]-1):
            if grid[i][j] not in ["W", "I", "0"]:
                x,y = j,i
                empty.append([x,y])
    return empty

def find_next_empty(empty, ect):
    ect += 1
    if ect > len(empty)-1:
        ect = 0
    return empty[ect][0], empty[ect][1], ect

def find_prev_empty(empty, ect):
    ect -= 1
    if ect < 0:
        ect = len(empty)-1
    return empty[ect][0], empty[ect][1], ect

def rem_empty(empty, x, y):
    return [e for e in empty if e != [x,y]]

def place_mill_in_lot(stdscr, grid, grid_size, inv, all_mills):
    empty = find_empty(grid, grid_size)
    if empty == []:
        return all_mills, inv, grid
    x,y, ect = find_next_empty(empty, -1)
    prevx, prevy = -1,-1
    update_place_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills)
    while True:
        key = stdscr.getch()

        if key == ord('a') or key == curses.KEY_LEFT:
            prevx, prevy = x,y
            x,y, ect = find_prev_empty(empty, ect)
        elif key == ord('d') or key == curses.KEY_RIGHT:
            prevx, prevy = x,y
            x,y, ect = find_next_empty(empty, ect)
        elif key == ord('q'):
            grid[y][x] = " "
            return all_mills, inv, grid
        elif key == ord('n'):
            ch = 0
            if "Wood mill" in inv:
                inv["Wood mill"] -= 1
                grid[y][x] = "W"
                all_mills.append(["Wood mill", x, y])
                ch = 1
            if ch == 1:
                if "Wood mill" in inv and inv["Wood mill"] <= 0:
                    del inv["Wood mill"]
                finalx, finaly = x,y
                empty = rem_empty(empty, x, y)
                if empty == []:
                    grid[finaly][finalx] = " "
                    return all_mills, inv, grid
                else:
                    x,y,ect = find_next_empty(empty, ect)
                prevx, prevy = -1,-1
        elif key == ord('m'):
            ch = 0
            if "Iron mill" in inv:
                inv["Iron mill"] -= 1
                grid[y][x] = "W"
                all_mills.append(["Iron mill", x, y])
                ch = 1
            if ch == 1:
                if "Iron mill" in inv and inv["Iron mill"] <= 0:
                    del inv["Iron mill"]
                finalx, finaly = x,y
                empty = rem_empty(empty, x, y)
                if empty == []:
                    grid[finaly][finalx] = " "
                    return all_mills, inv, grid
                else:
                    x,y,ect = find_next_empty(empty, ect)
                prevx, prevy = -1,-1
        
        if grid[y][x] == "W":
            x = prevx
            y = prevy
        elif grid[y][x] == "I":
            x = prevx
            y = prevy
        elif grid[y][x] == "0":
            x = prevx
            y = prevy

        update_place_mill_screen(stdscr, x, y, prevx, prevy, grid, grid_size, all_mills)

def place_mill(stdscr, eq, mills, grid_id, grid, grid_size, inv):
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
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, cleared=True)
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
            return mills, inv, grid
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            if eq == "Fuel Dispenser":
                grid[y][x] = "D"
            else:
                mill_size = [5,5] if eq == "Mill lot" else [10,10]
                mills[f"mill_{grid_id}_{x}_{y}"] = {"type": eq, "size": mill_size, "all_mills": []}
                grid[y][x] = 'm' if eq == "Mill lot" else "M"
            inv[eq] -= 1
            if eq in inv and inv[eq] <= 0:
                del inv[eq]
            return mills, inv, grid
        
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
        elif grid[y][x] == ">":
            x = prevx
            y = prevy
        elif grid[y][x] == "<":
            x = prevx
            y = prevy

        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id)