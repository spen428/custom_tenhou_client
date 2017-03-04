# -*- coding: utf-8 -*-

import os
import socket

import pygame

from tenhou.client import TenhouClient
from tenhou.gui.screens.in_game_ui import InGameAbstractScreen
from tenhou.gui.screens.main_menu import MainMenuAbstractScreen
from utils.settings_handler import settings


def get_resource_dir():
    return os.path.join("tenhou", "gui", "resources")


class Gui(object):
    def __init__(self, width=1280, height=720, framerate_limit=2000, resizable=True):
        pygame.init()
        self.tenhou = None
        if resizable:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode((width, height))
        self.canvas = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()
        self.framerate_limit = framerate_limit
        self.current_screen = MainMenuAbstractScreen(self)
        self.running = False

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
                    pass
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.on_mouse_up()
                elif event.type == pygame.MOUSEMOTION:
                    self.on_mouse_motion()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.canvas = pygame.Surface(self.screen.get_size())
                    self.on_window_resized()

            # Print framerate and playtime in titlebar.
            text = "Dave's Tenhou client | FPS: {0:.2f}".format(self.clock.get_fps())
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

    def on_mouse_up(self):
        self.current_screen.on_mouse_up()

    def on_mouse_motion(self):
        self.current_screen.on_mouse_motion()

    def on_window_resized(self):
        self.current_screen.on_window_resized()

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

    def ui_test(self):
        self.current_screen = InGameAbstractScreen(self)
