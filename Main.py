from __future__ import division

from pyglet.window import key, mouse
from Constants import *


main = None


def get_block_pos(position):
    x, y, z = position
    x, y, z = int(round(x)), int(round(y)), int(round(z))
    return x, y, z


def get_chunk(pos):
    x, y, z = pos
    x, y, z = x // Chunk.x_size, y // Chunk.y_size, z // Chunk.z_size
    return x, y, z


def get_vertices(x, y, z, n):
    return [
        x - n, y + n, z - n, x - n, y + n, z + n, x + n, y + n, z + n, x + n, y + n, z - n,  # top
        x - n, y - n, z - n, x + n, y - n, z - n, x + n, y - n, z + n, x - n, y - n, z + n,  # bottom
        x - n, y - n, z - n, x - n, y - n, z + n, x - n, y + n, z + n, x - n, y + n, z - n,  # left
        x + n, y - n, z + n, x + n, y - n, z - n, x + n, y + n, z - n, x + n, y + n, z + n,  # right
        x - n, y - n, z + n, x + n, y - n, z + n, x + n, y + n, z + n, x - n, y + n, z + n,  # front
        x + n, y - n, z - n, x - n, y - n, z - n, x - n, y + n, z - n, x + n, y + n, z - n,  # back
    ]


def setup_fog():
    """ Configure the OpenGL fog properties.
    """
    # Enable fog. Fog "blends a fog color with each rasterized pixel fragment's
    # post-texturing color."
    glEnable(GL_FOG)
    # Set the fog color.
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    # Say we have no preference between rendering speed and quality.
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    # Specify the equation used to compute the blending factor.
    glFogi(GL_FOG_MODE, GL_LINEAR)
    # How close and far away fog starts and ends. The closer the start and end,
    # the denser the fog in the fog range.
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)


def setup():
    """ Basic OpenGL configuration.
    """
    # Set the color of "clear", i.e. the sky, in rgba.
    glClearColor(0.5, 0.69, 1.0, 1)
    # Enable culling (not rendering) of back-facing facets -- facets that aren't
    # visible to you.
    glEnable(GL_CULL_FACE)
    # Set the texture minification/magnification function to GL_NEAREST (nearest
    # in Manhattan distance) to the specified texture coordinates. GL_NEAREST
    # "is generally faster than GL_LINEAR, but it can produce textured images
    # with sharper edges because the transition between texture elements is not
    # as smooth."
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()


class Chunk:
    x_size = 16
    y_size = 256
    z_size = 16

    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.all_blocks = {}
        self.visible_blocks = {}
        self.loaded = True

    def render(self):
        self.batch.draw()

    def add_block(self, x, y, z, texture):
        vertex_data = get_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        # create vertex list
        self.batch.add(24, GL_QUADS, texture_group, ('v3f/static', vertex_data), ('t2f/static', texture_data))
        self.all_blocks[(x, y, z)] = 1  # replace with id when there

    def remove_block(self, x, y, z):
        pos = x, y, z
        if pos in self.all_blocks:
            self.all_blocks.pop(pos)
            if pos in self.visible_blocks:
                self.visible_blocks.pop(pos)

    def update(self): pass  # will be implemented when ticks are a thing

    def update_visibility(self, x, y, z): pass

    def check_visible(self, x, y, z): pass


