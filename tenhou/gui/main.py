# -*- coding: utf-8 -*-

import os
import socket

import pygame

from tenhou.client import TenhouClient
from tenhou.gui.screens.in_game_ui import InGameScreen
from tenhou.gui.screens.main_menu import MainMenuScreen
from utils.settings_handler import settings


def get_resource_dir():
    return os.path.join("tenhou", "gui", "resources")


class Gui(object):
    def __init__(self, width=1280, height=720, framerate_limit=2000, resizable=True):
        pygame.init()
        self.tenhou = None
        if resizable:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.HWACCEL)
        else:
            self.screen = pygame.display.set_mode((width, height))
        self.canvas = self._create_canvas()
        self.clock = pygame.time.Clock()
        self.framerate_limit = framerate_limit
        self.current_screen = MainMenuScreen(self)
        self.running = False

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
                elif event.type == pygame.KEYDOWN:
                    self.current_screen.on_key_down(event)
                elif event.type == pygame.KEYUP:
                    self.current_screen.on_key_up(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.current_screen.on_mouse_down(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.current_screen.on_mouse_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.current_screen.on_mouse_motion(event)
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.canvas = self._create_canvas()
                    self.current_screen.on_window_resized(event)

            # Print framerate and playtime in titlebar.
            text = "Lykat's custom Tenhou client | FPS: {0:.2f}".format(self.clock.get_fps())
            pygame.display.set_caption(text)

            # Draw game
            self.canvas.fill((58, 92, 182))
            self.current_screen.draw_to_canvas(self.canvas)

            # Update Pygame display.
            # self.canvas = self.canvas.convert()
            self.screen.blit(self.canvas, (0, 0))
            pygame.display.flip()

        # Finish Pygame.
        if self.tenhou is not None:
            self.tenhou.end_game()
        pygame.quit()

    def log_in(self):
        if self.tenhou is not None:
            return False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((settings.TENHOU_HOST, settings.TENHOU_PORT))
        self.tenhou = TenhouClient(s)
        success = self.tenhou.authenticate()
        if success:
            print("Successfully logged in as {0}".format(settings.USER_ID))
        else:
            print("Authentication failure")
        return success

    def log_out(self):
        self.tenhou.end_game()
        self.tenhou = None
        return True

    def join_lobby(self):
        pass

    def start_game(self):
        pass

    def leave_game(self):
        self.current_screen = MainMenuScreen(self)

    def ui_test(self):
        self.current_screen = InGameScreen(self)
