class Enemy():

    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.status = "Roam"
        self.prevx = -1
        self.prevy = -1
        self.level = level
        self.attack = level*5
        self.health = level*30
    
    def received_damage(self, dam):
        self.health -= dam
        if self.health <= 0:
            self.status = "Dead"