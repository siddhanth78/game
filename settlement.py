import random
from collections import deque
from typing import List, Tuple, Optional, Dict, Any

class House:
    def __init__(self, x: int, y: int, grid_id: str):
        self.x = x
        self.y = y
        self.grid_id = grid_id
        self.settlers = []  # List of settler IDs that belong to this house
        self.max_settlers = 2
    
    def can_add_settler(self):
        return len(self.settlers) < self.max_settlers
    
    def add_settler(self, settler_id):
        if self.can_add_settler():
            self.settlers.append(settler_id)
            return True
        return False

class Settler:
    def __init__(self, x: int, y: int, grid_id: str, house_id: str, settler_id: str, is_vendor: bool = False):
        self.x = x
        self.y = y
        self.grid_id = grid_id
        self.house_id = house_id
        self.settler_id = settler_id
        self.is_vendor = is_vendor
        self.state = "sleep"  # sleep, awake, roam, returning
        self.turns_in_state = 0
        self.home_x = x
        self.home_y = y
        self.home_grid = grid_id
        self.path = []
        self.path_index = 0
        self.group_id = None
        self.is_group_leader = False
        self.group_turns_remaining = 0
        self.roam_target = None
        
        # Dialogue options
        self.greetings = [
            "Hello friend!",
            "Good day to you!",
            "Greetings, brother!",
            "Nice weather we're having!",
            "How are you doing?",
            "Safe travels!",
            "Lovely day, isn't it?",
            "Hope you're well!",
            "Good to see you!",
            "May fortune favor you!"
        ]
    
    def get_symbol(self):
        if self.is_vendor:
            return 'V'
        else:
            return 's'
    
    def update_state(self):
        """Update settler state based on turn count and conditions"""
        self.turns_in_state += 1
        
        if self.state == "sleep" and self.turns_in_state >= 100:
            self.state = "awake"
            self.turns_in_state = 0
        elif self.state == "awake":
            self.state = "roam"
            self.turns_in_state = 0
        elif self.state == "roam" and self.turns_in_state >= 800:
            self.state = "returning"
            self.turns_in_state = 0
        elif self.state == "returning" and self.x == self.home_x and self.y == self.home_y and self.grid_id == self.home_grid:
            self.state = "sleep"
            self.turns_in_state = 0
    
    def is_walkable(self, grid: List[List[str]], x: int, y: int) -> bool:
        """Check if position is walkable for settler"""
        rows, cols = len(grid), len(grid[0])
        
        if not (0 <= y < rows and 0 <= x < cols):
            return False
        
        cell = grid[y][x]
        obstacles = {'F', 'D', 'M', 'm', '*', 'T'}
        return cell not in obstacles
    
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
                        path = []
                        current = goal
                        while current is not None:
                            path.append(current)
                            current = parent[current]
                        return path[::-1]
        
        return []
    
    def get_random_roam_position(self, grid: List[List[str]]) -> Tuple[int, int]:
        """Get random position for roaming"""
        rows, cols = len(grid), len(grid[0])
        attempts = 0
        
        while attempts < 50:
            x = random.randint(1, cols - 2)
            y = random.randint(1, rows - 2)
            
            if self.is_walkable(grid, x, y):
                return (x, y)
            
            attempts += 1
        
        return (self.x, self.y)
    
    def move_along_path(self, grid: List[List[str]], player_x: int = None, player_y: int = None):
        """Move one step along current path"""
        if not self.path or self.path_index >= len(self.path):
            return False
        
        target_x, target_y = self.path[self.path_index]
        
        if not self.is_walkable(grid, target_x, target_y):
            self.path = []
            return False
        
        # Don't move if target position is occupied by player
        if player_x is not None and player_y is not None:
            if target_x == player_x and target_y == player_y:
                return False  # Blocked by player
        
        self.x = target_x
        self.y = target_y
        self.path_index += 1
        
        return True
    
    def handle_grid_edge_movement(self, gamefile: Dict, all_settlers: Dict):
        """Handle movement to adjacent grids"""
        current_grid = gamefile["grids"][self.grid_id]
        rows, cols = len(current_grid), len(current_grid[0])
        
        new_grid_id = None
        new_x, new_y = self.x, self.y
        
        # Check grid boundaries for 3x3 layout (grids 1-9)
        if self.x <= 0 and int(self.grid_id) % 3 != 1:  # Left edge, not leftmost column
            new_grid_id = str(int(self.grid_id) - 1)
            new_x = len(gamefile["grids"][new_grid_id][0]) - 2
        elif self.x >= cols - 1 and int(self.grid_id) % 3 != 0:  # Right edge, not rightmost column
            new_grid_id = str(int(self.grid_id) + 1)
            new_x = 1
        elif self.y <= 0 and int(self.grid_id) not in [1, 2, 3]:  # Top edge, not top row
            new_grid_id = str(int(self.grid_id) - 3)
            new_y = len(gamefile["grids"][new_grid_id]) - 2
        elif self.y >= rows - 1 and int(self.grid_id) not in [7, 8, 9]:  # Bottom edge, not bottom row
            new_grid_id = str(int(self.grid_id) + 3)
            new_y = 1
        
        # Check if new grid exists (1-9 range)
        if new_grid_id and 1 <= int(new_grid_id) <= 9:
            self.grid_id = new_grid_id
            self.x = new_x
            self.y = new_y
            return True
        
        return False

