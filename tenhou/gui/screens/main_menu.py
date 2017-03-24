import os
from enum import Enum
from tkinter.filedialog import askopenfilename, Tk

import pygame

import tenhou.gui
import tenhou.gui.gui
from tenhou.events import GAMEEVENT, UiEvent, UiEvents, UIEVENT
from tenhou.gui.screens import AbstractScreen, MenuButton, EventListener


class LoginStatus(Enum):
    NOT_LOGGED_IN = 0
    LOGGING_IN = 1
    LOGGED_IN = 2


class MainMenuScreen(AbstractScreen, EventListener):
    def __init__(self):
        self.logo_image = pygame.image.load(os.path.join(tenhou.gui.get_resource_dir(), "tenhou-logo.png"))
        self.login_buttons = [MenuButton("Log in", self._log_in),
                              MenuButton("Play anonymously", self._play_anonymously),
                              MenuButton("Open replay", self._open_replay), MenuButton("Exit game", self._exit_game),
                              MenuButton("Test In-Game UI", self._test_in_game_ui),
                              MenuButton("Test Replay Viewer", self._test_replay_viewer),
                              MenuButton("Test Live Game", self._test_lg),
                              MenuButton("Test Live Game Replay", self._test_lgr)]
        self.lobby_buttons = [MenuButton("Join lobby", self._join_lobby), MenuButton("Log out", self._log_out)]
        self.status: LoginStatus = LoginStatus.NOT_LOGGED_IN
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
        pygame.event.post(UiEvent(UiEvents.EXIT_GAME))

    def _test_in_game_ui(self):
        pygame.event.post(UiEvent(UiEvents.TEST_INGAMEUI))

    def _test_replay_viewer(self):
        pygame.event.post(UiEvent(UiEvents.TEST_REPLAY))

    def _test_lg(self):
        pygame.event.post(UiEvent(UiEvents.TEST_LG))

    def _test_lgr(self):
        pygame.event.post(UiEvent(UiEvents.TEST_LGR))

    def _log_in(self):
        pass

    def _open_replay(self):
        root = Tk()
        root.withdraw()  # Make the root window invisible
        filename = askopenfilename()
        root.destroy()
        if filename == '':
            return False
        else:
            pygame.event.post(UiEvent(UiEvents.OPEN_REPLAY, {'file_path': filename}))

    def _log_out(self):
        pygame.event.post(UiEvent(UiEvents.LOG_OUT))

    def _join_lobby(self):
        pygame.event.post(UiEvent(UiEvents.JOIN_LOBBY))

    def _play_anonymously(self):
        self.status = LoginStatus.LOGGING_IN
        pygame.event.post(UiEvent(UiEvents.LOG_IN, {'user_id': 'NoName'}))

    def _get_buttons(self):
        if self.status in [LoginStatus.NOT_LOGGED_IN, LoginStatus.LOGGING_IN]:
            return self.login_buttons
        elif self.status is LoginStatus.LOGGED_IN:
            return self.lobby_buttons

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
        elif event.type == GAMEEVENT:
            self.on_game_event(event)
        elif event.type == UIEVENT:
            self.on_ui_event(event)

    def on_ui_event(self, event):
        if event.ui_event == UiEvents.LOGGED_IN:
            self.status = LoginStatus.LOGGED_IN
        elif event.ui_event in [UiEvents.LOGIN_FAILED, UiEvents.LOGGED_OUT]:
            self.status = LoginStatus.NOT_LOGGED_IN

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

    def on_game_event(self, event):
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
