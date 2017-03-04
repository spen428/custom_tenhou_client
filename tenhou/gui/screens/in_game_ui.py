import math
import os
from random import randint

import pygame

import tenhou.gui.main
from tenhou.gui.screens import Screen


def rotate(origin, point, degrees):
    angle = math.radians(degrees)
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


def _load_64px_tile_sprites():
    tiles = []
    for suit in ["bamboo", "man", "pin"]:
        for number in range(1, 10):
            name = "{}{}.png".format(suit, number)
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", name))
            tiles.append(img)
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(
            os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "wind-" + wind + ".png"))
        tiles.append(img)
    for dragon in ["chun", "haku", "hatsu"]:
        img = pygame.image.load(
            os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "dragon-" + dragon + ".png"))
        tiles.append(img)
    for suit in ["bamboo", "man", "pin"]:
        img = pygame.image.load(
            os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "red-dora-" + suit + "5.png"))
        tiles.append(img)
    img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "face-down.png"))
    tiles.append(img)
    return tiles


def _load_38px_tile_sprites():
    tiles = []
    for suit in "SMP":
        for number in range(1, 10):
            name = "{}{}.gif".format(suit, number)
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", name))
            tiles.append(img)
    for tile in ["E", "S", "W", "N", "D1", "D2", "D3"]:
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", tile + ".gif"))
        tiles.append(img)
    for suit in "SMP":
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", suit + "5d.gif"))
        tiles.append(img)
    img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_38", "back.gif"))
    tiles.append(img)
    return tiles


class InGameScreen(Screen):
    def __init__(self, client):
        self.client = client
        # TILES 64
        self.tiles_64px = _load_64px_tile_sprites()
        # TILES 38
        self.tiles_38px = _load_38px_tile_sprites()
        # Other
        self.discards = [[randint(0, len(self.tiles_38px) - 2) for _ in range(21)] for _ in range(4)]
        self.calls = []
        for _ in range(4):
            player_calls = [(randint(0, len(self.tiles_38px) - 2), 2, _CallType.SHOUMINKAN),
                            (len(self.tiles_38px) - 8, 4, _CallType.NUKE),
                            (randint(0, len(self.tiles_38px) - 2), 0, _CallType.DAIMINKAN),
                            (randint(0, len(self.tiles_38px) - 2), 0, _CallType.PON)]
            self.calls.append(player_calls)
        self.tile_rects = []
        self.step = 0

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles_38px[tile_id]
        return self.tiles_64px[tile_id]

    def _draw_hand(self, canvas, center_pos, tiles, tsumohai=None):
        cx, cy = center_pos
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        total_width = tile_width * len(tiles)
        x = cx - (total_width / 2)
        y = cy - (tile_height / 2)
        for tile in tiles:
            self._draw_tile(canvas, tile, (x, y))
            x += tile_width
        if tsumohai is not None:
            x += 0.5 * tile_width
            self._draw_tile(canvas, tsumohai, (x, y))

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
        self._draw_hand(canvas, (canvas.get_width() / 2, 7 * canvas.get_height() / 8), hand_tiles, 22)
        self._draw_center_console(canvas, [0, 1, 2, 3], [72300, 8200, 11500, 23200], [True, False, False, True])

        # Debug lines
        pygame.draw.line(canvas, (0, 0, 0), (0, canvas.get_height() / 2), (canvas.get_width(), canvas.get_height() / 2))
        pygame.draw.line(canvas, (0, 0, 0), (canvas.get_width() / 2, 0), (canvas.get_width() / 2, canvas.get_height()))
        tile_width = self._get_tile_image(0, True).get_width()
        pygame.draw.rect(canvas, (0, 0, 0),
                         pygame.Rect(canvas.get_width() / 2 - tile_width * 3, canvas.get_height() / 2 - tile_width * 3,
                                     tile_width * 6,
                                     tile_width * 6), 1)

    def _draw_tile(self, canvas, tile_id, pos, small=False, rotation=0):
        x, y = pos
        tile_image = self._get_tile_image(tile_id, small)
        if rotation is not 0:
            tile_image = pygame.transform.rotate(tile_image, rotation)
        canvas.blit(tile_image, (x, y))
        self.tile_rects.append(pygame.Rect(x, y, tile_image.get_width(), tile_image.get_height()))

    def _draw_calls(self, canvas, calls, position):
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        cx = canvas.get_width() / 2
        cy = canvas.get_height() / 2
        x = canvas.get_width() - 3 * tile_width / 2
        y = canvas.get_height() - 3 * tile_height / 2
        for call in calls:
            rotation = self._position_to_angle_degrees(position)
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
                    pos = rotate((cx, cy), (x, y), rotation)
                    self._draw_tile(canvas, tile_id, pos, True, rotation + 90)
                    if call_type == _CallType.SHOUMINKAN:
                        pos = rotate((cx, cy), (x, y - tile_width), rotation)
                        self._draw_tile(canvas, tile_id, pos, True, rotation + 90)
                    x -= tile_width
                    y -= (tile_height - tile_width)
                else:
                    pos = rotate((cx, cy), (x, y), rotation)
                    self._draw_tile(canvas, tile_id, pos, True, rotation)
                    x -= tile_width
                    if call_type == _CallType.NUKE:
                        myfont = pygame.font.SysFont("Monospace", 13)
                        myfont.set_bold(True)
                        nuke_text = myfont.render("{}x".format(called), 1, (0, 0, 0))
                        tx = x + tile_width + nuke_text.get_width() / 4
                        ty = y + tile_height
                        pos = rotate((cx, cy), (tx, ty), rotation)
                        canvas.blit(nuke_text, pos)

    def _draw_discards(self, canvas, tiles, position):
        x_count = 0
        y_count = 0
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        cx = canvas.get_width() / 2
        cy = canvas.get_height() / 2
        for tile in tiles:
            x = cx + (x_count - 3) * tile_width
            y = cy + y_count * tile_height + 3.5 * tile_width
            rotation = self._position_to_angle_degrees(position)
            pos = rotate((cx, cy), (x, y), rotation)
            self._draw_tile(canvas, tile, pos, True, rotation)
            x_count += 1
            if x_count == 6 and y_count < 2:
                x_count = 0
                y_count += 1

    def _draw_center_console(self, canvas, positions, scores, riichi_states):
        cx = canvas.get_width() / 2
        cy = canvas.get_height() / 2
        score_font = pygame.font.SysFont("Arial", 16)
        seat_wind_font = pygame.font.SysFont("Arial", 40)
        for idx in range(len(scores)):
            score_text = score_font.render(str(scores[idx]), 1, (0, 0, 0))
            seat_wind_text = seat_wind_font.render(self._wind_ordinal_to_string(positions[idx]), 1, (0, 0, 0))
            if positions[idx] == 0:
                canvas.blit(seat_wind_text, (cx - seat_wind_text.get_width() / 2, cy))
                canvas.blit(score_text, (cx - score_text.get_width() / 2, cy + 50))

    @staticmethod
    def _wind_ordinal_to_string(ordinal):
        if ordinal == 0:
            return "東"
        if ordinal == 1:
            return "南"
        if ordinal == 2:
            return "西"
        else:
            return "北"

    @staticmethod
    def _position_to_angle_degrees(position):
        if position == 0:  # 自分
            return 0
        elif position == 1:  # 下家
            return -90
        elif position == 2:  # 対面
            return -180
        elif position == 3:  # 上家
            return -270
        else:
            raise ValueError("Position must be 0-3")