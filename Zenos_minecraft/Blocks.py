from Zenos_package import *
from noise import pnoise2
from random import random


def get_coords(row, col):
    row = 16 - row
    col -= 1
    step = 16 / 256
    x = col / 16
    y = row / 16
    return x, y, step, step


class MinecraftBlock(ThreeD.Cube):
    _vertex_type_base = "v3f/static"
    texture_path = "/Users/22staples/PycharmProjects/Minecraft/lots_of_textures.png"
    ids = {}
    id = bytes(0)
    base_texture = GREEN
    transparent = False

    def __init__(self, x, y, z):

        self.minecraft_pos = x, y, z
        super(MinecraftBlock, self).__init__((x + 0.5, y + 0.5, z + 0.5), 1, self.base_texture)

    def __init_subclass__(cls, **kwargs):
        super(MinecraftBlock, cls).__init_subclass__()
        cls.ids[cls.id] = cls


class Dirt(MinecraftBlock):
    id = 4
    base_texture = Texture(MinecraftBlock.texture_path, get_coords(1, 4))


class Grass(MinecraftBlock):
    id = 1
    TOP = Texture(MinecraftBlock.texture_path, get_coords(1, 2))
    BOTTOM = Dirt.base_texture
    SIDE = Texture(MinecraftBlock.texture_path, get_coords(1, 3))
    base_texture = MultiTexture(BOTTOM, TOP, SIDE, SIDE, SIDE, SIDE)


class Sand(MinecraftBlock):
    id = 2
    base_texture = Texture(MinecraftBlock.texture_path, get_coords(3, 5))


class Brick(MinecraftBlock):
    id = 3
    base_texture = Texture(MinecraftBlock.texture_path, get_coords(1, 8))


class Log(MinecraftBlock):
    id = 5
    base_texture = Texture(MinecraftBlock.texture_path, get_coords(2, 5))


class Leaves(MinecraftBlock):
    id = 6
    base_texture = Texture(MinecraftBlock.texture_path, get_coords(2, 12))


class Water(MinecraftBlock):
    water_group = Group()
    id = 7
    blank = Color(0, 0, 0, 0)
    water = Color(0, 0, 255, 100)
    base_texture = Color(50, 50, 255, 100)


class Chunk:
    key = {}
    size = 16
    load = set([])
    terrain_generator = pnoise2

    def __init__(self, x: int, z: int):
        # print(x, z)
        self.loaded = True
        self.unloaded_data = {}
        self.chunk_pos = self.regular_pos_to_chunk(x, z)
        x, z = self.chunk_pos
        self.start_point = int(x) * self.size, int(z) * self.size
        self.blocks = {}
        self.create_new()
        self.load.add(self)

    def generate_height_map(self):
        ox, oz = self.start_point
        self.height_map = [[self.get_height(x, z) for x in range(ox, ox + self.size)] for z in
                           range(oz, oz + self.size)]

    def create_new(self):
        self.generate_height_map()
        tree_chance = 1 / 200
        water_level = 3
        ox, oz = self.start_point
        for x in range(self.size):
            for z in range(self.size):
                height = self.height_map[z][x]
                for y in range(max(height, water_level)):
                    pos = x + ox, y, z + oz
                    type_ = Grass if y == height-1 and height > water_level else Sand if y == height-1 else Dirt if y < height else Water
                    # hidden = False
                    # if y < height - 1 and y != 0 and x > 0 and z > 0 and x < self.size - 1 and z < self.size - 1:
                    #     left = self.height_map[z - 1][x]
                    #     right = self.height_map[z + 1][x]
                    #     front = self.height_map[z][x + 1]
                    #     back = self.height_map[z][x - 1]
                    #     if left > y and right > y and front > y and back > y:
                    #         hidden = True
                    hidden = False
                    Window.active_window.queue(self.add_block, (pos, type_, hidden))
                if height < water_level and tree_chance > random():
                    # print("making tree")
                    self.make_tree((x + ox, height, z + oz))
        # print("#------------------#")

    def add_block(self, pos, type_, hidden=False):
        if self.loaded:
            block = type_(*pos)
            self.blocks[pos] = block
            if hidden:
                block.hide()
            if type_ == Water:
                Water.water_group.add(block)
        else:
            self.unloaded_data[pos] = type_.id

    def remove_block(self, pos):
        try:
            block = self.blocks.pop(pos)
            del block
        except KeyError as bad_thing:
            pass

    def unload(self):
        for pos in self.blocks:
            block = self.blocks[pos]
            self.unloaded_data[pos] = block.id
            del block
        self.blocks = {}
        self.loaded = False
        self.load.remove(self)

    def reload(self):
        # print("reloaded")
        for pos in self.unloaded_data:
            Window.active_window.queue(self.add_block, (pos, MinecraftBlock.ids[self.unloaded_data[pos]]))
        self.loaded = True
        self.load.add(self)

    @staticmethod
    def regular_pos_to_chunk(x, y):
        return x // Chunk.size, y // Chunk.size

    @staticmethod
    def chunk_pos_to_regualar(x, y):
        return x * Chunk.size, y * Chunk.size

    def __repr__(self):
        return str(self.chunk_pos)

    def get_height(self, x, z):
        x /= 20
        z /= 20
        random_num = self.terrain_generator(x, z, octaves=200, lacunarity=0.1)
        amplified = random_num * 25
        integer = abs(round(amplified))
        thing = integer + 1
        # thing = abs(round(self.terrain_generator(x, z) * 1000)) + 1
        # print(random_num, amplified, thing)
        return thing

    def make_tree(self, pos):
        x, y, z = pos
        tree_height = 4
        for dy in range(tree_height):  # make the trunk
            Window.active_window.queue(self.add_block, ((x, y + dy, z), Log))

        for dy in range(2, 4):  # two layers high
            for dx in range(-2, 3):  # 5x5 grid
                for dz in range(-2, 3):
                    if not (dx == 0 and dz == 0):
                        Window.active_window.queue(self.add_block, ((x + dx, y + dy, z + dz), Leaves))
        top_height = y + tree_height
        Window.active_window.queue(self.add_block, ((x + 0, top_height, z + 0), Leaves))
        Window.active_window.queue(self.add_block, ((x + 1, top_height, z + 0), Leaves))
        Window.active_window.queue(self.add_block, ((x + 0, top_height, z + 1), Leaves))
        Window.active_window.queue(self.add_block, ((x - 1, top_height, z + 0), Leaves))
        Window.active_window.queue(self.add_block, ((x + 0, top_height, z - 1), Leaves))
