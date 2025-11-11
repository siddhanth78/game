import json
import random

def generate():
    gjson = dict()
    flag = False
    vendor = None
    for i in range(1, 41):  # Changed from 20 to 40
        grid_size = (random.randint(35, 60), random.randint(15, 30))  # Changed min from 10 to 15
        grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]

        if (random.random() <= 0.2 and flag==False and i != 1) or (i == 15 and flag == False):

            vendor = dict()  # Changed from forge to vendor

            x = random.randint(1, grid_size[0] - 2)  # Avoid borders
            y = random.randint(1, grid_size[1] - 2)

            grid[y][x] = "V"  # Changed from "F" to "V" for vendor
            vendor["gridx"] = -1
            vendor["gridy"] = -1
            vendor["state"] = "Undiscovered"
            vendor["loc"] = str(i)
            flag = True
        
        # Removed trees (T) - no longer adding trees
        
        # Add plus symbols (+) instead of ore (*) - dense in grids 7, 8, 12, 13, 14, sparse elsewhere
        if i in [7, 8, 12, 13, 14]:  # Dense plus grids
            num_plus = random.randint(16, 25)
        else:  # Sparse plus grids
            num_plus = random.randint(3, 5)
        
        for _ in range(num_plus):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                if grid_size[0] <= 2 or grid_size[1] <= 2:  # Safety check
                    break
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = '+'  # Changed from '*' to '+'
                    break
                attempts += 1
        
        # Add more scattered '?' symbols (increased from around 20)
        num_question_marks = random.randint(35, 45)  # Increased from 18-22 to 35-45
        for _ in range(num_question_marks):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
                if grid_size[0] <= 2 or grid_size[1] <= 2:  # Safety check
                    break
                x = random.randint(1, grid_size[0] - 2)  # Avoid borders
                y = random.randint(1, grid_size[1] - 2)  # Avoid borders
                if grid[y][x] == ' ':  # Only place if cell is empty
                    grid[y][x] = '?'
                    break
                attempts += 1

        # Add bunches of 'o' (around 30 total)
        total_o_target = random.randint(28, 32)  # Around 30 o symbols
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
            if min_bunch > max_bunch:  # Safety check
                min_bunch = max_bunch
            bunch_size = random.randint(min_bunch, max_bunch)
            
            # Choose center position (avoiding borders)
            if grid_size[0] <= 4 or grid_size[1] <= 4:  # Safety check for center positioning
                continue
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

        # Add '>' at bottom corner of each grid
        grid[grid_size[1] - 1][grid_size[0] - 1] = '>'
        
        gjson[str(i)] = grid
    
    # Simplified final JSON with only grids, curr_grid, and vendor
    wjson = {"grids": gjson, "curr_grid": "1", "vendor": vendor}
    
    with open("grids.json", "w") as f:
        json.dump(wjson, f, indent=2)
    print("Generated depths")

if __name__ == "__main__":
    generate()