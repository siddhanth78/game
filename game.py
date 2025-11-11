import curses
import sys
import json
import math
import random
from inventory import add_to_inv, inventory
from forge import start_forge
from mill import start_mill, place_mill
from enemy import Enemy, check_enemy_collisions, spawn_enemy_in_grid, check_adjacent_enemy_attack

def add_coins(coins):
    coins += random.randint(10, 30)
    return coins

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

def handle_enemy_death(inv, enemy_level):
    """Handle enemy death drops - 10% Super Seed, 1% Radon"""
    drops = []
    
    # 10% chance for Super Seed
    if random.random() < 0.10:
        inv = add_to_inv("Super Seed", inv, 1)
        drops.append("Super Seed")
    
    # 1% chance for Radon
    if random.random() < 0.01:
        inv = add_to_inv("Radon", inv, 1)
        drops.append("Radon")
    
    return inv, drops

def is_position_blocked(x, y, enemies):
    """Check if position is blocked by an enemy"""
    for enemy in enemies:
        if enemy.status != "Dead" and enemy.x == x and enemy.y == y:
            return True
    return False

def spawn_enemies_in_grid(grid, enemy_level, existing_enemies, max_enemies=4):
    """Spawn enemies in valid positions when entering new grid"""
    spawned_enemies = []
    
    # Only spawn if there are no existing enemies
    if len(existing_enemies) > 0:
        return spawned_enemies

    if random.random() < 0.60:
        rows, cols = len(grid), len(grid[0])
        num_enemies = random.randint(1, max_enemies)
        
        for _ in range(num_enemies):
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                x = random.randint(1, cols - 2)
                y = random.randint(1, rows - 2)
                
                # Can spawn on empty space, coins, or question marks
                if grid[y][x] in [' ', 'o', '?']:
                    enemy = Enemy(x, y, enemy_level)
                    spawned_enemies.append(enemy)
                    break
                
                attempts += 1
    
    return spawned_enemies

def handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile):
    """Handle player death - lose coins, respawn at 0,0 grid 1"""
    death_penalty = 200
    
    if coins >= death_penalty:
        coins -= death_penalty
        death_message = f"You died! Lost {death_penalty} coins."
    else:
        death_message = "You died! Free respawn (insufficient coins)."
        coins = 0
    
    # Reset player health
    player.health = 300
    
    # Clear current position on grid
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = ' '
    
    # Save current grid state
    gamefile["grids"][grid_id] = grid
    
    # Respawn at grid 1, position 0,0
    new_grid_id = "1"
    new_grid = gamefile["grids"][new_grid_id]
    new_grid_size = [len(new_grid[0]), len(new_grid)]
    new_x, new_y = 0, 0
    new_prevx, new_prevy = -1, -1
    
    return (coins, new_x, new_y, new_prevx, new_prevy, new_grid_id, 
            new_grid, new_grid_size, death_message)

def change_grid(deltax, deltay, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies):
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

    # Spawn new enemies in the new grid (30% chance)
    enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
    new_enemies = spawn_enemies_in_grid(grid, enemy_level, enemies[grid_id])
    enemies[grid_id].extend(new_enemies)

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

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, health, enemies=[], cleared=False, got_item=None, equipped="", combat_log=None):
    if cleared == True:
        stdscr.clear()
    if prevx >= 0 and prevy >= 0:
        grid[prevy][prevx] = ' '
    grid[y][x] = '0'
    display_grid = [row[:] for row in grid]
    for enemy in enemies:
        if enemy.status != "Dead":
            display_grid[enemy.y][enemy.x] = 'E'
    for i in range(grid_size[1]):
        stdscr.addstr(i+1,0,"|")
        stdscr.addstr(i+1,grid_size[0]+1,"|")
        for j in range(grid_size[0]):
            stdscr.addstr(0,j+1,"-")
            stdscr.addstr(grid_size[1]+1,j+1,"-")
            stdscr.addstr(i+1,j+1,display_grid[i][j])
    stdscr.addstr(grid_size[1]+3,0,f"Grid: {((int(grid_id)-1)%5)+1}, {math.floor((int(grid_id)-1)/5)+1}")
    stdscr.addstr(grid_size[1]+4,0,f"Coins: {coins}")
    stdscr.addstr(grid_size[1]+5,0,f"Equipped: {equipped}")
    stdscr.addstr(grid_size[1]+6,0,f"Atk: {atk} | Health: {health} | Armor: {armor}")
    stdscr.addstr(grid_size[1]+9,0,"wasd/arrows:move | q:quit | i:inventory | enter:action")
    if forge["state"] == "Discovered":
        stdscr.addstr(grid_size[1]+7,0, f'Forge: {forge["gridx"]}, {forge["gridy"]}')
    if got_item:
        stdscr.addstr(grid_size[1]+10,0,f"{got_item} has been acquired!")
    if combat_log:
        for i, log_entry in enumerate(combat_log):
            if i < 3:
                stdscr.addstr(grid_size[1]+11+i,0,log_entry)
    stdscr.refresh()

