import os

import pygame

import tenhou.gui.main
from tenhou.gui.screens import AbstractScreen, MenuButton


class EscMenuScreen(AbstractScreen):
    def __init__(self, client):
        self.client = client
        self.logo_image = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tenhou-logo.png"))
        self.menu_buttons = [MenuButton("Leave game", self._nop)]
        # Constant render stuff
        self._button_font = pygame.font.SysFont("Arial", 16)
        self._button_width_px = 200
        self._button_height_px = 50
        self._button_color_normal = (255, 255, 255)  # White
        self._button_color_hover = (255, 255, 100)  # Pale yellow

    # Private Methods #

    def _nop(self):
        pass

    # Superclass methods #

    def on_mouse_up(self):
        pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            if btn.rect is not None and btn.rect.collidepoint(pos):
                if btn.on_click is not None:
                    btn.on_click()

    def on_mouse_motion(self):
        pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            btn.hover = False
            if btn.rect is not None and btn.rect.collidepoint(pos):
                btn.hover = True

    def on_window_resized(self):
        pass

    def draw_to_canvas(self, canvas):
        # draw logo
        x = canvas.get_width() / 2 - self.logo_image.get_width() / 2
        y = 25
        canvas.blit(self.logo_image, (x, y))

        # draw buttons
        num_buttons = len(self.menu_buttons)
        btn_v_spacing = 25
        x = canvas.get_width() / 2 - self._button_width_px / 2
        y = canvas.get_height() / 2 - (num_buttons * (self._button_height_px + btn_v_spacing)) / 2
        for btn in self.menu_buttons:
            # determine button colour
            if btn.hover:
                btn_color = self._button_color_hover
            else:
                btn_color = self._button_color_normal
            # draw rectangle
            btn.rect = pygame.draw.rect(canvas, btn_color, (x, y, self._button_width_px, self._button_height_px), 0)
            # draw label
            btn_label = self._button_font.render(btn.text, 1, (0, 0, 0))
            label_x = x + (self._button_width_px / 2 - btn_label.get_width() / 2)
            label_y = y + (self._button_height_px / 2 - btn_label.get_height() / 2)
            canvas.blit(btn_label, (label_x, label_y))
            y += btn_v_spacing + self._button_height_px