def check_for_grouping(settler: Settler, all_settlers: Dict) -> bool:
    """Check if settler should join or form a group"""
    if settler.group_id is not None:
        return False  # Already in a group
    
    if random.random() > 0.05:  # 5% chance per turn
        return False
    
    # Look for nearby settlers
    for other_settler in all_settlers.values():
        if (other_settler.settler_id != settler.settler_id and
            other_settler.grid_id == settler.grid_id and
            other_settler.group_id is None and
            abs(other_settler.x - settler.x) + abs(other_settler.y - settler.y) <= 3):
            
            # Form a group
            group_id = f"group_{settler.settler_id}_{other_settler.settler_id}"
            settler.group_id = group_id
            settler.is_group_leader = True
            settler.group_turns_remaining = 10
            
            other_settler.group_id = group_id
            other_settler.is_group_leader = False
            other_settler.group_turns_remaining = 10
            
            return True
    
    return False

def update_settler_group(settler: Settler, all_settlers: Dict):
    """Update group behavior"""
    if settler.group_id is None:
        return
    
    settler.group_turns_remaining -= 1
    
    if settler.group_turns_remaining <= 0:
        # Break from group
        group_id = settler.group_id
        settler.group_id = None
        settler.is_group_leader = False
        
        # Break other group members too
        for other_settler in all_settlers.values():
            if other_settler.group_id == group_id:
                other_settler.group_id = None
                other_settler.is_group_leader = False

def move_settler_in_group(settler: Settler, grid: List[List[str]], all_settlers: Dict, player_x: int = None, player_y: int = None):
    """Handle movement for grouped settlers"""
    if settler.is_group_leader:
        # Leader moves normally
        if not settler.path or settler.path_index >= len(settler.path):
            settler.roam_target = settler.get_random_roam_position(grid)
            settler.path = settler.bfs_path(grid, settler.roam_target[0], settler.roam_target[1])
            settler.path_index = 1 if len(settler.path) > 1 else 0
        
        if random.random() < 0.7:
            settler.move_along_path(grid, player_x, player_y)
    else:
        # Follower tries to stay close to leader
        leader = None
        for other_settler in all_settlers.values():
            if (other_settler.group_id == settler.group_id and 
                other_settler.is_group_leader):
                leader = other_settler
                break
        
        if leader:
            # Move toward leader if too far
            distance = abs(leader.x - settler.x) + abs(leader.y - settler.y)
            if distance > 2:
                settler.path = settler.bfs_path(grid, leader.x, leader.y)
                settler.path_index = 1 if len(settler.path) > 1 else 0
                if random.random() < 0.8:
                    settler.move_along_path(grid, player_x, player_y)

