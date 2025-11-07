import json
import random

def generate():
    gjson = dict()
    for i in range(1, 21):
        grid_size = (random.randint(10, 50),random.randint(10, 25))
        grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]

        gjson[str(i)] = grid

    wjson = {"grids":gjson, "curr_grid":"1", "player": [0,0], "inventory": [["Sword",1], ["Shield",1], ["Potion",1]], "coins": 0}

    with open("grids.json", "w") as f:
        json.dump(wjson, f, indent=2)

    print("Generated world")

if __name__ == "__main__":
    generate()
