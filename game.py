import curses
import sys
import json
import math
import random
from inventory import add_to_inv, inventory
from forge import start_forge
from mill import start_mill, place_mill
from enemy import Enemy, spawn_enemy_in_grid, check_adjacent_enemy_attack
from start_depths import start_depths
from player_ascension import load_ascension_data, ascend_player, save_ascension_data, get_ascension_display_info
import gen_depths

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

    if random.random() < 0.80:
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

def change_grid(deltax, deltay, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies, clear_20=0):
    prevgridsize = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]

    new_grid_num = int(grid_id) + deltax + (deltay * 5)

    if (int(grid_id) % 5 == 1 and deltax < 0) or (int(grid_id) % 5 == 0 and deltax > 0):
        return x, y, prevx, prevy, grid_id, grid, prevgridsize, gamefile
    if (int(grid_id) in [1,2,3,4,5] and deltay < 0) or (int(grid_id) in [16,17,18,19,20] and deltay > 0):
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

    if forge["loc"] == grid_id and forge["state"] == "Undiscovered":
        forge["gridx"] = ((int(grid_id)-1) % 5) + 1
        forge["gridy"] = math.floor((int(grid_id)-1) / 5) + 1
        forge["state"] = "Discovered"

    grid_num = int(grid_id)
    if grid_num <= 5:
        enemy_level = 1
    elif grid_num <= 10:
        enemy_level = random.randint(2, 3)
    elif grid_num <= 15:
        enemy_level = random.randint(4, 7)
    elif grid_num <= 19:
        enemy_level = random.randint(8, 15)
    else:
        rows, cols = len(grid), len(grid[0])
        num_enemies = 10
        spawned_enemies = []
        for _ in range(num_enemies):
            attempts = 0
            while attempts < 50:
                ex = random.randint(1, cols - 2)
                ey = random.randint(1, rows - 2)
                el = random.randint(10, 14)
                
                if grid[ey][ex] in [' ', 'o', '?']:
                    enemy = Enemy(ex, ey, el)
                    spawned_enemies.append(enemy)
                    break
                
                attempts += 1

    if grid_num == 20 and clear_20 == 0:
        if enemies[grid_id] == []:
            new_enemies = spawned_enemies
            enemies[grid_id] = new_enemies
    elif grid_num == 20 and clear_20 == 1:
        enemies[grid_id] = []
    else:
        new_enemies = spawn_enemies_in_grid(grid, enemy_level, enemies[grid_id])
        enemies[grid_id].extend(new_enemies)

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

