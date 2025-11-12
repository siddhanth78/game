import curses
import sys
import json
import math
import random
from inventory import add_to_inv, inventory
from vendor import start_vendor
from enemy import Enemy, spawn_enemy_in_grid, check_adjacent_enemy_attack
from enemy import spawn_final_boss
from player_ascension import get_enemy_scale_multiplier, save_ascension_data

def add_coins(coins):
    coins += random.randint(10, 30)
    return coins

def get_item():
    chance = random.random()
    item = None
    if 0 <= chance < 0.30:
        item = "Potion"
    elif 0.3 <= chance < 0.5:
        item = "Spark"
    elif 0.50 <= chance < 0.6:
        item = "Radon"
    elif 0.80 <= chance < 0.9:
        item = "Super Seed"
    else:
        item = ""
    return item

def handle_enemy_death(inv, enemy_level):
    """Handle enemy death drops - 10% Potion, 5% Super Seed, 10% Radon"""
    drops = []
    
    # 10% chance for Potion
    if random.random() < 0.10:
        inv = add_to_inv("Potion", inv, 1)
        drops.append("Potion")
    
    # 5% chance for Super Seed
    if random.random() < 0.05:
        inv = add_to_inv("Super Seed", inv, 1)
        drops.append("Super Seed")
    
    # 10% chance for Radon
    if random.random() < 0.10:
        inv = add_to_inv("Radon", inv, 1)
        drops.append("Radon")

    # 10% chance for Spark
    if random.random() < 0.10:
        inv = add_to_inv("Spark", inv, 1)
        drops.append("Spark")
    
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

    if random.random() < 0.80:
        rows, cols = len(grid), len(grid[0])
        num_enemies = random.randint(1, max_enemies)
        
        for _ in range(num_enemies):
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                x = random.randint(1, cols - 2)
                y = random.randint(1, rows - 2)
                
                # Can spawn on empty space, coins, question marks, or healing spots
                if grid[y][x] in [' ', 'o', '?', '+']:
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

