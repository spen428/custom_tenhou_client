import os
from enum import Enum

import pygame

import tenhou.gui.gui
from tenhou.gui.screens import AbstractScreen, MenuButton


class LoginStatus(Enum):
    NOT_LOGGED_IN = 0
    LOGGING_IN = 1
    LOGGED_IN = 2


class MainMenuScreen(AbstractScreen):
    def __init__(self, client):
        self.client = client
        self.logo_image = pygame.image.load(os.path.join(tenhou.gui.gui.get_resource_dir(), "tenhou-logo.png"))
        self.login_buttons = [MenuButton("Log in", self._log_in),
                              MenuButton("Play anonymously", self._play_anonymously),
                              MenuButton("Open replay", self._open_replay), MenuButton("Exit game", self._exit_game),
                              MenuButton("InGameScreen Test", self._ui_test),
                              MenuButton("Replay Test", self._replay_test)]
        self.lobby_buttons = [MenuButton("Join lobby", self._join_lobby), MenuButton("Log out", self._log_out)]
        self.status: Enum = LoginStatus.NOT_LOGGED_IN
        # Constant render stuff
        self._footer_font = pygame.font.SysFont("Arial", 13)
        self._footer_text = self._footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        self._button_font = pygame.font.SysFont("Arial", 16)
        self._button_width_px = 200
        self._button_height_px = 50
        self._button_color_normal = (255, 255, 255)  # White
        self._button_color_hover = (255, 255, 100)  # Pale yellow

    # Private Methods #

    def _exit_game(self):
        self.client.running = False

    def _ui_test(self):
        self.client.ui_test()

    def _replay_test(self):
        self.client.replay_test()

    def _log_in(self):
        pass

    def _open_replay(self):
        pass

    def _log_out(self):
        if self.client.log_out():
            self.status = LoginStatus.NOT_LOGGED_IN

    def _join_lobby(self):
        self.client.join_lobby()

    def _play_anonymously(self):
        self.status = LoginStatus.LOGGING_IN
        if self.client.log_in():
            self.status = LoginStatus.LOGGED_IN
        else:
            self.status = LoginStatus.NOT_LOGGED_IN

    def _get_buttons(self):
        if self.status in [LoginStatus.NOT_LOGGED_IN, LoginStatus.LOGGING_IN]:
            return self.login_buttons
        elif self.status is LoginStatus.LOGGED_IN:
            return self.lobby_buttons

    # Superclass methods #

    def on_key_down(self, event):
        pass

    def on_key_up(self, event):
        pass

    def on_mouse_down(self, event):
        pass

    def on_mouse_up(self, event):
        pos = pygame.mouse.get_pos()
        for btn in self._get_buttons():
            if btn.rect is not None and btn.rect.collidepoint(pos):
                if callable(btn.on_click):
                    btn.on_click()

    def on_mouse_motion(self, event):
        pos = pygame.mouse.get_pos()
        for btn in self._get_buttons():
            btn.hover = False
            if btn.rect is not None and btn.rect.collidepoint(pos):
                btn.hover = True

    def on_window_resized(self, event):
        pass

    def draw_to_canvas(self, canvas):
        # draw logo
        x = canvas.get_width() / 2 - self.logo_image.get_width() / 2
        y = 25
        canvas.blit(self.logo_image, (x, y))

        # draw footer text
        x = canvas.get_width() / 2 - self._footer_text.get_width() / 2
        y = canvas.get_height() - 25
        canvas.blit(self._footer_text, (x, y))

        # draw buttons
        num_buttons = len(self._get_buttons())
        btn_v_spacing = 25
        x = canvas.get_width() / 2 - self._button_width_px / 2
        y = canvas.get_height() / 2 - (num_buttons * (self._button_height_px + btn_v_spacing)) / 2
        for btn in self._get_buttons():
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
