block_ids = {
    1: None,
    2: None
}


class Block:
    transparent = False
    durability = 0
    width = 1

    def __init__(self, x, y, z, texture):
        self.x, self.y, self.z = x, y, z
        self.texture = texture

    def get_open_sides(self): pass

    def get_neighbors(self): pass

    def get_vertices(self):
        x, y, z = self.pos()
        n = self.width
        return [
            x - n, y + n, z - n, x - n, y + n, z + n, x + n, y + n, z + n, x + n, y + n, z - n,  # top
            x - n, y - n, z - n, x + n, y - n, z - n, x + n, y - n, z + n, x - n, y - n, z + n,  # bottom
            x - n, y - n, z - n, x - n, y - n, z + n, x - n, y + n, z + n, x - n, y + n, z - n,  # left
            x + n, y - n, z + n, x + n, y - n, z - n, x + n, y + n, z - n, x + n, y + n, z + n,  # right
            x - n, y - n, z + n, x + n, y - n, z + n, x + n, y + n, z + n, x - n, y + n, z + n,  # front
            x + n, y - n, z - n, x - n, y - n, z - n, x - n, y + n, z - n, x + n, y + n, z - n,  # back
        ]

    def pos(self):
        return self.x, self.y, self.z

class Dirt:
    texture = pass