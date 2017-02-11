import os

import pygame

import tenhou.gui.main
import tenhou.gui.main
from random import randint


class InGameUi(object):
    def __init__(self, client):
        self.client = client
        # Load tile images
        self.tile_images = []
        # numbered
        for suit in ["bamboo", "man", "pin"]:
            for number in range(1, 10):
                name = "{}{}.png".format(suit, number)
                img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", name))
                self.tile_images.append(img)
        # winds
        for wind in ["east", "south", "west", "north"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "wind-" + wind + ".png"))
            self.tile_images.append(img)
        # dragons
        for dragon in ["chun", "haku", "hatsu"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "dragon-" + dragon + ".png"))
            self.tile_images.append(img)
        # red fives
        for suit in ["bamboo", "man", "pin"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "red-dora-" + suit + "5.png"))
            self.tile_images.append(img)
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "face-down.png"))
        self.tile_images.append(img)
        self.discards = [[randint(0, len(self.tile_images) - 1) for _ in range(18)] for _ in range(4)]
        self.tile_rects = []

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def _get_tile_image(self, tile_id):
        return self.tile_images[tile_id]

    def _draw_hand(self, canvas, tiles, cx, cy):
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        total_width = tile_width * len(tiles)
        x = cx - (total_width / 2)
        y = cy - (tile_height / 2)
        for tile in tiles:
            self._draw_tile(canvas, tile, x, y)
            x += tile_width

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
        hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]
        self._draw_hand(canvas, hand_tiles, canvas.get_width() / 2, 7 * canvas.get_height() / 8)

    def _draw_tile(self, canvas, tile_id, x, y):
        tile_image = self._get_tile_image(tile_id)
        canvas.blit(tile_image, (x, y))
        self.tile_rects.append(pygame.Rect(x, y, tile_image.get_width(), tile_image.get_height()))

    def _draw_discards(self, canvas, tiles, position):
        x_count = 0
        y_count = 0
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        for tile in tiles:
            if position == 0:
                x = canvas.get_width() / 2 - tile_width * 6 / 2
                y = 2 * canvas.get_height() / 3 - tile_height * 3 / 2
            elif position == 1:
                x = 7 * canvas.get_width() / 8 - tile_width * 6 / 2
                y = canvas.get_height() / 2 - tile_height * 3 / 2
            elif position == 2:
                x = canvas.get_width() / 2 - tile_width * 6 / 2
                y = 1 * canvas.get_height() / 4 - tile_height * 3 / 2
            elif position == 3:
                x = 1 * canvas.get_width() / 8 - tile_width * 6 / 2
                y = canvas.get_height() / 2 - tile_height * 3 / 2
            else:
                raise ValueError("Position must be 0-3")
            x += x_count * tile_width
            y += y_count * tile_height
            self._draw_tile(canvas, tile, x, y)
            x_count += 1
            if x_count == 6:
                x_count = 0
                y_count += 1

