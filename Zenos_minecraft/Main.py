import Zenos_package
from Zenos_minecraft.Blocks import *


def normalize(pos):
    return tuple([int(round(i-.5)) for i in pos])


class Window(Zenos_package.Window):
    view_label = Zenos_package.TwoD.Text((0, 50), "", 10, Zenos_package.RED)
    position_label = Zenos_package.TwoD.Text((0, 20), "", 10, Zenos_package.RED)
    inventory_label = Zenos_package.TwoD.Text((0, 200), "", 10, Zenos_package.RED)

    def __init__(self):
        super(Window, self).__init__()
        self.position = 0, 3, 0
        self.lock_mouse()
        self.set_background(LIGHT_BLUE)
        self.load_radius = 3
        self.create_chunks(self.load_radius)
        self.center = 0, 0
        self.cx, self.cy = self.screen_center = self.width//2, self.height//2
        self.reticle_v = Zenos_package.TwoD.Line((self.cx, self.cy+10), (self.cx, self.cy-10))
        self.reticle_h = Zenos_package.TwoD.Line((self.cx-10, self.cy), (self.cx+10, self.cy))
        self.player_height = 2
        self.set_fullscreen()
        self.inventory = {Brick.id: 20}
        self.selected_block = Brick
        self.start()

    def on_resize(self, width, height):
        self.reticle_h.moveTo((width//2, height//2))
        self.reticle_v.moveTo((width//2, height//2))

    def create_chunks(self, radius):
        self.chunks = {}
        self.load_chunks = []
        for x, z in self.get_square((0, 0), radius):
            pos = x, z
            c = Chunk(*Chunk.chunk_pos_to_regualar(x, z))
            self.chunks[pos] = c
            self.load_chunks.append(pos)

    def get_square(self, pos, radius):
        x1, z1 = pos
        return list(set([(x+x1, z+z1) for x in range(-radius, radius+1) for z in range(-radius, radius+1)]))

    def periodic(self, dt: float):
        previous = self.position
        self._inner.process_queue()
        if self.is_pressed(self.keys.DOWN) or self.is_pressed(self.keys.S):
            self.move_forward(-dt * self.speed)
        elif self.is_pressed(self.keys.UP) or self.is_pressed(self.keys.W):
            self.move_forward(dt * self.speed)
        elif self.is_pressed(self.keys.RIGHT) or self.is_pressed(self.keys.D):
            self.move_sideways(dt * self.speed)
        elif self.is_pressed(self.keys.LEFT) or self.is_pressed(self.keys.A):
            self.move_sideways(-dt * self.speed)
        b = self.block_at(normalize(self.position))
        if b is not None and b.id != Water.id:
            self.position = previous
        self.render_shown()
        self.render(Water.water_group)
        self.update_loaded()
        self.view_label.set_string(self.rotation)
        self.position_label.set_string(self.position)
        s = ""
        for block in self.inventory:
            s += f"{MinecraftBlock.ids[block].__name__}: {self.inventory[block]}\n"
        self.inventory_label.set_string(s)
        self.render(self.view_label, self.position_label, self.inventory_label)

    def update_loaded(self):
        x, y, z = self.position
        center = Chunk.regular_pos_to_chunk(x, z)
        if center != self.center:
            new_loaded = self.get_square(center, self.load_radius)
            self.center = center
            for new, old in zip(new_loaded, self.load_chunks):
                if new not in self.load_chunks:
                    if new not in self.chunks:
                        self.chunks[new] = Chunk(*Chunk.chunk_pos_to_regualar(*new))
                    else:
                        self.chunks[new].reload()
                if old not in new_loaded:
                    self.chunks[old].unload()
            self.load_chunks = new_loaded

    def on_key_press(self, symbol, modifiers):
        super(Window, self).on_key_press(symbol, modifiers)
        if symbol == self.keys.E:
            self.place_block()

    def hit_test(self, max_distance=8):
        position = self.position
        vector = self.vision_vector()
        step_dis = 10
        x, y, z = position
        dx, dy, dz = vector
        previous = x, y, z
        for _ in range(max_distance * step_dis):
            key = normalize((x, y, z))
            if key != previous:
                b = self.block_at(key)
                if b is not None and b.id != Water.id:
                    return key, previous
            previous = key
            x, y, z = x + dx / step_dis, y + dy / step_dis, z + dz / step_dis
        return None, None

    def block_at(self, pos):
        x, y, z = pos
        try:
            chunk = self.chunks[Chunk.regular_pos_to_chunk(x, z)]
            return chunk.blocks[pos]
        except KeyError:
            return None

    def add_block(self, pos, block=Brick):
        x, y, z = pos
        try:
            chunk = self.chunks[Chunk.regular_pos_to_chunk(x, z)]
            if block.id in self.inventory and self.inventory[block.id] > 0:
                chunk.add_block(pos, block)
                self.inventory[block.id] -= 1
                if self.inventory[block.id] <= 0:
                    self.inventory.pop(block.id)
                    keys = list(self.inventory.keys())
                    self.selected_block = self.inventory[keys[0]] if len(keys) > 0 else None
                    print(self.inventory)
        except KeyError:
            pass

    def remove_block(self, pos):
        x, y, z = pos
        try:
            chunk = self.chunks[Chunk.regular_pos_to_chunk(x, z)]
            chunk.remove_block(pos)
        except KeyError:
            print("test")
            return None

    def on_mouse_press(self, x, y, button, modifiers):
        self.break_block()

    def break_block(self):
        hit, previous = self.hit_test()
        if hit is not None:
            b = self.block_at(hit)
            self.remove_block(hit)
            if len(self.inventory) == 0:
                self.selected_block = type(b)
            self.inventory[b.id] = self.inventory[b.id] + 1 if b.id in self.inventory else 1

    def place_block(self):
        hit, previous = self.hit_test()
        if hit is not None:
            self.add_block(previous, self.selected_block)

    @staticmethod
    def neighbors(pos, h=1):
        x, y, z = pos
        neigbors = []
        for dy in range(h):
            _y = y - dy
            neigbors.extend([(x+1, _y, z), (x-1, _y, z), (x, _y, z+1), (x, _y, z-1)])  # sides
        neigbors.extend([(x, y+1, z), (x, y-h, z)])
        return neigbors

    def update_pos(self, pos):
        pass


if __name__ == '__main__':
    w = Window()