def handle_settler_interaction(settler: Settler, player_x: int, player_y: int) -> Dict:
    """Handle interaction when player collides with settler"""
    if settler.state == "sleep":
        return {"interaction": False}
    
    if settler.x != player_x or settler.y != player_y:
        return {"interaction": False}
    
    result = {"interaction": True, "log": []}
    
    # Random dialogue
    greeting = random.choice(settler.greetings)
    result["log"].append(f"Settler: \"{greeting}\"")
    
    # Chance for gift
    if random.random() < 0.10:  # 10% chance
        gift_items = ["Tree Starter", "Ore Starter"]
        gift_item = random.choice(gift_items)
        gift_amount = random.randint(1, 3)
        
        result["log"].append(f"Settler: \"A gift for you!\"")
        result["gift"] = {"item": gift_item, "amount": gift_amount}
    
    # Vendor interaction
    if settler.is_vendor:
        result["open_vendor"] = True
        result["vendor_id"] = settler.settler_id
    
    return result

def update_settler(settler: Settler, grid: List[List[str]], gamefile: Dict, all_settlers: Dict, player_x: int = None, player_y: int = None):
    """Update individual settler AI"""
    settler.update_state()
    
    if settler.state == "sleep":
        return
    
    elif settler.state == "awake":
        # Just changed to awake, will move to roam next turn
        return
    
    elif settler.state == "roam":
        # Handle grouping
        if settler.group_id is None:
            check_for_grouping(settler, all_settlers)
        else:
            update_settler_group(settler, all_settlers)
        
        # Move based on group status
        if settler.group_id is not None:
            move_settler_in_group(settler, grid, all_settlers, player_x, player_y)
        else:
            # Solo roaming
            if not settler.path or settler.path_index >= len(settler.path):
                settler.roam_target = settler.get_random_roam_position(grid)
                settler.path = settler.bfs_path(grid, settler.roam_target[0], settler.roam_target[1])
                settler.path_index = 1 if len(settler.path) > 1 else 0
            
            if random.random() < 0.7:
                if not settler.move_along_path(grid, player_x, player_y):
                    # Try to move to adjacent grid if at edge and not blocked by player
                    if settler.x <= 0 or settler.x >= len(grid[0]) - 1 or settler.y <= 0 or settler.y >= len(grid) - 1:
                        settler.handle_grid_edge_movement(gamefile, all_settlers)
    
    elif settler.state == "returning":
        # Navigate back to home
        if (settler.grid_id != settler.home_grid or 
            not settler.path or settler.path_index >= len(settler.path)):
            
            # Need to pathfind to home (possibly across grids)
            if settler.grid_id == settler.home_grid:
                settler.path = settler.bfs_path(grid, settler.home_x, settler.home_y)
                settler.path_index = 1 if len(settler.path) > 1 else 0
            else:
                # Move toward home grid first
                settler.handle_grid_edge_movement(gamefile, all_settlers)
        else:
            settler.move_along_path(grid, player_x, player_y)

def spawn_house(grid: List[List[str]], grid_id: str) -> Optional[House]:
    """Spawn a house in a random valid location"""
    rows, cols = len(grid), len(grid[0])
    attempts = 0
    
    while attempts < 100:
        x = random.randint(1, cols - 2)
        y = random.randint(1, rows - 2)
        
        if grid[y][x] == ' ':
            grid[y][x] = 'H'
            return House(x, y, grid_id)
        
        attempts += 1
    
    return None

def create_settler(house: House, settler_count: int) -> Settler:
    """Create a new settler for a house"""
    settler_id = f"settler_{house.grid_id}_{house.x}_{house.y}_{settler_count}"
    is_vendor = (settler_count % 10 == 0)  # Every 10th settler is a vendor
    
    return Settler(house.x, house.y, house.grid_id, f"house_{house.grid_id}_{house.x}_{house.y}", 
                  settler_id, is_vendor)