def serialize_enemies(enemies):
    """Convert enemies to saveable format"""
    serialized = {}
    for grid_id, enemy_list in enemies.items():
        serialized[grid_id] = []
        for enemy in enemy_list:
            if enemy.status != "Dead":  # Only save living enemies
                serialized[grid_id].append({
                    "x": enemy.x,
                    "y": enemy.y,
                    "level": enemy.level,
                    "health": enemy.health,
                    "status": enemy.status,
                    "chase_moves": enemy.chase_moves
                })
    return serialized

def deserialize_enemies(serialized_enemies):
    """Load enemies from saved format"""
    enemies = {}
    for grid_id in [str(i) for i in range(1, 21)]:
        enemies[grid_id] = []
        
        if grid_id in serialized_enemies:
            for enemy_data in serialized_enemies[grid_id]:
                enemy = Enemy(enemy_data["x"], enemy_data["y"], enemy_data["level"])
                enemy.health = enemy_data["health"]
                enemy.status = enemy_data["status"]
                enemy.chase_moves = enemy_data["chase_moves"]
                enemies[grid_id].append(enemy)
    
    return enemies

class Player:
    def __init__(self, health):
        self.health = health

def main(stdscr):

    with open("grids.json", "r") as file:
        gamefile = json.load(file)

    grid_id = gamefile["curr_grid"]
    grid_size = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]
    grid = gamefile["grids"][grid_id]
    inv = gamefile["inventory"]
    essentials = gamefile["essentials"]

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    x,y = gamefile["player"]
    coins = gamefile["coins"]
    forge = gamefile["forge"]
    equipped = gamefile["equipped"]
    mills = gamefile["mills"]
    health = gamefile["health"]
    curr_mill = None
    prevx, prevy = -1,-1
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

    # Initialize enemies
    if "enemies" in gamefile:
        enemies = deserialize_enemies(gamefile["enemies"])
    else:
        # First time - initialize enemies
        enemies = {}
        for grid_num in range(1, 21):
            enemies[str(grid_num)] = []
            if random.random() < 0.3:
                enemy_level = max(1, (grid_num - 1) // 4 + 1)
                enemy = spawn_enemy_in_grid(gamefile["grids"][str(grid_num)], enemy_level)
                if enemy:
                    enemies[str(grid_num)].append(enemy)

    player = Player(health)
    combat_log = None

    for enemy in enemies[grid_id][:]:
        if enemy.status == "Dead":
            enemies[grid_id].remove(enemy)
        else:
            # Check proximity to player
            enemy.check_prox(x, y)
            
            # Act based on current status
            if enemy.status == "Alert":
                enemy.alert(grid, x, y)
            elif enemy.status == "Roam":
                enemy.roam(grid)
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, player.health, enemies[grid_id], equipped=equipped)
    item = None
    ec = 0

    while True:
        clear_grid = False
        key = stdscr.getch()
        
        # Movement and attack
        moved = False
        if key == ord('w') or key == curses.KEY_UP:
            if y > 0:
                new_x, new_y = x, y - 1
                if not is_position_blocked(new_x, new_y, enemies[grid_id]):
                    prevx, prevy = x, y
                    y = new_y
                    moved = True
                else:
                    # Try to attack adjacent enemy instead
                    attack_result = check_adjacent_enemy_attack(enemies[grid_id], x, y, atk, player, armor)
                    if attack_result.get("collision", False):
                        combat_log = attack_result.get("log", [])
                        if attack_result.get("player_died", False):
                            (coins, x, y, prevx, prevy, grid_id, grid, grid_size, 
                            death_message) = handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile)
                            combat_log = [death_message, "Respawned at starting location."]
                            clear_grid = True
                        if attack_result.get("enemy_died", False):
                            coins += attack_result["coins_gained"]
                            enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
                            inv, drops = handle_enemy_death(inv, enemy_level)
                            if drops:
                                drop_text = ", ".join(drops)
                                combat_log.append(f"Enemy dropped: {drop_text}!")
                        clear_grid = True
            elif y <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, -1, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies)
                clear_grid = True
                moved = True

        elif key == ord('s') or key == curses.KEY_DOWN:
            if y < grid_size[1]-1:
                new_x, new_y = x, y + 1
                if not is_position_blocked(new_x, new_y, enemies[grid_id]):
                    prevx, prevy = x, y
                    y = new_y
                    moved = True
                else:
                    # Try to attack adjacent enemy instead
                    attack_result = check_adjacent_enemy_attack(enemies[grid_id], x, y, atk, player, armor)
                    if attack_result.get("collision", False):
                        combat_log = attack_result.get("log", [])
                        if attack_result.get("player_died", False):
                            (coins, x, y, prevx, prevy, grid_id, grid, grid_size, 
                            death_message) = handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile)
                            combat_log = [death_message, "Respawned at starting location."]
                            clear_grid = True
                        if attack_result.get("enemy_died", False):
                            coins += attack_result["coins_gained"]
                            enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
                            inv, drops = handle_enemy_death(inv, enemy_level)
                            if drops:
                                drop_text = ", ".join(drops)
                                combat_log.append(f"Enemy dropped: {drop_text}!")
                        clear_grid = True
            elif y >= grid_size[1]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, 1, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies)
                clear_grid = True
                moved = True

        elif key == ord('a') or key == curses.KEY_LEFT:
            if x > 0:
                new_x, new_y = x - 1, y
                if not is_position_blocked(new_x, new_y, enemies[grid_id]):
                    prevx, prevy = x, y
                    x = new_x
                    moved = True
                else:
                    # Try to attack adjacent enemy instead
                    attack_result = check_adjacent_enemy_attack(enemies[grid_id], x, y, atk, player, armor)
                    if attack_result.get("collision", False):
                        combat_log = attack_result.get("log", [])
                        if attack_result.get("player_died", False):
                            (coins, x, y, prevx, prevy, grid_id, grid, grid_size, 
                            death_message) = handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile)
                            combat_log = [death_message, "Respawned at starting location."]
                            clear_grid = True
                        if attack_result.get("enemy_died", False):
                            coins += attack_result["coins_gained"]
                            enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
                            inv, drops = handle_enemy_death(inv, enemy_level)
                            if drops:
                                drop_text = ", ".join(drops)
                                combat_log.append(f"Enemy dropped: {drop_text}!")
                        clear_grid = True
            elif x <= 0:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies)
                clear_grid = True
                moved = True

        elif key == ord('d') or key == curses.KEY_RIGHT:
            if x < grid_size[0]-1:
                new_x, new_y = x + 1, y
                if not is_position_blocked(new_x, new_y, enemies[grid_id]):
                    prevx, prevy = x, y
                    x = new_x
                    moved = True
                else:
                    # Try to attack adjacent enemy instead
                    attack_result = check_adjacent_enemy_attack(enemies[grid_id], x, y, atk, player, armor)
                    if attack_result.get("collision", False):
                        combat_log = attack_result.get("log", [])
                        if attack_result.get("player_died", False):
                            (coins, x, y, prevx, prevy, grid_id, grid, grid_size, 
                            death_message) = handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile)
                            combat_log = [death_message, "Respawned at starting location."]
                            clear_grid = True
                        if attack_result.get("enemy_died", False):
                            coins += attack_result["coins_gained"]
                            enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
                            inv, drops = handle_enemy_death(inv, enemy_level)
                            if drops:
                                drop_text = ", ".join(drops)
                                combat_log.append(f"Enemy dropped: {drop_text}!")
                        clear_grid = True
            elif x >= grid_size[0]-1:
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies)
                clear_grid = True
                moved = True

        if key in [ord('w'), ord('s'), ord('a'), ord('d')] and not moved:
            print(f"Trying adjacent attack at {x},{y}")  # Debug
            # Manual check for adjacent enemies
            for enemy in enemies[grid_id]:
                if enemy.status != "Dead":
                    distance = abs(enemy.x - x) + abs(enemy.y - y)
                    if distance == 1:  # Adjacent
                        print(f"Found adjacent enemy at {enemy.x},{enemy.y}")
                        combat_log = [f"Attacking enemy! Damage: {atk}"]
                        clear_grid = True
                        break

        if key in [ord('w'), ord('s'), ord('a'), ord('d'), curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            collision_result = check_enemy_collisions(enemies[grid_id], x, y, atk, player)
            if collision_result.get("collision", True):
                combat_log = collision_result.get("log", [])
                
                if collision_result.get("player_died", False):
                    (coins, x, y, prevx, prevy, grid_id, grid, grid_size, 
                    death_message) = handle_player_death(player, coins, grid_id, x, y, prevx, prevy, grid, gamefile)
                    combat_log = [death_message, "Respawned at starting location."]
                    clear_grid = True
                
                if collision_result.get("enemy_died", False):
                    coins += collision_result["coins_gained"]
                    enemy_level = max(1, (int(grid_id) - 1) // 4 + 1)
                    inv, drops = handle_enemy_death(inv, enemy_level)
                    if drops:
                        drop_text = ", ".join(drops)
                        combat_log.append(f"Enemy dropped: {drop_text}!")
                
                clear_grid = True

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
            ec+=1
            if ec > len(essentials)-1: ec = len(essentials)-1
            equipped = essentials[ec]
            clear_grid = True
        elif key == ord('k') and essentials != []:
            ec-=1
            if ec < 0: ec = 0
            equipped = essentials[ec]
            clear_grid = True

        # Exit
        elif key == ord('q'):
            gamefile["grids"][grid_id] = grid
            gamefile["curr_grid"] = grid_id
            gamefile["player"] = [x,y]
            gamefile["inventory"] = inv
            gamefile["coins"] = coins
            gamefile["forge"] = forge
            gamefile["equipped"] = equipped
            gamefile["essentials"] = essentials
            gamefile["mills"] = mills
            gamefile["health"] = player.health
            gamefile["attack"] = atk
            gamefile["enemies"] = serialize_enemies(enemies)
            with open("grids.json", "w") as f:
                json.dump(gamefile, f)
            sys.exit(0)
       
        if grid[y][x] == "o":
            coins = add_coins(coins)
            clear_grid = True
        elif grid[y][x] == "?":
            item = get_item()
            if item != "":
                if item in ["Wood", "Iron"]:
                    add_ = random.randint(2,5)
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
                    inv = add_to_inv("Fuel", inv, random.randint(3,10))
                elif 0.5 <= Fuelprob < 0.501:
                    item = "Super Seed"
                    inv = add_to_inv("Super Seed", inv, random.randint(3,10))
                else:
                    item = None
                    clear_grid = True
            elif equipped == "Mill lot" or equipped == "Big mill lot" or equipped == "Fuel Dispenser":
                mills, inv, grid = place_mill(stdscr, equipped, mills, grid_id, grid, grid_size, inv)
                essentials = [e for e in essentials for i in inv if e in i]
                equipped = ""
                clear_grid = True
            elif equipped == "Potion":
                for i in range(len(inv)):
                    if inv[i][0] == "Potion":
                        inv[i][1] -= 1
                        player.health += 10
                        if player.health > 300:
                            player.health = 300
                        if inv[i][1] <= 0:
                            equipped = ""
                essentials = [e for e in essentials for i in inv if e in i]
                inv = [i for i in inv if i[1] > 0]
                clear_grid = True
        elif grid[y][x] == "D":
            coins -= 15
            for i in range(len(inv)):
                if inv[i][0] == "Fuel":
                    inv[i][1] += 1
                    break
            x = prevx
            y = prevy
            item = "Fuel"
            clear_grid = True
        elif grid[y][x] == "T":
            if equipped == "Axe":
                inv = add_to_inv("Wood", inv, random.randint(2,10))
                item = "Wood"
                grid[y][x] = " "
            x = prevx
            y = prevy
        elif grid[y][x] == "*":
            if equipped == "Pickaxe":
                inv = add_to_inv("Iron", inv, random.randint(2,10))
                item = "Iron"
                grid[y][x] = " "
            x = prevx
            y = prevy
        elif grid[y][x] == "m" or grid[y][x] == "M":
            curr_mill = mills[f"mill_{grid_id}_{x}_{y}"]
            x = prevx
            y = prevy
            inv, coins, curr_mill = start_mill(stdscr, inv, coins, curr_mill)
            essentials = [e for e in essentials for i in inv if e in i]
            mills[f"mill_{grid_id}_{x}_{y}"] = curr_mill
            curr_mill = None
            clear_grid = True
        elif grid[y][x] == "F":
            x = prevx
            y = prevy
            inv, coins = start_forge(stdscr, inv, coins)
            essentials = [e for e in essentials for i in inv if e in i]
            clear_grid = True

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

        for enemy in enemies[grid_id][:]:
            if enemy.status == "Dead":
                enemies[grid_id].remove(enemy)
            else:
                # Check proximity to player
                enemy.check_prox(x, y)
                
                # Act based on current status
                if enemy.status == "Alert":
                    enemy.alert(grid, x, y)
                elif enemy.status == "Roam":
                    enemy.roam(grid)

        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, player.health, enemies[grid_id], cleared=clear_grid, got_item=item, equipped=equipped, combat_log=combat_log)
        if item:
            item = None

curses.wrapper(main)
