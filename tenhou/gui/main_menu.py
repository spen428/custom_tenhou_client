import os

import pygame

import tenhou.gui.main


class Button(object):
    def __init__(self, text, on_click=None):
        self.text = text
        self.on_click = on_click
        self.hover = False
        self.rect = None


class _Status(object):
    NOT_LOGGED_IN = 0
    LOGGING_IN = 1
    LOGGED_IN = 2


class MainMenu(object):
    def __init__(self, client):
        self.client = client
        self.tenhou_logo = pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "tenhou-logo.png"))
        self.login_buttons = [Button("Log in", self._log_in), Button("Play anonymously", self._play_anonymously),
                              Button("Open replay", self._open_replay), Button("Exit game", self._exit_game),
                              Button("InGameUi Test", self._ui_test)]
        self.lobby_buttons = [Button("Join lobby", self._join_lobby),
                              Button("Log out", self._log_out)]
        self.status = _Status.NOT_LOGGED_IN

    def _exit_game(self):
        self.client.running = False

    def _ui_test(self):
        self.client.ui_test()

    def _log_in(self):
        pass

    def _open_replay(self):
        pass

    def _log_out(self):
        if self.client.log_out():
            self.status = _Status.NOT_LOGGED_IN

    def _join_lobby(self):
        self.client.join_lobby()

    def _play_anonymously(self):
        self.status = _Status.LOGGING_IN
        if self.client.log_in():
            self.status = _Status.LOGGED_IN
        else:
            self.status = _Status.NOT_LOGGED_IN

    def on_mouse_up(self):
        pos = pygame.mouse.get_pos()
        for btn in self._get_buttons():
            if btn.rect is not None and btn.rect.collidepoint(pos):
                if btn.on_click is not None:
                    btn.on_click()

    def on_mouse_motion(self):
        pos = pygame.mouse.get_pos()
        for btn in self._get_buttons():
            btn.hover = False
            if btn.rect is not None and btn.rect.collidepoint(pos):
                btn.hover = True

    def _get_buttons(self):
        if self.status in [_Status.NOT_LOGGED_IN, _Status.LOGGING_IN]:
            return self.login_buttons
        elif self.status is _Status.LOGGED_IN:
            return self.lobby_buttons

    def draw_to_canvas(self, canvas):
        # draw title
        x = canvas.get_width() / 2 - self.tenhou_logo.get_width() / 2
        y = 25
        canvas.blit(self.tenhou_logo, (x, y))

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2,
                                  canvas.get_height() - 25))

        # draw buttons
        btn_color_normal = (255, 255, 255)
        btn_color_hover = (255, 255, 100)
        btn_width = 200
        btn_height = 50
        num_btns = len(self._get_buttons())
        v_spacing = 25
        x = canvas.get_width() / 2 - btn_width / 2
        y = canvas.get_height() / 2 - (num_btns * (btn_height + v_spacing)) / 2
        btn_font = pygame.font.SysFont("Arial", 16)
        for btn in self._get_buttons():
            btn_color = btn_color_hover if btn.hover else btn_color_normal
            rect = pygame.draw.rect(canvas, btn_color, (x, y, btn_width, btn_height), 0)
            btn.rect = rect
            btn_label = btn_font.render(btn.text, 1, (0, 0, 0))
            bx = x + (btn_width / 2 - btn_label.get_width() / 2)
            by = y + (btn_height / 2 - btn_label.get_height() / 2)
            canvas.blit(btn_label, (bx, by))
            y += v_spacing + btn_height