def change_grid(deltay, x, y, prevx, prevy, grid_id, grid, gamefile, enemies, vendor, ascension_data):
    """Modified to accept ascension_data parameter instead of loading it"""
    prevgridsize = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]

    new_grid_num = int(grid_id) + deltay

    # Check if new grid number is valid (1-40)
    if new_grid_num < 1 or new_grid_num > 40:
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile

    new_grid_id = str(new_grid_num)
    new_grid = gamefile["grids"][new_grid_id]
    new_grid_size = [len(new_grid[0]), len(new_grid)]

    # Set new position based on vertical movement
    if deltay > 0:  # Moving down
        new_x = min(max(0, x), new_grid_size[0] - 1)
        new_y = 0
    elif deltay < 0:  # Moving up
        new_x = min(max(0, x), new_grid_size[0] - 1)
        new_y = new_grid_size[1] - 1

    grid[y][x] = ' '
    gamefile["grids"][grid_id] = grid
    
    # Switch to new grid
    grid_id = new_grid_id
    grid = new_grid
    grid_size = new_grid_size

    # Vendor discovery logic
    if vendor["loc"] == grid_id and vendor["state"] == "Undiscovered":
        vendor["state"] = "Discovered"

    # Determine enemy level based on grid number (1-40)
    grid_num = int(grid_id)
    
    # Special handling for depth 40 - spawn only final boss
    if grid_num == 40 and ascension_data["boss_kills"] == 0:
        if not enemies[grid_id]:  # Only spawn boss if no enemies exist
            ascension_level = ascension_data["level"]
            
            boss = spawn_final_boss(grid, 40)
            if boss:
                boss.health = 1000 * (1 + ascension_level * 1.5)
                boss.max_health = 1000 * (1 + ascension_level * 1.5)
                boss.attack = 100 * (1 + ascension_level * 0.5)
                enemies[grid_id] = [boss]
    else:
        # Normal enemy spawning for other depths with ascension scaling
        enemy_multiplier = get_enemy_scale_multiplier(ascension_data["level"])
        
        if grid_num <= 5:
            base_level = random.randint(1, 5)
        elif grid_num <= 10:
            base_level = random.randint(6, 10)
        elif grid_num <= 15:
            base_level = random.randint(11, 15)
        elif grid_num <= 20:
            base_level = random.randint(16, 20)
        elif grid_num <= 25:
            base_level = random.randint(21, 25)
        elif grid_num <= 30:
            base_level = random.randint(26, 30)
        elif grid_num <= 35:
            base_level = random.randint(31, 35)
        else:
            base_level = random.randint(36, 40)

        # Apply ascension scaling to enemy level
        scaled_level = int(base_level * enemy_multiplier)
        
        # Spawn new enemies if none exist
        new_enemies = spawn_enemies_in_grid(grid, scaled_level, enemies[grid_id])
        enemies[grid_id].extend(new_enemies)

    # Add scattered '?' symbols and healing spots
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
    
    # Add healing spots
    if random.random() <= 0.15:
        num_healing_spots = random.randint(1, 3)
        for _ in range(num_healing_spots):
            attempts = 0
            while attempts < 100:
                hx = random.randint(1, grid_size[0] - 2)
                hy = random.randint(1, grid_size[1] - 2)
                if grid[hy][hx] == ' ':
                    grid[hy][hx] = '+'
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
            bunch_size = random.randint(min_bunch, max_bunch)
            
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

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, vendor, atk, armor, health, enemies=[],
                  cleared=False, got_item=None, equipped="", combat_log=None, ascension_data=None):
    if cleared:
        stdscr.clear()

    if prevx >= 0 and prevy >= 0 and (prevx != x or prevy != y):
        if 0 <= prevy < len(grid) and 0 <= prevx < len(grid[0]):
            grid[prevy][prevx] = ' '

    display_grid = [row[:] for row in grid]

    if 0 <= y < len(display_grid) and 0 <= x < len(display_grid[0]):
        display_grid[y][x] = '0'

    for enemy in enemies:
        if enemy.status != "Dead":
            if 0 <= enemy.y < len(display_grid) and 0 <= enemy.x < len(display_grid[0]):
                display_grid[enemy.y][enemy.x] = enemy.symbol  # Use enemy.symbol instead of 'E'

    for i in range(grid_size[1]):
        stdscr.addstr(i+1, 0, "|")
        stdscr.addstr(i+1, grid_size[0]+1, "|")
        for j in range(grid_size[0]):
            stdscr.addstr(0, j+1, "-")
            stdscr.addstr(grid_size[1]+1, j+1, "-")
            stdscr.addstr(i+1, j+1, display_grid[i][j])
    
    stdscr.addstr(grid_size[1]+3, 0, f"Depths Level: {grid_id}")
    stdscr.addstr(grid_size[1]+4, 0, f"Coins: {coins}")
    stdscr.addstr(grid_size[1]+5, 0, f"Equipped: {equipped}")
    stdscr.addstr(grid_size[1]+6, 0, f"Atk: {atk} | Health: {health} | Armor: {armor}")

    bar = "wasd/arrows:move | q:quit | i:inventory | enter:action | j/k:switch"
    
    if vendor["state"] == "Discovered":
        stdscr.addstr(grid_size[1]+7, 0, f'Vendor: Level {vendor["loc"]}')
        if ascension_data["unlocks"]["fast_access"]:
            bar += " | v:vendor"

    stdscr.addstr(grid_size[1]+9, 0, bar)
    
    if got_item:
        stdscr.addstr(grid_size[1]+10, 0, f"{got_item} has been acquired!")
    if combat_log:
        for i, log_entry in enumerate(combat_log):
            if i < 3:
                stdscr.addstr(grid_size[1]+11+i, 0, log_entry)
    
    stdscr.refresh()

def serialize_enemies(enemies):
    """Convert enemies to saveable format"""
    serialized = {}
    for grid_id, enemy_list in enemies.items():
        serialized[grid_id] = []
        for enemy in enemy_list:
            if enemy.status != "Dead":
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
    for grid_id in [str(i) for i in range(1, 41)]:
        enemies[grid_id] = []
        
        if grid_id in serialized_enemies:
            for enemy_data in serialized_enemies[grid_id]:
                if grid_id == "40":
                    enemy = Enemy(enemy_data["x"], enemy_data["y"], enemy_data["level"], is_final_boss=True)
                else:
                    enemy = Enemy(enemy_data["x"], enemy_data["y"], enemy_data["level"])
                enemy.health = enemy_data["health"]
                enemy.status = enemy_data["status"]
                enemy.chase_moves = enemy_data["chase_moves"]
                enemies[grid_id].append(enemy)
    
    return enemies