def initialize_settlement_system(gamefile: Dict) -> Tuple[Dict[str, List[House]], Dict[str, Settler]]:
    """Initialize houses and settlers for all grids"""
    houses = {}
    settlers = {}
    settler_count = 0
    
    for grid_id in [str(i) for i in range(1, 10)]:  # Changed from 1-21 to 1-9
        houses[grid_id] = []
        grid = gamefile["grids"][grid_id]
        
        # 20% chance to spawn 1-3 houses per grid
        if random.random() < 0.20:
            num_houses = random.randint(1, min(3, 25))  # Max 25 houses total
            
            for _ in range(num_houses):
                house = spawn_house(grid, grid_id)
                if house:
                    houses[grid_id].append(house)
                    
                    # Create 1-2 settlers per house
                    for _ in range(2):
                        if len(settlers) < 30:
                            settler = create_settler(house, settler_count)
                            settlers[settler.settler_id] = settler
                            house.add_settler(settler.settler_id)
                            settler_count += 1
    
    return houses, settlers

def check_settler_interactions(settlers: Dict[str, Settler], grid_id: str, player_x: int, player_y: int) -> Dict:
    """Check for interactions with settlers in current grid"""
    for settler in settlers.values():
        if settler.grid_id == grid_id:
            result = handle_settler_interaction(settler, player_x, player_y)
            if result["interaction"]:
                return result
    
    return {"interaction": False}

def update_all_settlers(settlers: Dict[str, Settler], gamefile: Dict, player_x: int = None, player_y: int = None, current_grid_id: str = None):
    """Update all settlers across all grids"""
    for settler in settlers.values():
        current_grid = gamefile["grids"][settler.grid_id]
        # Only pass player position if settler is in same grid as player
        settler_player_x = player_x if settler.grid_id == current_grid_id else None
        settler_player_y = player_y if settler.grid_id == current_grid_id else None
        update_settler(settler, current_grid, gamefile, settlers, settler_player_x, settler_player_y)

def serialize_settlement_data(houses: Dict, settlers: Dict) -> Dict:
    """Serialize settlement data for saving"""
    serialized = {
        "houses": {},
        "settlers": {}
    }
    
    for grid_id, house_list in houses.items():
        serialized["houses"][grid_id] = []
        for house in house_list:
            serialized["houses"][grid_id].append({
                "x": house.x,
                "y": house.y,
                "grid_id": house.grid_id,
                "settlers": house.settlers
            })
    
    for settler_id, settler in settlers.items():
        serialized["settlers"][settler_id] = {
            "x": settler.x,
            "y": settler.y,
            "grid_id": settler.grid_id,
            "house_id": settler.house_id,
            "is_vendor": settler.is_vendor,
            "state": settler.state,
            "turns_in_state": settler.turns_in_state,
            "home_x": settler.home_x,
            "home_y": settler.home_y,
            "home_grid": settler.home_grid,
            "group_id": settler.group_id,
            "is_group_leader": settler.is_group_leader,
            "group_turns_remaining": settler.group_turns_remaining
        }
    
    return serialized

def deserialize_settlement_data(serialized: Dict) -> Tuple[Dict, Dict]:
    """Deserialize settlement data from save file"""
    houses = {}
    settlers = {}
    
    # Initialize empty lists for all grids (1-9 for settlement world)
    for grid_id in [str(i) for i in range(1, 10)]:
        houses[grid_id] = []
    
    if "houses" in serialized:
        for grid_id, house_list in serialized["houses"].items():
            for house_data in house_list:
                house = House(house_data["x"], house_data["y"], house_data["grid_id"])
                house.settlers = house_data["settlers"]
                houses[grid_id].append(house)
    
    if "settlers" in serialized:
        for settler_id, settler_data in serialized["settlers"].items():
            settler = Settler(
                settler_data["x"], settler_data["y"], settler_data["grid_id"],
                settler_data["house_id"], settler_id, settler_data["is_vendor"]
            )
            settler.state = settler_data["state"]
            settler.turns_in_state = settler_data["turns_in_state"]
            settler.home_x = settler_data["home_x"]
            settler.home_y = settler_data["home_y"]
            settler.home_grid = settler_data["home_grid"]
            settler.group_id = settler_data.get("group_id")
            settler.is_group_leader = settler_data.get("is_group_leader", False)
            settler.group_turns_remaining = settler_data.get("group_turns_remaining", 0)
            
            settlers[settler_id] = settler
    
    return houses, settlers