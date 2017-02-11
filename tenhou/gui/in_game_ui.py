import os

import pygame

import tenhou.gui.main


class InGameUi(object):
    def __init__(self, client):
        self.client = client

    def on_mouse_up(self):
        pass

    def on_mouse_motion(self):
        pass

    def draw_to_canvas(self, canvas):
        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2,
                                  canvas.get_height() - 25))

        # placeholder text
        txt = footer_font.render("IN GAME", 1, (0, 0, 0))
        canvas.blit(txt, (canvas.get_width() / 2 - txt.get_width() / 2,
                          canvas.get_height() / 2 - txt.get_height() / 2))
