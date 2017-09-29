# -*- coding: utf-8 -*-

import logging
import os

import pygame

from tenhou.game_client import GameClient
from tenhou.client_async import TenhouClient
from tenhou.events import UIEVENT, UiEvents, UiEvent
from tenhou.gui import get_resource_dir
from tenhou.gui.screens import AbstractScreen
from tenhou.gui.screens.in_game_ui import InGameScreen
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
        self.main_menu = MainMenuScreen()
        self.in_game_screen = InGameScreen()
        self.current_screen: AbstractScreen = self.main_menu
        self.replay_client: ReplayClient = None
        self.game_client: GameClient = GameClient()
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
                if self.replay_client is not None:
                    self.replay_client.on_event(event)
                if self.game_client is not None:
                    self.game_client.on_event(event)

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
            def _end_game_callback():
                pygame.quit()
            self.game_manager.end_game(_end_game_callback)

    def on_ui_event(self, event):
        if event.ui_event == UiEvents.LOG_IN:
            self._log_in(event.user_id)
        elif event.ui_event == UiEvents.LOG_OUT:
            self._log_out()
        elif event.ui_event == UiEvents.CANCEL_LOGIN:
            self._cancel_login()
        elif event.ui_event == UiEvents.LEAVE_GAME:
            self._leave_game()
        elif event.ui_event == UiEvents.EXIT_GAME:
            self.running = False
        elif event.ui_event == UiEvents.OPEN_REPLAY:
            self._load_replay(event.file_path)
        elif event.ui_event == UiEvents.JOIN_GAME:
            self._join_game(event.lobby, event.game_type_id)
        elif event.ui_event == UiEvents.TEST_INGAMEUI:
            self._ingameui_test()
        elif event.ui_event == UiEvents.TEST_REPLAY:
            self._replay_test()
        elif event.ui_event == UiEvents.TEST_LG:
            self._lg_test()
        elif event.ui_event == UiEvents.TEST_LGR:
            self._lgr_test()
        elif event.ui_event == UiEvents.LOGGED_IN:
            self.main_menu.set_logged_in(True)
            logging.info('Logged in')
        elif event.ui_event == UiEvents.LOGGED_OUT:
            self.main_menu.set_logged_in(False)
            logging.info('Logged out')
        elif event.ui_event == UiEvents.JOINED_GAME_QUEUE:
            logging.info('Joined game queue')
        elif event.ui_event == UiEvents.JOINED_GAME:
            self.current_screen = self.in_game_screen
            self.in_game_screen.erase_state()
            logging.info('Joined game')

    def _log_in(self, user_id):
        if self.game_manager is not None:
            return False

        # TODO: Should this be in TenhouClient?
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((settings.TENHOU_HOST, settings.TENHOU_PORT))
        self.game_manager = TenhouClient(sock)

        def _log_in_callback(success):
            if success:
                pygame.event.post(UiEvent(UiEvents.LOGGED_IN))
            else:
                pygame.event.post(UiEvent(UiEvents.LOGIN_FAILED))
        self.game_manager.authenticate(user_id, _log_in_callback)

    def _log_out(self):
        def _log_out_callback():
            self.game_manager = None
            pygame.event.post(UiEvent(UiEvents.LOGGED_OUT))
        self.game_manager.log_out(_log_out_callback)

    def _cancel_login(self):
        self.game_client.cancel_login()

    def _join_game(self, lobby, game_type_id):
        self.game_client.join_game(lobby, game_type_id)

    def _leave_game(self):
        self.game_client.leave_game()
        self.current_screen = MainMenuScreen()

    def _load_replay(self, replay_file_path, autoskip=True):
        if type(self.game_manager) is not ReplayClient:
            if type(self.game_manager) is TenhouClient:
                self.game_manager.close()
            self.game_manager = ReplayClient()
        if type(self.current_screen) is not ReplayScreen:
            self.current_screen = ReplayScreen()
        self.game_manager.load_replay(replay_file_path, autoskip)

    def _ingameui_test(self):
        self.current_screen = TestInGameScreen()

    def _replay_test(self):
        self.replay_client = ReplayClient()
        self.current_screen = TestReplayScreen()
        self.current_screen._load_next_replay()

    def _lg_test(self):
        path = os.path.join(get_resource_dir(), 'live_game', 'gamelog.thr')
        self._load_replay(path, autoskip=False)

    def _lgr_test(self):
        path = os.path.join(get_resource_dir(), 'live_game', 'replay.thr')
        self._load_replay(path)
