import json

pl_inv = {}

inv = {"Axe": {}, "Sword": {}, "Shield": {}}
inv_grid = [["." for i in range(50)] for j in range(25)]

pl_inv["inventory_grid"] = inv_grid
pl_inv["inventory"] = inv
with open("player_inv.json", "w") as file:
    json.dump(pl_inv, file, indent=2)

art = {
    "Sword":
    ["  /\\  ",
     " /  \\ ",
     " |  | ",
     " |  | ",
     "------",
     "  ||  ",
     "  --  "],

    "Shield":
    ["/-----\\",
     "\\     /",
     " \\___/ "],

    "Axe":
    [" /|\\___/|\\ ",
     "| |     | |",
     " \\|/---\\|/ ",
     "    | |    ",
     "    | |    ",
     "    |_|    "],

     "Pickaxe":
    [" ______ ",
     "/  ||  \\",
     "   ||   ",
     "   ||   "]
}

with open("item_art.json", "w") as file_:
    json.dump(art, file_, indent=2)