import os

import pygame

import tenhou.gui.main
import tenhou.gui.main

class InGameUi(object):
    def __init__(self, client):
        self.client = client
        # Load tile images
        self.tiles = []
        # numbered
        for suit in ["bamboo", "man", "pin"]:
            for number in range(1, 10):
                name = "{}{}.png".format(suit, number)
                img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", name))
                self.tiles.append(img)
        # winds
        for wind in ["east", "south", "west", "north"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "wind-" + wind + ".png"))
            self.tiles.append(img)
        # dragons
        for dragon in ["chun", "haku", "hatsu"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "dragon-" + dragon + ".png"))
            self.tiles.append(img)
        # red fives
        for suit in ["bamboo", "man", "pin"]:
            img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "red-dora-" + suit + "5.png"))
            self.tiles.append(img)
        img = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tiles_64", "face-down.png"))
        self.tiles.append(img)

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def _draw_hand(self, canvas, tiles, cx, cy):
        tile_width = self.tiles[0].get_width()
        tile_height = self.tiles[0].get_height()
        total_width = tile_width * len(tiles)
        x = cx - (total_width / 2)
        y = cy - (tile_height / 2)
        for tile in tiles:
            canvas.blit(self.tiles[tile], (x, y))
            x += tile_width

    def draw_to_canvas(self, canvas):
        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2,
                                  canvas.get_height() - 25))

        # tile test
        x = 0
        y = 0
        for tile_img in self.tiles:
            canvas.blit(tile_img, (x, y))
            x += 64
            if x == 64 * 6:
                x = 0
                y += 64

        hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]
        self._draw_hand(canvas, hand_tiles, canvas.get_width() / 2, 3 * canvas.get_height() / 4)

