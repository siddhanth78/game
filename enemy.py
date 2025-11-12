import random
from collections import deque
from typing import List, Tuple, Optional

class Enemy:
    def __init__(self, x, y, level, is_final_boss=False):
        self.x = x
        self.y = y
        self.status = "Roam"
        self.prevx = -1
        self.prevy = -1
        self.level = level
        self.attack = level * 5
        self.health = level * 30
        self.max_health = level * 30
        self.chase_moves = 0
        self.max_chase_moves = 10
        self.path = []
        self.path_index = 0
        self.roam_target = None
        
        # Boss-specific attributes
        self.is_final_boss = is_final_boss
        if is_final_boss:
            self.boss_mode = "alert"  # alert, shell, rest
            self.mode_timer = 0
            self.mode_duration = 2
            self.symbol = "@"
        else:
            self.symbol = "E"
    
    def update_boss_mode(self):
        """Update boss mode cycling for final boss"""
        if not self.is_final_boss:
            return []
        
        self.mode_timer += 1
        messages = []
        
        if self.mode_timer >= self.mode_duration:
            self.mode_timer = 0
            # Cycle through modes: alert -> shell -> rest -> alert
            if self.boss_mode == "alert":
                self.boss_mode = "shell"
                self.mode_duration = 10
                messages.append("Boss enters SHELL mode! (Damage immunity)")
            elif self.boss_mode == "shell":
                self.boss_mode = "rest"
                self.mode_duration = 2
                messages.append("Boss enters REST mode! (2x damage vulnerability)")
            elif self.boss_mode == "rest":
                self.boss_mode = "alert"
                self.mode_duration = 8
                messages.append("Boss enters ALERT mode! (Normal behavior)")
        
        return messages

    def received_damage(self, dam):
        if self.is_final_boss and self.boss_mode == "shell":
            # Shell mode: no damage taken
            return False
        elif self.is_final_boss and self.boss_mode == "rest":
            # Rest mode: double damage
            self.health -= dam * 2
        else:
            # Normal damage
            self.health -= dam
        
        if self.health <= 0:
            self.status = "Dead"
            return True  # Enemy died
        return False  # Enemy survived

    def get_boss_mode_info(self):
        """Get current boss mode information"""
        if not self.is_final_boss:
            return ""
        
        mode_descriptions = {
            "alert": "ALERT - Normal behavior",
            "shell": "SHELL - Immune to damage", 
            "rest": "REST - Takes 2x damage"
        }
        
        remaining_moves = self.mode_duration - self.mode_timer
        return f"Boss Mode: {mode_descriptions[self.boss_mode]} ({remaining_moves} moves left)"

    def check_prox(self, px, py):
        """Check if player is within 3 spaces and update status"""
        if self.is_final_boss:
            # Boss always knows where player is when not in shell/rest mode
            if self.boss_mode == "alert":
                self.status = "Alert"
                self.chase_moves = 0
                self.path = []
            elif self.boss_mode in ["shell", "rest"]:
                # In shell/rest mode, boss doesn't move toward player
                self.status = "Roam"
                self.path = []
            return
        
        # Normal enemy proximity check
        distance = abs(px - self.x) + abs(py - self.y)  # Manhattan distance
        if distance <= 3:
            if self.status != "Alert":
                self.status = "Alert"
                self.chase_moves = 0
                self.path = []  # Clear any existing path
        else:
            if self.status == "Alert":
                self.status = "Roam"
                self.chase_moves = 0
                self.path = []

    def is_walkable(self, grid: List[List[str]], x: int, y: int) -> bool:
        """Check if enemy can move to this position"""
        rows, cols = len(grid), len(grid[0])
        
        # Check bounds
        if not (0 <= y < rows and 0 <= x < cols):
            return False
        
        cell = grid[y][x]
        
        # Enemy can walk on empty spaces, eat 'o' and '?' and '+', but blocked by obstacles
        # Obstacles: F, D, M, m, *, T, V
        obstacles = {'F', 'D', 'M', 'm', '*', 'T', 'V'}
        
        return cell not in obstacles

    def can_eat(self, grid: List[List[str]], x: int, y: int) -> bool:
        """Check if enemy can eat what's at this position"""
        if not (0 <= y < len(grid) and 0 <= x < len(grid[0])):
            return False
        
        cell = grid[y][x]
        return cell in {'o', '?', '+'}

    def bfs_path(self, grid: List[List[str]], target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Find shortest path to target using BFS"""
        if not self.is_walkable(grid, target_x, target_y):
            return []
        
        start = (self.x, self.y)
        goal = (target_x, target_y)
        
        if start == goal:
            return [start]
        
        rows, cols = len(grid), len(grid[0])
        queue = deque([start])
        visited = {start}
        parent = {start: None}
        
        # Directions: up, down, left, right
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            current_x, current_y = queue.popleft()
            
            for dx, dy in directions:
                next_x, next_y = current_x + dx, current_y + dy
                next_pos = (next_x, next_y)
                
                if (0 <= next_x < cols and 0 <= next_y < rows and 
                    self.is_walkable(grid, next_x, next_y) and 
                    next_pos not in visited):
                    
                    visited.add(next_pos)
                    parent[next_pos] = (current_x, current_y)
                    queue.append(next_pos)
                    
                    if next_pos == goal:
                        # Reconstruct path
                        path = []
                        current = goal
                        while current is not None:
                            path.append(current)
                            current = parent[current]
                        return path[::-1]  # Reverse to get start -> goal
        
        return []  # No path found

    def get_random_walkable_position(self, grid: List[List[str]]) -> Tuple[int, int]:
        """Find a random walkable position for roaming"""
        rows, cols = len(grid), len(grid[0])
        attempts = 0
        
        while attempts < 50:
            x = random.randint(1, cols - 2)
            y = random.randint(1, rows - 2)
            
            if self.is_walkable(grid, x, y):
                return (x, y)
            
            attempts += 1
        
        # Fallback: return current position
        return (self.x, self.y)

    def move_towards_target(self, grid: List[List[str]], player_x: int = None, player_y: int = None):
        """Move one step along the current path"""
        if not self.path or self.path_index >= len(self.path):
            return False
        
        target_x, target_y = self.path[self.path_index]
        
        # Check if target position is still walkable
        if not self.is_walkable(grid, target_x, target_y):
            self.path = []  # Clear invalid path
            return False
        
        # Don't move if target position is occupied by player
        if player_x is not None and player_y is not None:
            if target_x == player_x and target_y == player_y:
                return False  # Can't move into player position
        
        # Store previous position
        self.prevx = self.x
        self.prevy = self.y
        
        # Check if we can eat at the new position
        if self.can_eat(grid, target_x, target_y):
            grid[target_y][target_x] = ' '  # Eat the item
        
        # Move to new position
        self.x = target_x
        self.y = target_y
        self.path_index += 1
        
        return True

    def alert(self, grid: List[List[str]], player_x: int, player_y: int):
        """Handle alert/chase behavior"""
        if self.is_final_boss and self.boss_mode in ["shell", "rest"]:
            # Boss doesn't move in shell/rest modes
            return
        
        self.chase_moves += 1
        
        # After max chase moves, go back to roam (only for normal enemies)
        if not self.is_final_boss and self.chase_moves >= self.max_chase_moves:
            self.status = "Roam"
            self.chase_moves = 0
            self.path = []
            return
        
        # If no path or reached end of path, calculate new path to player
        if not self.path or self.path_index >= len(self.path):
            self.path = self.bfs_path(grid, player_x, player_y)
            self.path_index = 1 if len(self.path) > 1 else 0  # Skip current position
        
        # Move towards player
        if self.path and self.path_index < len(self.path):
            self.move_towards_target(grid, player_x, player_y)  # Pass player position

    def roam(self, grid: List[List[str]]):
        """Handle roaming behavior"""
        if self.is_final_boss:
            # Boss doesn't roam, just stays in place during shell/rest modes
            return
        
        # If no roam target or reached target, pick new one
        if (self.roam_target is None or 
            (self.x, self.y) == self.roam_target or
            not self.path or self.path_index >= len(self.path)):
            
            self.roam_target = self.get_random_walkable_position(grid)
            self.path = self.bfs_path(grid, self.roam_target[0], self.roam_target[1])
            self.path_index = 1 if len(self.path) > 1 else 0
        
        # Move towards roam target
        if self.path and self.path_index < len(self.path):
            # 70% chance to actually move (makes roaming less predictable)
            if random.random() < 0.7:
                self.move_towards_target(grid)  # No player position needed for roaming

    def get_info(self) -> dict:
        """Get enemy info for debugging/display"""
        info = {
            "position": (self.x, self.y),
            "status": self.status,
            "health": f"{self.health}/{self.max_health}",
            "level": self.level,
            "attack": self.attack,
            "chase_moves": self.chase_moves,
            "has_path": len(self.path) > 0,
            "symbol": self.symbol
        }
        
        if self.is_final_boss:
            info["boss_mode"] = self.boss_mode
            info["mode_timer"] = f"{self.mode_timer}/{self.mode_duration}"
        
        return info
    
def check_adjacent_enemy_attack(enemies: List[Enemy], player_x: int, player_y: int, player_damage: int, player, player_armor: int = 0) -> dict:
    """Check for adjacent enemies and attack them"""
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right
    
    for dx, dy in directions:
        check_x, check_y = player_x + dx, player_y + dy
        
        for enemy in enemies[:]:
            if (enemy.x == check_x and enemy.y == check_y and 
                enemy.status != "Dead"):
                
                # Attack this adjacent enemy
                result = handle_player_enemy_collision(player, enemy, player_damage, player_armor)
                result["collision"] = True
                
                if result["enemy_died"]:
                    enemies.remove(enemy)
                return result
    
    return {"collision": False}

def handle_player_enemy_collision(player, enemy, player_damage: int, player_armor: int = 0) -> dict:
    """Handle combat between player and enemy"""
    combat_log = []
    
    # Add boss mode info to combat log
    if enemy.is_final_boss:
        mode_info = enemy.get_boss_mode_info()
        combat_log.append(mode_info)
    
    # Player attacks first
    if enemy.is_final_boss and enemy.boss_mode == "shell":
        combat_log.append(f"Attack blocked by shell! No damage dealt.")
        enemy_died = False
    elif enemy.is_final_boss and enemy.boss_mode == "rest":
        actual_damage = player_damage * 2
        enemy_died = enemy.received_damage(player_damage)
        combat_log.append(f"Critical hit! {actual_damage} damage dealt!")
    else:
        enemy_died = enemy.received_damage(player_damage)
        combat_log.append(f"You hit the enemy for {player_damage} damage!")
    
    if enemy_died:
        if enemy.is_final_boss:
            combat_log.append("FINAL BOSS DEFEATED! You can now ascend!")
            return {
                "enemy_died": True,
                "player_damage_taken": 0,
                "coins_gained": enemy.level * 10,
                "log": combat_log,
                "boss_defeated": True
            }
        else:
            combat_log.append(f"Enemy defeated! (+{enemy.level * 10} coins)")
            return {
                "enemy_died": True,
                "player_damage_taken": 0,
                "coins_gained": enemy.level * 10,
                "log": combat_log,
                "boss_defeated": False
            }
    else:
        # Enemy retaliates immediately (except in shell/rest modes for boss)
        if enemy.is_final_boss and enemy.boss_mode in ["shell", "rest"]:
            combat_log.append("Boss does not retaliate in this mode!")
            return {
                "enemy_died": False,
                "player_damage_taken": 0,
                "player_died": False,
                "coins_gained": 0,
                "log": combat_log,
                "boss_defeated": False
            }
        else:
            # Normal retaliation - apply armor reduction
            raw_damage = enemy.attack
            actual_damage = max(0, raw_damage - player_armor)
            
            player.health -= actual_damage
            
            if actual_damage == 0:
                combat_log.append(f"Enemy attack blocked by armor! ({raw_damage} damage blocked)")
            else:
                combat_log.append(f"Enemy strikes back for {actual_damage} damage! ({player_armor} blocked by armor)")
            
            player_died = player.health <= 0
            if player_died:
                combat_log.append("You have been defeated!")
            
            return {
                "enemy_died": False,
                "player_damage_taken": actual_damage,
                "player_died": player_died,
                "coins_gained": 0,
                "log": combat_log,
                "boss_defeated": False
            }

# Example usage functions
def spawn_enemy_in_grid(grid: List[List[str]], level: int = 1) -> Optional[Enemy]:
    """Spawn an enemy in a random walkable location"""
    rows, cols = len(grid), len(grid[0])
    attempts = 0
    
    while attempts < 100:
        x = random.randint(1, cols - 2)
        y = random.randint(1, rows - 2)
        
        if grid[y][x] == ' ':  # Empty space
            return Enemy(x, y, level)
        
        attempts += 1
    
    return None

def spawn_final_boss(grid: List[List[str]], level: int = 40) -> Optional[Enemy]:
    """Spawn the final boss at depth 40"""
    rows, cols = len(grid), len(grid[0])
    
    # Try to spawn boss in center of grid
    center_x, center_y = cols // 2, rows // 2
    
    if grid[center_y][center_x] in [' ', 'o', '?', '+']:
        return Enemy(center_x, center_y, level, is_final_boss=True)
    
    # If center is blocked, find nearby empty space
    attempts = 0
    while attempts < 50:
        x = random.randint(max(1, center_x - 3), min(cols - 2, center_x + 3))
        y = random.randint(max(1, center_y - 3), min(rows - 2, center_y + 3))
        
        if grid[y][x] in [' ', 'o', '?']:
            return Enemy(x, y, level, is_final_boss=True)
        
        attempts += 1
    
    return None

def update_enemies(enemies: List[Enemy], grid: List[List[str]], player_x: int, player_y: int):
    """Update all enemies in the current grid"""
    mode_messages = []
    
    for enemy in enemies[:]:  # Use slice to avoid modification during iteration
        if enemy.status == "Dead":
            enemies.remove(enemy)
        else:
            # Update boss modes and get any mode change messages
            if enemy.is_final_boss:
                messages = enemy.update_boss_mode()
                mode_messages.extend(messages)
            
            # Check proximity to player
            enemy.check_prox(player_x, player_y)
            
            # Act based on current status
            if enemy.status == "Alert":
                enemy.alert(grid, player_x, player_y)
            elif enemy.status == "Roam":
                enemy.roam(grid)
    
    return mode_messages