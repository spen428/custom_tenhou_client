# coding: utf-8
import math
import os
import time
from random import randint

import pygame

import tenhou.gui.main
from tenhou.gui.screens import AbstractScreen
from tenhou.utils import calculate_score_deltas, seconds_to_time_string


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


class InGameScreen(AbstractScreen):
    def __init__(self, client):
        self.DEBUG = False
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
        self.centre_hover = False
        self.centre_square = None
        self.hover_tile = None
        self.tile_hover_colour = (255, 0, 0)
        self.corner_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 15)
        self.score_font = pygame.font.SysFont("Arial", 16)
        self.discard_timer_font = pygame.font.SysFont("Arial", 10)
        self.name_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 12)
        self.centre_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 12)
        self.start_time_secs = time.time()
        self.discard_start_secs = time.time()
        self.tile_highlights = [
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-green.png")),
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-red.png"))]

    # Private methods #

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles_38px[tile_id]
        return self.tiles_64px[tile_id]

    # Superclass methods #

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pos = pygame.mouse.get_pos()
        if self.centre_square is not None:
            self.centre_hover = self.centre_square.collidepoint(pos)
        self.hover_tile = None
        for rect in self.tile_rects:
            if rect.collidepoint(pos):
                self.hover_tile = rect
                break

    def on_window_resized(self):
        self.centre_square = None

    def draw_to_canvas(self, canvas):
        canvas_width = canvas.get_width()
        canvas_height = canvas.get_height()
        centre_x = canvas_width / 2
        centre_y = canvas_height / 2

        tile_img = self._get_tile_image(0, True)
        tile_width = tile_img.get_width()
        tile_height = tile_img.get_height()

        # Clear storage
        self.tile_rects = []
        if self._get_discard_time() <= 0:
            self.discard_start_secs = time.time()

        # initialise centre square shape
        if self.centre_square is None:
            width = tile_width * 6
            x = centre_x - width / 2
            y = centre_y - width / 2
            self.centre_square = pygame.Rect(x, y, width, width)

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2, canvas.get_height() - 25))

        for n in range(len(self.discards)):
            self._draw_discards(canvas, self.discards[n], n)
            # self._draw_calls(canvas, self.calls[n], n)
        hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]
        self._draw_hand(canvas, (canvas.get_width() / 2, 7 * canvas.get_height() / 8), hand_tiles, 22)
        scores = [72300, 8200, 11500, 23200]
        names = ["Dave", "てつやち", "藤田プロ", "Mark"]
        ranks = ["四段", "初段", "八段", "２級"]
        self._draw_centre_console(canvas, [0, 1, 2, 3], scores, calculate_score_deltas(scores, 0),
                                  [True, False, False, True], names, ranks)

        if self.hover_tile is not None:
            # canvas.blit(self.tile_highlights[0], (self.hover_tile.x, self.hover_tile.y))
            pygame.draw.rect(canvas, self.tile_hover_colour, self.hover_tile, 3)

        time_delta_secs = int(time.time() - self.start_time_secs)  # Truncate milliseconds
        time_string = seconds_to_time_string(time_delta_secs)

        lines = [time_string, "東風戦喰速赤", "東四局二本", "オーラス"]
        self._draw_corner_text(canvas, lines)

        if self.DEBUG:  # Draw positioning lines
            # Center cross
            pygame.draw.line(canvas, (0, 0, 0), (0, centre_y), (canvas_width, centre_y))
            pygame.draw.line(canvas, (0, 0, 0), (centre_x, 0), (centre_x, canvas_height))

            # Center squares
            for n in [1.5, 3.0, 4.5]:
                width = tile_width * n
                x = centre_x - width / 2
                y = centre_y - width / 2
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(x, y, width, width), 1)
            pygame.draw.rect(canvas, (0, 0, 0), self.centre_square, 1)

            # Discard zones
            width = tile_width * 6
            height = tile_height * 3.25
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

    # Game information methods #

    def _get_discard_time(self):
        now = time.time()
        discard_time_secs = 4.0  # TODO
        return self.discard_start_secs + discard_time_secs - now

    # Drawing methods #

    def _draw_hand(self, canvas, center_pos, tiles, tsumohai=None):
        discard_time = self._get_discard_time()
        if discard_time is not None:
            time_string = "{0:.2f}".format(discard_time)
            discard_timer_text = self.discard_timer_font.render(time_string, 1, (255, 255, 255))
        centre_x, centre_y = center_pos
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        total_width = tile_width * len(tiles)
        x = centre_x - (total_width / 2)
        y = canvas.get_height() - tile_height - 30
        for tile in tiles:
            self._draw_tile(canvas, tile, (x, y))
            x += tile_width
        if tsumohai is not None:
            x += 0.5 * tile_width
            self._draw_tile(canvas, tsumohai, (x, y))
            if discard_timer_text is not None:
                canvas.blit(discard_timer_text, (x - discard_timer_text.get_width() / 2 + tile_width / 2, y - 13))

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
            rotation = [0, -90, -180, -270][position]
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
        centre_x = canvas.get_width() / 2
        centre_y = canvas.get_height() / 2
        discard_offset = tile_height * 3.25
        for tile in tiles:

            x = centre_x + (x_count - 3) * tile_width
            y = centre_y + discard_offset + y_count * tile_height
            rotation = [0, -90, -180, -270][position]
            # Positioning hacks
            if position in [1, 2]:
                x += tile_width
            if position in [2, 3]:
                y += tile_height
            # Rotate into place
            pos = rotate((centre_x, centre_y), (x, y), rotation)
            self._draw_tile(canvas, tile, pos, True, rotation)
            x_count += 1
            if x_count == 6 and y_count < 2:
                x_count = 0
                y_count += 1

    def _draw_corner_text(self, canvas, lines):
        canvas_width = canvas.get_width()
        y_offset = 20
        x_offset = y = 2 * y_offset
        for line in lines:
            text = self.corner_font.render(line, 1, (0, 0, 0))
            x = canvas_width - text.get_width() - x_offset
            canvas.blit(text, (x, y))
            y += y_offset

    def _draw_centre_console(self, canvas, positions, scores, score_deltas, riichi_states, names, ranks):
        centre_x = canvas.get_width() / 2
        centre_y = canvas.get_height() / 2
        tile_img = self._get_tile_image(0, True)
        tile_width = tile_img.get_width()
        tile_height = tile_img.get_height()
        wind_offset = tile_height * 1.20
        score_offset = tile_height * 2.15
        name_offset = score_offset + 20
        riichi_offset = tile_height * 3.00

        for idx in range(len(positions)):
            if self.centre_hover:
                score_text = self.score_font.render(str(score_deltas[idx]), 1, (0, 0, 0))
            else:
                score_text = self.score_font.render(str(scores[idx]), 1, (0, 0, 0))
            name_text = self.name_font.render("{0}・{1}".format(names[idx], ranks[idx]), 1, (0, 0, 0))
            wind_sprite = self.wind_sprites[positions[idx]]
            riichi_sprite = self.riichi_stick_sprite
            if positions[idx] == 0:  # Self
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y + wind_offset - wind_sprite.get_height() / 2
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y + score_offset - score_text.get_height() / 2
                name_x = centre_x - name_text.get_width() / 2
                name_y = centre_y + name_offset - name_text.get_height() / 2
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y + riichi_offset - riichi_sprite.get_height() / 2
            if positions[idx] == 1:  # Shimocha
                wind_sprite = pygame.transform.rotate(wind_sprite, 90)
                wind_x = centre_x + wind_offset - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, 90)
                score_x = centre_x + score_offset - score_text.get_width() / 2
                score_y = centre_y - score_text.get_height() / 2
                name_text = pygame.transform.rotate(name_text, 90)
                name_x = centre_x + name_offset - name_text.get_width() / 2
                name_y = centre_y - name_text.get_height() / 2
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
                name_text = pygame.transform.rotate(name_text, 180)
                name_x = centre_x - name_text.get_width() / 2
                name_y = centre_y - name_offset - name_text.get_height() / 2
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
                name_text = pygame.transform.rotate(name_text, -90)
                name_x = centre_x - name_offset - name_text.get_width() / 2
                name_y = centre_y - name_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, -90)
                riichi_x = centre_x - riichi_offset - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_sprite.get_height() / 2

            canvas.blit(wind_sprite, (wind_x, wind_y))
            canvas.blit(score_text, (score_x, score_y))
            canvas.blit(name_text, (name_x, name_y))
            if riichi_states[idx]:
                canvas.blit(riichi_sprite, (riichi_x, riichi_y))
            centre_text_line0 = self.centre_font.render("東四局", 1, (0, 0, 0))
            centre_text_line1 = self.centre_font.render("二本場", 1, (0, 0, 0))
            canvas.blit(centre_text_line0,
                        (centre_x - centre_text_line0.get_width() / 2, centre_y - centre_text_line0.get_height()))
            canvas.blit(centre_text_line1, (centre_x - centre_text_line1.get_width() / 2, centre_y))
