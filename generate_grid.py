import json
import random

def generate():
    gjson = dict()
    flag = False
    forge = None
    for i in range(1, 21):
        grid_size = (random.randint(10, 50), random.randint(10, 25))
        grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]

        if (random.random() <= 0.2 and flag==False and i != 1) or (i == 15 and flag == False):

            forge = dict()

            x = random.randint(1, grid_size[0] - 2)  # Avoid borders
            y = random.randint(1, grid_size[1] - 2)

            grid[y][x] = "F"
            forge["gridx"] = -1
            forge["gridy"] = -1
            forge["state"] = "Undiscovered"
            forge["loc"] = str(i)
            flag = True
        
        # Add scattered '?' symbols (around 20)
        num_question_marks = random.randint(18, 22)  # Around 20 ? symbols
        for _ in range(num_question_marks):
            attempts = 0
            while attempts < 100:  # Prevent infinite loops
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
        
        gjson[str(i)] = grid
    
    wjson = {"grids": gjson, "curr_grid": "1", "player": [0, 0], "inventory": [["Sword", 1], ["Shield", 1], ["Potion", 1]], "coins": 0, "forge":forge}
    with open("grids.json", "w") as f:
        json.dump(wjson, f, indent=2)
    print("Generated world")

if __name__ == "__main__":
    generate()
