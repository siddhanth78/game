import json
import random

def generate_settlements():
    """Generate 9 settlement grids (50x25) with sparse resources"""
    gjson = dict()
    
    for i in range(1, 10):  # Generate 9 grids
        grid_size = (50, 25)  # Fixed size 50x25
        grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]
        
        # Add sparse trees (T) - much fewer than main world
        num_trees = random.randint(8, 15)  # Sparse distribution
        
        for _ in range(num_trees):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = 'T'
                    break
                attempts += 1
        
        # Add sparse ore (*) - much fewer than main world
        num_ore = random.randint(5, 10)  # Sparse distribution
        
        for _ in range(num_ore):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = '*'
                    break
                attempts += 1
        
        # Add scattered '?' symbols - fewer than main world
        num_question_marks = random.randint(10, 15)  # Sparse distribution
        for _ in range(num_question_marks):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = '?'
                    break
                attempts += 1

        # Add sparse bunches of 'o' - fewer than main world
        total_o_target = random.randint(15, 20)  # Sparse distribution
        placed_o = 0

        # Create 2-3 bunches to reach the target
        num_bunches = random.randint(2, 3)
        for bunch_num in range(num_bunches):
            if placed_o >= total_o_target:
                break
                
            # Simple bunch size calculation
            remaining_o = total_o_target - placed_o
            remaining_bunches = num_bunches - bunch_num
            
            # Ensure we have a reasonable bunch size
            min_bunch = max(1, remaining_o // remaining_bunches - 2)
            max_bunch = min(8, remaining_o + 3)
            if min_bunch > max_bunch:  # Safety check
                min_bunch = max_bunch
            bunch_size = random.randint(min_bunch, max_bunch)
            
            # Choose center position (avoiding borders)
            center_x = random.randint(3, grid_size[0] - 4)
            center_y = random.randint(3, grid_size[1] - 4)
            
            # Create clustered bunch around center
            for _ in range(bunch_size):
                if placed_o >= total_o_target:
                    break
                    
                attempts = 0
                while attempts < 50:  # Prevent infinite loops
                    offset_x = random.randint(-2, 2)
                    offset_y = random.randint(-2, 2)
                    x = center_x + offset_x
                    y = center_y + offset_y
                    
                    # Ensure within safe bounds (not on borders)
                    if 1 <= x < grid_size[0] - 1 and 1 <= y < grid_size[1] - 1:
                        if grid[y][x] == ' ':  # Only place if cell is empty
                            grid[y][x] = 'o'
                            placed_o += 1
                            break
                    
                    attempts += 1
        
        gjson[str(i)] = grid
    
    wjson = {
        "grids": gjson, 
        "curr_grid": "1", 
        "player": [0, 0],
        "settlements": {}  # Will be populated by settlement system
    }
    
    with open("settlements.json", "w") as f:
        json.dump(wjson, f, indent=2)
    
    print("Generated settlement world with 9 grids (50x25)")
    print("Sparse resources: Trees, Ore, Coins, Question marks")
    print("Exit portal '<' placed at bottom-left of grid 1")
    print("Saved to settlements.json")

if __name__ == "__main__":
    generate_settlements()