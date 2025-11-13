import generate_grid
import gen_depths
from player_ascension import create_default_ascension
import json

generate_grid.generate(DEV = True)
gen_depths.generate(DEV = True)
asc = create_default_ascension()
with open("ascension.json", "w") as file:
    json.dump(asc, file, indent=2)
