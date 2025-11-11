import random
from collections import deque
from typing import List, Tuple, Optional

class Enemy:
    def __init__(self, x, y, level):
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
    
    def received_damage(self, dam):
        self.health -= dam
        if self.health <= 0:
            self.status = "Dead"
            return True  # Enemy died
        return False  # Enemy survived

    def check_prox(self, px, py):
        """Check if player is within 3 spaces and update status"""
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
        
        # Enemy can walk on empty spaces, eat 'o' and '?', but blocked by obstacles
        # Obstacles: F, D, M, m, *, T
        obstacles = {'F', 'D', 'M', 'm', '*', 'T'}
        
        return cell not in obstacles

    def can_eat(self, grid: List[List[str]], x: int, y: int) -> bool:
        """Check if enemy can eat what's at this position"""
        if not (0 <= y < len(grid) and 0 <= x < len(grid[0])):
            return False
        
        cell = grid[y][x]
        return cell in {'o', '?'}

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
        self.chase_moves += 1
        
        # After max chase moves, go back to roam
        if self.chase_moves >= self.max_chase_moves:
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
        return {
            "position": (self.x, self.y),
            "status": self.status,
            "health": f"{self.health}/{self.max_health}",
            "level": self.level,
            "attack": self.attack,
            "chase_moves": self.chase_moves,
            "has_path": len(self.path) > 0
        }
    
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
    """
    Handle collision when player walks into enemy position.
    Player damages enemy first, then enemy retaliates if alive.
    
    Args:
        player: Player object with health attribute
        enemy: Enemy object
        player_damage: Damage player deals to enemy
        player_armor: Player's armor value
    
    Returns:
        dict with combat results
    """
    combat_log = []
    
    # Player attacks first
    enemy_died = enemy.received_damage(player_damage)
    combat_log.append(f"You hit the enemy for {player_damage} damage!")
    
    if enemy_died:
        combat_log.append(f"Enemy defeated! (+{enemy.level * 10} coins)")
        return {
            "enemy_died": True,
            "player_damage_taken": 0,
            "coins_gained": enemy.level * 10,
            "log": combat_log
        }
    else:
        # Enemy retaliates immediately - apply armor reduction
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
            "log": combat_log
        }
        
def check_enemy_collisions(enemies: List[Enemy], player_x: int, player_y: int, player_damage: int, player, player_armor: int = 0) -> dict:
    """
    Check if player is on same position as any enemy and handle combat.
    """
    for i, enemy in enumerate(enemies[:]):
        if enemy.x == player_x and enemy.y == player_y and enemy.status != "Dead":
            result = handle_player_enemy_collision(player, enemy, player_damage, player_armor)
            
            if result["enemy_died"]:
                enemies.remove(enemy)
            
            result["enemy_index"] = i
            return result
    
    return {"collision": False}

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

def update_enemies(enemies: List[Enemy], grid: List[List[str]], player_x: int, player_y: int):
    """Update all enemies in the current grid"""
    for enemy in enemies[:]:  # Use slice to avoid modification during iteration
        if enemy.status == "Dead":
            enemies.remove(enemy)
        else:
            enemy.update(grid, player_x, player_y)