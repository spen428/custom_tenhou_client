# -*- coding: utf-8 -*-

import logging
import os

import pygame

from tenhou.client_async import TenhouClient
from tenhou.events import UIEVENT, UiEvents, UiEvent, GameEvents
from tenhou.gui import get_resource_dir
from tenhou.gui.screens import AbstractScreen
from tenhou.gui.screens.main_menu import MainMenuScreen
from tenhou.gui.screens.replay_ui import ReplayScreen
from tenhou.gui.tests.test_in_game_ui import TestInGameScreen
from tenhou.gui.tests.test_replay_ui import TestReplayScreen
from tenhou.replayer import ReplayClient

logger = logging.getLogger('tenhou')


class Gui(object):
    def __init__(self, width=1280, height=720, framerate_limit=2000, resizable=True):
        pygame.init()
        display_flags = (pygame.RESIZABLE | pygame.HWACCEL) if resizable else 0
        self.version_str: str = "v1.00Alpha"
        self.screen: pygame.Surface = pygame.display.set_mode((width, height), display_flags)
        self.canvas: pygame.Surface = self._create_canvas()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.framerate_limit: int = framerate_limit
        self.current_screen: AbstractScreen = MainMenuScreen()
        self.game_manager = None
        self.running: bool = False

    def _create_canvas(self):
        canvas = pygame.Surface(self.screen.get_size(), flags=pygame.HWACCEL)
        return canvas

    def run(self):
        self.running = True

        while self.running:
            if self.framerate_limit > 0:
                # Impose framerate limit
                self.clock.tick(self.framerate_limit)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.canvas = self._create_canvas()
                elif event.type == UIEVENT:
                    self.on_ui_event(event)
                # Pass events to other listeners
                self.current_screen.on_event(event)
                if self.game_manager is not None:
                    self.game_manager.on_event(event)

            # Print framerate and playtime in titlebar.
            text = "Lykat's custom Tenhou client {0} | FPS: {1:.2f}".format(self.version_str, self.clock.get_fps())
            pygame.display.set_caption(text)

            # Draw game
            self.canvas.fill((58, 92, 182))
            self.current_screen.draw_to_canvas(self.canvas)

            # Update Pygame display.
            # self.canvas = self.canvas.convert()
            self.screen.blit(self.canvas, (0, 0))
            pygame.display.flip()

        # Finish Pygame.
        if self.game_manager is not None:
            self.game_manager.end_game()
        pygame.quit()

    def on_ui_event(self, event):
        if event.ui_event == UiEvents.LOG_OUT:
            self._log_out()
        elif event.ui_event == UiEvents.LEAVE_GAME:
            self._leave_game()
        elif event.ui_event == UiEvents.EXIT_GAME:
            self.running = False
        elif event.ui_event == UiEvents.OPEN_REPLAY:
            self._load_replay(event.file_path)
        elif event.ui_event == UiEvents.JOIN_LOBBY:
            self._join_lobby()
        elif event.ui_event == UiEvents.TEST_INGAMEUI:
            self._ingameui_test()
        elif event.ui_event == UiEvents.TEST_REPLAY:
            self._replay_test()
        elif event.ui_event == UiEvents.TEST_LG:
            self._lg_test()
        elif event.ui_event == UiEvents.TEST_LGR:
            self._lgr_test()

    def on_game_event(self, event):
        if event.game_event == GameEvents.LOGIN_REQUEST_FAILED:
            logger.error("Login request failure")
        elif event.game_event == GameEvents.RECV_AUTH_SUCCESSFUL:
            logger.info("Successfully logged in")

    def _log_in(self, user_id):
        if self.game_manager is not None:
            return False  # already logged in

        self.game_manager = TenhouClient()
        self.game_manager.log_in(user_id)

    def _log_out(self):
        self.game_manager.end_game()
        self.game_manager = None
        pygame.event.post(UiEvent(UiEvents.LOGGED_OUT))
        return True

    def _join_lobby(self):
        pass

    def _load_replay(self, replay_file_path, autoskip=True):
        if type(self.game_manager) is not ReplayClient:
            self.game_manager = ReplayClient()
        if type(self.current_screen) is not ReplayScreen:
            self.current_screen = ReplayScreen()
        self.game_manager.load_replay(replay_file_path, autoskip)

    def _leave_game(self):
        self.current_screen = MainMenuScreen()

    def _ingameui_test(self):
        self.current_screen = TestInGameScreen()

    def _replay_test(self):
        self.game_manager = ReplayClient()
        self.current_screen = TestReplayScreen()
        self.current_screen._load_next_replay()

    def _lg_test(self):
        path = os.path.join(get_resource_dir(), 'live_game', 'gamelog.thr')
        self._load_replay(path, autoskip=False)

    def _lgr_test(self):
        path = os.path.join(get_resource_dir(), 'live_game', 'replay.thr')
        self._load_replay(path)
