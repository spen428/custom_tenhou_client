import os

import pygame

import tenhou.gui.main
import tenhou.gui.main
from random import randint
import math


def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


class _CallType(object):
    NUKE = 0
    CHII = 1
    PON = 2
    ANKAN = 3
    SHOUMINKAN = 4
    DAIMINKAN = 5

    @staticmethod
    def is_kantsu(call_type):
        return call_type in [_CallType.ANKAN, _CallType.DAIMINKAN, _CallType.SHOUMINKAN]


class InGameUi(object):
    def __init__(self, client):
        self.client = client
        # TILES 64
        self.tiles64 = []
        for suit in ["bamboo", "man", "pin"]:
            for number in range(1, 10):
                name = "{}{}.png".format(suit, number)
                img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", name))
                self.tiles64.append(img)
        for wind in ["east", "south", "west", "north"]:
            img = pygame.image.load(
                os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "wind-" + wind + ".png"))
            self.tiles64.append(img)
        for dragon in ["chun", "haku", "hatsu"]:
            img = pygame.image.load(
                os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "dragon-" + dragon + ".png"))
            self.tiles64.append(img)
        for suit in ["bamboo", "man", "pin"]:
            img = pygame.image.load(
                os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "red-dora-" + suit + "5.png"))
            self.tiles64.append(img)
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "face-down.png"))
        self.tiles64.append(img)
        # TILES 38
        self.tiles38 = []
        for suit in "SMP":
            for number in range(1, 10):
                name = "{}{}.gif".format(suit, number)
                img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", name))
                self.tiles38.append(img)
        for tile in ["E", "S", "W", "N", "D1", "D2", "D3"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", tile + ".gif"))
            self.tiles38.append(img)
        for suit in "SMP":
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", suit + "5d.gif"))
            self.tiles38.append(img)
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", "back.gif"))
        self.tiles38.append(img)
        # Other
        self.discards = [[randint(0, len(self.tiles38) - 2) for _ in range(21)] for _ in range(4)]
        self.calls = []
        for _ in range(4):
            player_calls = [(randint(0, len(self.tiles38) - 2), 2, _CallType.SHOUMINKAN),
                            (len(self.tiles38) - 8, 4, _CallType.NUKE),
                            (randint(0, len(self.tiles38) - 2), 0, _CallType.DAIMINKAN),
                            (randint(0, len(self.tiles38) - 2), 0, _CallType.PON)]
            self.calls.append(player_calls)
        self.tile_rects = []
        self.step = 0

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles38[tile_id]
        return self.tiles64[tile_id]

    def _draw_hand(self, canvas, cx, cy, tiles, tsumohai=None):
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        total_width = tile_width * len(tiles)
        x = cx - (total_width / 2)
        y = cy - (tile_height / 2)
        for tile in tiles:
            self._draw_tile(canvas, tile, x, y)
            x += tile_width
        if tsumohai is not None:
            x += 0.5 * tile_width
            self._draw_tile(canvas, tsumohai, x, y)

    def draw_to_canvas(self, canvas):
        # Clear storage
        self.tile_rects = []

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2,
                                  canvas.get_height() - 25))

        for n in range(4):
            self._draw_discards(canvas, self.discards[n], n)
            self._draw_calls(canvas, self.calls[n], n)
        hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]
        self._draw_hand(canvas, canvas.get_width() / 2, 7 * canvas.get_height() / 8, hand_tiles, 22)

        # Debug lines
        pygame.draw.line(canvas, (0, 0, 0), (0, canvas.get_height() / 2), (canvas.get_width(), canvas.get_height() / 2))
        pygame.draw.line(canvas, (0, 0, 0), (canvas.get_width() / 2, 0), (canvas.get_width() / 2, canvas.get_height()))
        tile_width = self._get_tile_image(0, True).get_width()
        pygame.draw.rect(canvas, (0, 0, 0),
                         pygame.Rect(canvas.get_width() / 2 - tile_width * 3, canvas.get_height() / 2 - tile_width * 3,
                                     tile_width * 6,
                                     tile_width * 6), 1)

    def _draw_tile(self, canvas, tile_id, x, y, small=False, rotation=0):
        tile_image = self._get_tile_image(tile_id, small)
        if rotation is not 0:
            tile_image = pygame.transform.rotate(tile_image, rotation)
        canvas.blit(tile_image, (x, y))
        self.tile_rects.append(pygame.Rect(x, y, tile_image.get_width(), tile_image.get_height()))

    def _draw_calls(self, canvas, calls, position):
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        x = canvas.get_width() - 3 * tile_width / 2
        y = canvas.get_height() - 3 * tile_height / 2
        for call in calls:
            if position == 0:
                rotation = 0
                tile_id, called, call_type = call
                if call_type == _CallType.NUKE:
                    num_tiles = 1
                elif call_type in [_CallType.DAIMINKAN, _CallType.ANKAN]:
                    num_tiles = 4
                else:
                    num_tiles = 3
                for idx in range(num_tiles):
                    if call_type != _CallType.NUKE and idx == called:
                        x -= (tile_height - tile_width)
                        y += (tile_height - tile_width)
                        self._draw_tile(canvas, tile_id, x, y, True, rotation + 90)
                        if call_type == _CallType.SHOUMINKAN:
                            self._draw_tile(canvas, tile_id, x, y - tile_width, True, rotation + 90)
                        x -= tile_width
                        y -= (tile_height - tile_width)
                    else:
                        self._draw_tile(canvas, tile_id, x, y, True, rotation)
                        x -= tile_width
                    if call_type == _CallType.NUKE:
                        myfont = pygame.font.SysFont("Monospace", 13)
                        myfont.set_bold(True)
                        nuke_text = myfont.render("{}x".format(called), 1, (0, 0, 0))
                        tx = x + tile_width + nuke_text.get_width() / 4
                        ty = y + tile_height
                        canvas.blit(nuke_text, (tx, ty))
            else:
                pass

    def _draw_discards(self, canvas, tiles, position):
        x_count = 0
        y_count = 0
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        cx = canvas.get_width() / 2
        cy = canvas.get_height() / 2
        for tile in tiles:
            if position == 0:  # 自分
                rotation = 0
                x = cx + (x_count - 3) * tile_width
                y = cy + y_count * tile_height + 3.5 * tile_width
            elif position == 1:  # 下家
                rotation = -90
                x = cx + y_count * tile_height + 3.5 * tile_width
                y = cy - (x_count - 2) * tile_width
            elif position == 2:  # 対面
                rotation = -180
                x = cx - (x_count - 2) * tile_width
                y = cy - (y_count + 1) * tile_height - 3.5 * tile_width
            elif position == 3:  # 上家
                rotation = -270
                x = cx - (y_count + 1) * tile_height - 3.5 * tile_width
                y = cy + (x_count - 3) * tile_width
            else:
                raise ValueError("Position must be 0-3")
            self._draw_tile(canvas, tile, x, y, True, rotation)
            x_count += 1
            if x_count == 6 and y_count < 2:
                x_count = 0
                y_count += 1
