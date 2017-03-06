import math
import os
from random import randint

import pygame

import tenhou.gui.main
from tenhou.gui.screens import AbstractScreen


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
    resource_dir = tenhou.gui.main.get_resource_dir()
    # suited tiles
    for suit in ["bamboo", "man", "pin"]:
        for number in range(1, 10):
            name = "{}{}.png".format(suit, number)
            img = pygame.image.load(os.path.join(resource_dir, "tiles_64", name))
            tiles.append(img)
        # dora fives
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "red-dora-" + suit + "5.png"))
        tiles.append(img)

    # honour tiles
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "wind-" + wind + ".png"))
        tiles.append(img)
    for dragon in ["chun", "haku", "hatsu"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "dragon-" + dragon + ".png"))
        tiles.append(img)

    # back of tile
    img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "face-down.png"))
    tiles.append(img)
    return tiles


def _load_38px_tile_sprites():
    tiles = []
    resource_dir = tenhou.gui.main.get_resource_dir()
    # suited tiles
    for suit in "SMP":
        for number in range(1, 10):
            name = "{}{}.gif".format(suit, number)
            img = pygame.image.load(os.path.join(resource_dir, "tiles_38", name))
            tiles.append(img)
        # dora fives
        img = pygame.image.load(os.path.join(resource_dir, "tiles_38", suit + "5d.gif"))
        tiles.append(img)

    # honour tiles
    for tile in ["E", "S", "W", "N", "D1", "D2", "D3"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_38", tile + ".gif"))
        tiles.append(img)

    # back of tile
    img = pygame.image.load(os.path.join(resource_dir, "tiles_38", "back.gif"))
    tiles.append(img)
    return tiles


def _load_wind_sprites():
    winds = []
    resource_dir = tenhou.gui.main.get_resource_dir()
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(os.path.join(resource_dir, wind + ".png"))
        winds.append(img)
    return winds


def _wind_ordinal_to_string(ordinal):
    if ordinal == 0:
        return u"東"
    if ordinal == 1:
        return u"南"
    if ordinal == 2:
        return u"西"
    else:
        return u"北"


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


class InGameScreen(AbstractScreen):
    def __init__(self, client):
        self.DEBUG = True
        self.client = client
        # TILES 64
        self.tiles_64px = _load_64px_tile_sprites()
        # TILES 38
        self.tiles_38px = _load_38px_tile_sprites()
        # WINDS
        self.wind_sprites = _load_wind_sprites()
        self.riichi_stick_sprite = pygame.image.load(
            os.path.join(tenhou.gui.main.get_resource_dir(), "riichi_stick.png"))
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

    # Private methods #

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles_38px[tile_id]
        return self.tiles_64px[tile_id]

    # Superclass methods #

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def on_window_resized(self):
        pass

    def draw_to_canvas(self, canvas):
        # Clear storage
        self.tile_rects = []

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2, canvas.get_height() - 25))

        for n in range(len(self.discards)):
            pass
            # self._draw_discards(canvas, self.discards[n], n)
            # self._draw_calls(canvas, self.calls[n], n)
        # hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]
        # self._draw_hand(canvas, (canvas.get_width() / 2, 7 * canvas.get_height() / 8), hand_tiles, 22)
        self._draw_centre_console(canvas, [0, 1, 2, 3], [72300, 8200, 11500, 23200], [True, False, False, True])

        if self.DEBUG:  # Draw positioning lines
            canvas_width = canvas.get_width()
            canvas_height = canvas.get_height()
            centre_x = canvas_width / 2
            centre_y = canvas_height / 2

            tile_img = self._get_tile_image(0, True)
            tile_width = tile_img.get_width()
            tile_height = tile_img.get_height()

            # Center cross
            pygame.draw.line(canvas, (0, 0, 0), (0, centre_y), (canvas_width, centre_y))
            pygame.draw.line(canvas, (0, 0, 0), (centre_x, 0), (centre_x, canvas_height))

            # Center squares
            for n in [1.5, 3.0, 4.5, 6.0]:
                width = tile_width * n
                x = centre_x - width / 2
                y = centre_y - width / 2
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, width), 1)

            # Discard zones
            width = tile_width * 6
            height = tile_height * 3
            x = centre_x - width / 2
            y = centre_y + height
            pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, height), 1)  # Self
            y = centre_y - 2 * height
            pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, height), 1)  # Toimen
            width, height = height, width  # I love Python
            x = centre_x + width
            y = centre_y - height / 2
            pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, height), 1)  # Shimocha
            x = centre_x - 2 * width
            pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, height), 1)  # Kamicha

    # Drawing methods #

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
            rotation = _position_to_angle_degrees(position)
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
            rotation = _position_to_angle_degrees(position)
            pos = rotate((cx, cy), (x, y), rotation)
            self._draw_tile(canvas, tile, pos, True, rotation)
            x_count += 1
            if x_count == 6 and y_count < 2:
                x_count = 0
                y_count += 1

    def _draw_centre_console(self, canvas, positions, scores, riichi_states):
        centre_x = canvas.get_width() / 2
        centre_y = canvas.get_height() / 2
        tile_img = self._get_tile_image(0, True)
        tile_width = tile_img.get_width()
        tile_height = tile_img.get_height()
        wind_offset = tile_height * 1.20
        score_offset = tile_height * 2.15
        riichi_offset = tile_height * 2.75

        score_font = pygame.font.SysFont("Arial", 16)

        for idx in range(len(positions)):
            score_text = score_font.render(str(scores[idx]), 1, (0, 0, 0))
            wind_sprite = self.wind_sprites[positions[idx]]
            riichi_sprite = self.riichi_stick_sprite
            if positions[idx] == 0:  # Self
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y + wind_offset - wind_sprite.get_height() / 2
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y + score_offset - score_text.get_height() / 2
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y + riichi_offset - riichi_sprite.get_height() / 2
            if positions[idx] == 1:  # Shimocha
                wind_sprite = pygame.transform.rotate(wind_sprite, 90)
                wind_x = centre_x + wind_offset - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, 90)
                score_x = centre_x + score_offset - score_text.get_width() / 2
                score_y = centre_y - score_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, 90)
                riichi_x = centre_x + riichi_offset - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_sprite.get_height() / 2
            if positions[idx] == 2:  # Toimen
                wind_sprite = pygame.transform.rotate(wind_sprite, 180)
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_offset - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, 180)
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y - score_offset - score_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, 180)
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_offset - riichi_sprite.get_height() / 2
            if positions[idx] == 3:  # Kamicha
                wind_sprite = pygame.transform.rotate(wind_sprite, -90)
                wind_x = centre_x - wind_offset - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, -90)
                score_x = centre_x - score_offset - score_text.get_width() / 2
                score_y = centre_y - score_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, -90)
                riichi_x = centre_x - riichi_offset - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_sprite.get_height() / 2

            canvas.blit(wind_sprite, (wind_x, wind_y))
            canvas.blit(score_text, (score_x, score_y))
            canvas.blit(riichi_sprite, (riichi_x, riichi_y))