class Game:
    chunk_list = []
    loaded_chunks = []
    FACES = [
        (0, 1, 0),
        (0, -1, 0),
        (-1, 0, 0),
        (1, 0, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]

    def __init__(self):
        # A mapping from position to the texture of the block at that position.
        # This defines all the blocks that are currently in the world.
        self.world = {}

        # Same mapping as `world` but only contains blocks that are shown.
        self.shown = {}

        self.create_world()

    def create_world(self):
        coords = get_chunk((0, 0, 0))
        chunk = Chunk()
        self.world[coords] = chunk
        chunk.add_block(0, 0, 0, GRASS)

    def hit_test(self, position, vector, max_distance=8):
        step_dis = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * step_dis):
            key = get_block_pos((x, y, z))
            if key != previous and self.block_at(*key):
                return key, previous
            previous = key
            x, y, z = x + dx / step_dis, y + dy / step_dis, z + dz / step_dis
        return None, None

    def place_block(self, texture, pos):
        chunk = self.world[get_chunk(pos)]
        chunk.add_block(*pos, texture)

    def delete_block(self, pos):
        chunk = self.world[get_chunk(pos)]
        chunk.remove_block(*pos)

    def block_neighbors(self, pos):
        x, y, z = pos
        neighbors = []
        for dx, dy, dz in self.FACES:
            new_coord = x + dx, y + dy, z + dz
            if self.block_at(*new_coord):
                neighbors.append(new_coord)
        return neighbors

    def exposed(self, pos):
        for neighbor in pos:
            if self.block_at(*neighbor):
                return True
        return False

    def draw_world(self):
        for chunk in self.loaded_chunks:
            chunk.render()

    def load_chunk(self, pos):
        if pos not in self.loaded_chunks:
            chunk = self.world[pos]
            self.loaded_chunks.append(chunk)

    def hide_chunk(self, pos):
        self.loaded_chunks.remove(chunk)

    def block_at(self, x, y, z):
        chunk = self.world[get_chunk((x, y, z))]
        return (x, y, z) in chunk.all_blocks

    def change_sectors(self, before, after):
        """ Move from sector `before` to sector `after`. A sector is a
        contiguous x, y sub-region of world. Sectors are used to speed up
        world rendering.
        """
        before_set = set()
        after_set = set()
        pad = 4
        for dx in range(-pad, pad + 1):
            for dy in [0]:  # xrange(-pad, pad + 1):
                for dz in range(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.load_chunk(sector)
        for sector in hide:
            self.hide_chunk(sector)


class Player:
    def __init__(self, start_pos=(0, 0, 0), start_rotation=(0, 0), forward=0, side=0, up_vel=0):
        self.x, self.y, self.z = start_pos
        self.rotation = start_rotation
        self.forward = forward
        self.side = side
        self.up = up_vel
        self.current_sector = None
        self.selected_block = None

    def jump(self): pass
    def get_sight_vector(self): pass
    def get_motion_vector(self): pass
    def collide(self): pass
    def move(self): pass
    def get_sector(self): pass


class Window(pyglet.window.Window):
    fps = 60

    def __init__(self, *args, **kwargs):
        global main
        super(Window, self).__init__(*args, **kwargs)

        # Whether or not the window exclusively captures the mouse.
        self.exclusive = False

        # When flying gravity has no effect and speed is increased.
        self.flying = True

        # Strafing is moving lateral to the direction you are facing,
        # e.g. moving to the left or right while continuing to face forward.
        #
        # First element is -1 when moving forward, 1 when moving back, and 0
        # otherwise. The second element is -1 when moving left, 1 when moving
        # right, and 0 otherwise.
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = (0, 0, 0)

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (0, 0)

        # Which sector the player is currently in.
        self.sector = None

        # The crosshairs at the center of the screen.
        self.reticle = None

        # Velocity in the y (upward) direction.
        self.dy = 0

        # A list of blocks the player can place. Hit num keys to cycle.
        self.inventory = [BRICK, GRASS, SAND]

        # The current block the user can place. Hit num keys to cycle.
        self.block = self.inventory[0]

        # Convenience list of num keys.
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]

        # Instance of the model that handles the world.
        self.model = Game()
        main = self.model

        # the player
        self.player = Player()

        # The label that is displayed in the top left of the canvas.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
                                       x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
                                       color=(0, 0, 0, 255))

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / self.fps)

    def set_exclusive_mouse(self, exclusive):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.
        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def update(self, dt):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called when a mouse button is pressed. See pyglet docs for button
        amd modifier mappings.
        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        button : int
            Number representing mouse button that was clicked. 1 = left button,
            4 = right button.
        modifiers : int
            Number representing any modifying keys that were pressed when the
            mouse button was clicked.
        """
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # ON OSX, control + left click = right click.
                if previous:
                    self.model.place_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and block:
                texture = self.model.world[block]
                if texture != STONE:  # stone is bedrock
                    self.model.delete_block(block)
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Called when the player moves the mouse.
        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        dx, dy : float
            The movement of the mouse.
        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press(self, symbol, modifiers):
        """ Called when the player presses a key. See pyglet docs for key
        mappings.
        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.
        """
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]

    def on_key_release(self, symbol, modifiers):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.
        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.
        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

    def on_resize(self, width, height):
        """ Called when the window is resized to a new `width` and `height`.
        """
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
                                                   ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
                                                   )
    def on_draw(self):
        """ Called by pyglet to draw the view.  """
        self.clear()  # clears previous view
        self.set_3d()  # prepares 3d visuals
        glColor3d(1, 1, 1)  # something about colors - look into
        self.model.draw_world()  # calls the world to draw everything
        self.draw_focused_block()  # draws outline on viewed block
        self.set_2d()  # prepare to draw 2d
        self.draw_label()  # draw info label
        self.draw_reticle()  # draw pointer

    def configure_3d(self):
        width, height = self.get_size()  # window size
        glEnable(GL_DEPTH_TEST)  # start 3d capabilities
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))  # adjust window size
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()  # clears matrix
        gluPerspective(65.0, width / float(height), 0.1, 60.0)  # set up FOVs
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)  # rotates camera sideways
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))  # rotates camera up
        x, y, z = self.position
        glTranslatef(-x, -y, -z)  # moves camera to your potion

    def configure_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)  # 3d functions
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def draw_label(self):
        """ Draw the label in the top left of the screen.
        """
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z,
            len(self.model._shown), len(self.model.world))
        self.label.draw()

    def draw_recticle(self):
        """ Draw the crosshairs in the center of the screen. """
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

    def draw_health(self): pass
    def draw_hotbar(self): pass
    def draw_hunger(self): pass