class Player:
    def __init__(self, health):
        self.health = health

def start_depths(mx, my,stdscr, atk, health, coins, inv, equipped, essentials, ascension_data):

    with open("depths.json", "r") as file:
        gamefile = json.load(file)

    grid_id = gamefile["curr_grid"]
    grid_size = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]
    grid = gamefile["grids"][grid_id]
    
    # Initialize vendor
    if "vendor" not in gamefile:
        vendor_location = random.randint(5, 35)  # Vendor appears somewhere between level 5-35
        gamefile["vendor"] = {
            "loc": str(vendor_location),
            "state": "Undiscovered"
        }
    vendor = gamefile["vendor"]

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
        regen = 2
    elif "Epic Shield" in essentials:
        armor = 50
        regen = 1
    elif "Big Shield" in essentials:
        armor = 20
        regen = 0
    elif "Shield" in essentials:
        armor = 5
        regen = 0
    else:
        armor = 0
        regen = 0

    # Initialize enemies with ascension scaling
    if "enemies" in gamefile:
        enemies = deserialize_enemies(gamefile["enemies"])
    else:
        enemy_multiplier = get_enemy_scale_multiplier(ascension_data["level"])
        
        enemies = {}
        for grid_num in range(1, 40):
            enemies[str(grid_num)] = []
            if random.random() < 0.3:
                # Scale enemy level based on depth
                if grid_num <= 5:
                    base_level = random.randint(1, 5)
                elif grid_num <= 10:
                    base_level = random.randint(6, 10)
                elif grid_num <= 15:
                    base_level = random.randint(11, 15)
                elif grid_num <= 20:
                    base_level = random.randint(16, 20)
                elif grid_num <= 25:
                    base_level = random.randint(21, 25)
                elif grid_num <= 30:
                    base_level = random.randint(26, 30)
                elif grid_num <= 35:
                    base_level = random.randint(31, 35)
                else:
                    base_level = random.randint(36, 40)
                
                # Apply ascension scaling
                scaled_level = int(base_level * enemy_multiplier)
                enemy = spawn_enemy_in_grid(gamefile["grids"][str(grid_num)], scaled_level)
                if enemy:
                    enemies[str(grid_num)].append(enemy)

        enemies["40"] = []

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
    
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, vendor, atk, armor, player.health,
                  enemies[grid_id], equipped=equipped, cleared=True, ascension_data=ascension_data)
    item = None
    ec = 0

    while True:
        clear_grid = False
        key = stdscr.getch()

        if key in [ord('w'), ord('s'), ord('a'), ord('d'), curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            player.health += regen
            if player.health > 300:
                player.health = 300
            
            # Determine target position based on key
            target_x, target_y = x, y
            if key == ord('w') or key == curses.KEY_UP:
                target_y = y - 1
            elif key == ord('s') or key == curses.KEY_DOWN:
                target_y = y + 1
            elif key == ord('a') or key == curses.KEY_LEFT:
                target_x = x - 1
            elif key == ord('d') or key == curses.KEY_RIGHT:
                target_x = x + 1
            
            # Check if target position has an enemy - if so, attack it
            attack_result = check_adjacent_enemy_attack(enemies[grid_id], target_x, target_y, atk, player, armor)
            
            if attack_result.get("collision", False):
                # Combat happened
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
                
                if attack_result.get("boss_defeated", False):
                    combat_log.append("Press 'Shift+A' to ascend once exited!")
                    ascension_data["boss_kills"] += 1
                    ascension_data = save_ascension_data(ascension_data)
                
                clear_grid = True
            else:
                # No enemy at target position, try to move there
                if target_y < 0:  # Moving up, change grid
                    x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, x, y, prevx, prevy, grid_id, grid, gamefile, enemies, vendor, ascension_data)
                    clear_grid = True
                elif target_y >= grid_size[1]:  # Moving down, change grid  
                    x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, x, y, prevx, prevy, grid_id, grid, gamefile, enemies, vendor, ascension_data)
                    clear_grid = True
                elif 0 <= target_x < grid_size[0] and 0 <= target_y < grid_size[1] and not is_position_blocked(target_x, target_y, enemies[grid_id]):
                    # Valid move within grid
                    prevx, prevy = x, y
                    x, y = target_x, target_y

        elif key == ord("v"):
            inv, coins = start_vendor(stdscr, inv, coins)
            essentials = [e for e in essentials if e in inv]
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
            gamefile["vendor"] = vendor
            gamefile["enemies"] = serialize_enemies(enemies)

            ascension_data = save_ascension_data(ascension_data)

            with open("depths.json", "w") as f:
                json.dump(gamefile, f)

            with open("grids.json", "r") as file:
                main_game = json.load(file)

            main_game["inventory"] = inv
            main_game["coins"] = coins
            main_game["equipped"] = equipped
            main_game["essentials"] = essentials
            main_game["health"] = player.health
            main_game["attack"] = atk
            main_game["player"] = [mx, my]
            
            # Save ascension data
            ascension_data = save_ascension_data(ascension_data)
            
            with open("grids.json", "w") as f:
                json.dump(main_game, f)
            sys.exit(0)
       
        if grid[y][x] == "o":
            coins = add_coins(coins)
            clear_grid = True
        elif grid[y][x] == "?":
            item = get_item()
            if item != "":
                add_ = 1
                inv = add_to_inv(item, inv, add_)
                clear_grid = True
            else:
                item = None
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord('\r'):
            if equipped == "Pickaxe":
                Fuelprob = random.random()
                if 0.5 <= Fuelprob < 0.501:
                    item = "Super Seed"
                    inv = add_to_inv("Super Seed", inv, random.randint(3,10))
                else:
                    item = None
                    clear_grid = True
            elif equipped == "Potion":
                inv["Potion"] -= 1
                player.health += 10
                if player.health > 300:
                    player.health = 300
                if inv["Potion"] <= 0:
                    del inv["Potion"]
                    equipped = ""
                essentials = [e for e in essentials if e in inv]
                clear_grid = True
        elif grid[y][x] == "+":
            player.health += 2
            if player.health > 300:
                player.health = 300
            clear_grid = True
        elif grid[y][x] == "V":
            x = prevx
            y = prevy
            inv, coins = start_vendor(stdscr, inv, coins)
            essentials = [e for e in essentials if e in inv]
            clear_grid = True
        elif grid[y][x] == ">":
            x = prevx
            y = prevy
            gamefile["grids"][grid_id] = grid
            gamefile["curr_grid"] = grid_id
            gamefile["vendor"] = vendor
            gamefile["enemies"] = serialize_enemies(enemies)
            ascension_data = save_ascension_data(ascension_data)
            with open("depths.json", "w") as f:
                json.dump(gamefile, f)
            
            # Return values to main game
            return atk, player.health, coins, inv, equipped, essentials, ascension_data

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
            regen = 2
        elif "Epic Shield" in essentials:
            armor = 50
            regen = 1
        elif "Big Shield" in essentials:
            armor = 20
            regen = 0
        elif "Shield" in essentials:
            armor = 5
            regen = 0
        else:
            armor = 0
            regen = 0

        for enemy in enemies[grid_id][:]:
            if enemy.status == "Dead":
                enemies[grid_id].remove(enemy)
            else:
                # Update boss modes and get any mode change messages
                if hasattr(enemy, 'is_final_boss') and enemy.is_final_boss:
                    mode_messages = enemy.update_boss_mode()
                    if mode_messages:
                        combat_log = mode_messages  # Show mode changes
                        clear_grid = True
                
                # Check proximity to player
                enemy.check_prox(x, y)
                
                # Act based on current status
                if enemy.status == "Alert":
                    enemy.alert(grid, x, y)
                elif enemy.status == "Roam":
                    enemy.roam(grid)

        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, vendor, atk, armor, player.health,
                      enemies[grid_id], cleared=clear_grid, got_item=item, equipped=equipped, combat_log=combat_log, ascension_data=ascension_data)
        if item:
            item = None