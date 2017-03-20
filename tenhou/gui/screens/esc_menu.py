import os

import pygame

import tenhou.gui.gui
from tenhou.events import GAME_EVENT
from tenhou.gui.screens import AbstractScreen, MenuButton, EventListener


class EscMenuScreen(AbstractScreen, EventListener):
    def __init__(self, parent):
        self.parent = parent
        self.logo_image = pygame.image.load(os.path.join(tenhou.gui.gui.get_resource_dir(), "tenhou-logo.png"))
        self.menu_buttons = [MenuButton("NOP", self._nop), MenuButton("NOP", self._nop), MenuButton("NOP", self._nop),
                             MenuButton("NOP", self._nop), MenuButton("Leave game", self._leave_game)]
        # Constant render stuff
        self._button_font = pygame.font.SysFont("Arial", 16)
        self._button_width_px = 200
        self._button_height_px = 50
        self._button_color_normal = (255, 255, 255)  # White
        self._button_color_hover = (255, 255, 100)  # Pale yellow

    # Private Methods #

    def _nop(self):
        pass

    def _leave_game(self):
        self.parent.leave_game()

    # Event methods #

    def on_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.on_key_down(event)
        elif event.type == pygame.KEYUP:
            self.on_key_up(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.on_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            self.on_mouse_motion(event)
        elif event.type == pygame.VIDEORESIZE:
            self.on_window_resized(event)
        elif event.type == GAME_EVENT:
            self.on_game_event(event)

    def on_key_down(self, event):
        pass

    def on_key_up(self, event):
        pass

    def on_mouse_down(self, event):
        pass

    def on_mouse_up(self, event):
        pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            if btn.rect is not None and btn.rect.collidepoint(pos):
                if callable(btn.on_click):
                    btn.on_click()

    def on_mouse_motion(self, event):
        pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            btn.hover = False
            if btn.rect is not None and btn.rect.collidepoint(pos):
                btn.hover = True

    def on_window_resized(self, event):
        pass

    def on_game_event(self, event):
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