def update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, health, enemies=[], cleared=False, got_item=None, equipped="", combat_log=None, ascension_data=None):
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
                display_grid[enemy.y][enemy.x] = 'E'

    for i in range(grid_size[1]):
        stdscr.addstr(i+1, 0, "|")
        stdscr.addstr(i+1, grid_size[0]+1, "|")
        for j in range(grid_size[0]):
            stdscr.addstr(0, j+1, "-")
            stdscr.addstr(grid_size[1]+1, j+1, "-")
            stdscr.addstr(i+1, j+1, display_grid[i][j])
    
    stdscr.addstr(grid_size[1]+3, 0, f"Grid: {((int(grid_id)-1)%5)+1}, {math.floor((int(grid_id)-1)/5)+1}")
    stdscr.addstr(grid_size[1]+4, 0, f"Coins: {coins}")
    stdscr.addstr(grid_size[1]+5, 0, f"Equipped: {equipped}")
    stdscr.addstr(grid_size[1]+6, 0, f"Atk: {atk} | Health: {health} | Armor: {armor}")
    
    # Add ascension info display
    ascension_info = get_ascension_display_info(ascension_data)
    stdscr.addstr(grid_size[1]+8, 0, ascension_info)

    bar = "wasd/arrows:move | q:quit | i:inventory | enter:action | j/k:switch equipped"

    if ascension_data["boss_kills"] > 0:
        bar += " | A:ASCEND"
    
    if forge["state"] == "Discovered":
        stdscr.addstr(grid_size[1]+7, 0, f'Forge: {forge["gridx"]}, {forge["gridy"]}')
        if ascension_data["unlocks"]["fast_access"]:
            bar += " | f:forge"

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
    # Load ascension data
    ascension_data = load_ascension_data()

    with open("grids.json", "r") as file:
        gamefile = json.load(file)

    grid_id = gamefile["curr_grid"]
    grid_size = [len(gamefile["grids"][grid_id][0]), len(gamefile["grids"][grid_id])]
    grid = gamefile["grids"][grid_id]
    inv = gamefile["inventory"]
    essentials = gamefile["essentials"]
    cl20 = gamefile["clear_20"]

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

    # Initialize enemies
    if "enemies" in gamefile:
        enemies = deserialize_enemies(gamefile["enemies"])
    else:
        # First time - initialize enemies
        enemies = {}
        for grid_num in range(1, 20):
            enemies[str(grid_num)] = []
            if random.random() < 0.3:
                enemy_level = max(1, (grid_num - 1) // 4 + 1)
                enemy = spawn_enemy_in_grid(gamefile["grids"][str(grid_num)], enemy_level)
                if enemy:
                    enemies[str(grid_num)].append(enemy)

        enemies["20"] = []
        gamefile["enemies"] = serialize_enemies(enemies)

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
    
    # Get ascension display info
    ascension_info = get_ascension_display_info(ascension_data)
    
    update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, player.health, enemies[grid_id], equipped=equipped, ascension_data=ascension_data)
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
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, -1, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies, clear_20=cl20)
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
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(0, 1, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies, clear_20=cl20)
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
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(-1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies, clear_20=cl20)
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
                x, y, prevx, prevy, grid_id, grid, grid_size, gamefile = change_grid(1, 0, x, y, prevx, prevy, grid_id, grid, gamefile, forge, enemies, clear_20=cl20)
                clear_grid = True
                moved = True

        # Ascension (Shift+A)
        elif key == ord('A'):  # Capital A (Shift+A)
            if ascension_data["boss_kills"] > 0:
                messages, reset_needed, ascension_data = ascend_player(ascension_data)
                for msg in messages:
                    combat_log = [msg] if not combat_log else combat_log + [msg]
                ascension_data = save_ascension_data(ascension_data)
                
                if reset_needed:
                    n_inv = {"Axe": 1, "Pickaxe": 1}
                    if ascension_data["level"] == 1:
                        n_inv["Big Sword"] = 1
                        n_inv["Big Shield"] = 1
                        n_inv["Radon"] = 10
                        n_inv["Potion"] = 10
                    elif ascension_data["level"] == 2:
                        n_inv["Epic Sword"] = 1
                        n_inv["Epic Shield"] = 1
                        n_inv["Radon"] = 10
                        n_inv["Potion"] = 20
                        n_inv["Spark"] = 10
                    elif ascension_data["level"] == 3:
                        n_inv["Epic Sword"] = 1
                        n_inv["Epic Shield"] = 1
                        n_inv["Radon"] = 10
                        n_inv["Potion"] = 25
                        n_inv["Spark"] = 20
                    elif ascension_data["level"] == 4:
                        n_inv["Epic Sword"] = 1
                        n_inv["Epic Shield"] = 1
                        n_inv["Radon"] = 15
                        n_inv["Potion"] = 30
                        n_inv["Spark"] = 30
                    elif ascension_data["level"] == 5:
                        n_inv["Godly Sword"] = 1
                        n_inv["Godly Shield"] = 1
                        n_inv["Radon"] = 50
                        n_inv["Potion"] = 50
                        n_inv["Spark"] = 50
                    n_gamefile = {
                        "grids": gamefile["grids"],
                        "curr_grid": "1",
                        "player": [0, 0],
                        "inventory": n_inv,
                        "coins": 0,
                        "health": 300,
                        "attack": 1,
                        "forge": gamefile["forge"],
                        "equipped": "",
                        "essentials": [],
                        "mills": gamefile.get("mills", {}),
                        "clear_20": 0
                    }

                    with open("grids.json", "w") as file:
                        json.dump(n_gamefile, file, indent=2)
                    
                    # Also reset depths completely
                    gen_depths.generate()
                    # Show reset message and exit to main game
                    stdscr.clear()
                    stdscr.addstr(0, 0, "ASCENSION COMPLETE!")
                    stdscr.addstr(2, 0, "All progress reset. Starting fresh in the main world.")
                    stdscr.addstr(3, 0, "Lord Bastion accepts your sacrifice...")
                    stdscr.addstr(5, 0, "Press any key to return to main game...")
                    stdscr.refresh()
                    stdscr.getch()

                    gamefile = n_gamefile

                    enemies = {}
                    for grid_num in range(1, 20):
                        enemies[str(grid_num)] = []
                        if random.random() < 0.3:
                            enemy_level = max(1, (grid_num - 1) // 4 + 1)
                            enemy = spawn_enemy_in_grid(gamefile["grids"][str(grid_num)], enemy_level)
                            if enemy:
                                enemies[str(grid_num)].append(enemy)

                    enemies["20"] = []
                    gamefile["enemies"] = serialize_enemies(enemies)

                    grid = gamefile["grids"][grid_id]
                    grid_id = gamefile["curr_grid"]
                    x, y = gamefile["player"]
                    inv = gamefile["inventory"]
                    coins = gamefile["coins"]
                    forge = gamefile["forge"]
                    equipped = gamefile["equipped"]
                    essentials = gamefile["essentials"]
                    mills = gamefile["mills"]
                    player.health = gamefile["health"]
                    atk = gamefile["attack"]
                    enemies = deserialize_enemies(gamefile["enemies"])
                    cl20 = gamefile["clear_20"]
                
                clear_grid = True
            else:
                combat_log = ["No ascension available - defeat final boss first!"]
                clear_grid = True

        elif key == ord('f'):
            if ascension_data["unlocks"]["fast_access"] and forge["state"] == "Discovered":
                inv, coins = start_forge(stdscr, inv, coins)
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
            gamefile["clear_20"] = cl20
            
            # Save ascension data
            ascension_data = save_ascension_data(ascension_data)
            
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
                essentials = [e for e in essentials if e in inv]
                if equipped not in inv:
                    equipped = ""
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
        elif grid[y][x] == "D":
            coins -= 15
            inv["Fuel"] += 1
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
            essentials = [e for e in essentials if e in inv]
            mills[f"mill_{grid_id}_{x}_{y}"] = curr_mill
            curr_mill = None
            clear_grid = True
        elif grid[y][x] == "F":
            x = prevx
            y = prevy
            inv, coins = start_forge(stdscr, inv, coins)
            essentials = [e for e in essentials if e in inv]
            clear_grid = True
        elif grid[y][x] == ">":
            x = prevx
            y = prevy
            if cl20 == 0:
                combat_log = ["Clear zone to proceed"]
            else:
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
                gamefile["clear_20"] = cl20

                with open("grids.json", "w") as f:
                    json.dump(gamefile, f)

                returned_values = start_depths(x,y,stdscr, atk, player.health, coins, inv, equipped, essentials, ascension_data)
                if returned_values:
                    atk, player.health, coins, inv, equipped, essentials, ascension_data = returned_values
                    
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
                # Check proximity to player
                enemy.check_prox(x, y)
                
                # Act based on current status
                if enemy.status == "Alert":
                    enemy.alert(grid, x, y)
                elif enemy.status == "Roam":
                    enemy.roam(grid)

        if enemies[grid_id] == [] and grid_id == "20":
            cl20 = 1

        if moved == True:
            player.health += regen
            if player.health > 300:
                player.health = 300

        update_screen(stdscr, x, y, prevx, prevy, grid, grid_size, grid_id, coins, forge, atk, armor, player.health, enemies[grid_id], cleared=clear_grid, got_item=item, equipped=equipped, combat_log=combat_log, ascension_data=ascension_data)
        if item:
            item = None

curses.wrapper(main)