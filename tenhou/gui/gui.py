# -*- coding: utf-8 -*-

import os
import socket

import logging
import pygame

from tenhou.client import TenhouClient
from tenhou.gui.screens.in_game_ui import InGameScreen
from tenhou.gui.screens.main_menu import MainMenuScreen
from tenhou.replayer import ReplayClient
from utils.settings_handler import settings

logger = logging.getLogger('tenhou')


def get_resource_dir():
    return os.path.join("tenhou", "gui", "resources")


class Gui(object):
    def __init__(self, width=1280, height=720, framerate_limit=2000, resizable=True):
        pygame.init()
        display_flags = (pygame.RESIZABLE | pygame.HWACCEL) if resizable else 0
        self.version_str: str = "v0.81 Alpha"
        self.screen: pygame.Surface = pygame.display.set_mode((width, height), display_flags)
        self.canvas: pygame.Surface = self._create_canvas()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.framerate_limit: int = framerate_limit
        self.current_screen = MainMenuScreen(self)
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

    def log_in(self):
        if self.game_manager is not None:
            return False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((settings.TENHOU_HOST, settings.TENHOU_PORT))
        self.game_manager = TenhouClient(s)
        success = self.game_manager.authenticate()
        if success:
            print("Successfully logged in as {0}".format(settings.USER_ID))
        else:
            print("Authentication failure")
        return success

    def log_out(self):
        self.game_manager.end_game()
        self.game_manager = None
        return True

    def join_lobby(self):
        pass

    def start_game(self):
        pass

    def load_replay(self):
        pass

    def leave_game(self):
        self.current_screen = MainMenuScreen(self)

    def ui_test(self):
        self.current_screen = InGameScreen(self)

    def replay_test(self):
        test_replay_path = os.path.join(get_resource_dir(), "2017010100gm-00a9-0000-2d7e1616.thr")
        self.game_manager = ReplayClient(test_replay_path)
        self.current_screen = InGameScreen(self)
