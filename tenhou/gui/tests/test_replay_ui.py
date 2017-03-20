import logging
import os

import pygame

from tenhou.events import GameEvents
from tenhou.gui import get_resource_dir
from tenhou.gui.screens.replay_ui import ReplayScreen

logger = logging.getLogger('tenhou')


class TestReplayScreen(ReplayScreen):
    def __init__(self, client):
        super().__init__(client)
        logger.setLevel(logging.INFO)
        self.autoplay = False
        self.last_autoplay = 0
        self.autoplay_delay_secs = 0.01
        self.replays = []
        self.replayidx = 0
        with open(os.path.join(get_resource_dir(), "replays", "replaylist.txt"), 'r') as f:
            self.replays = [line.strip() for line in f.readlines()]

    def on_game_event(self, event):
        """Overrides InGameScreen.on_game_event() to add replay-specific functionality.

        :return: True if the event was handled, else False
        """
        handled = super().on_game_event(event)
        if handled:
            return True

        if event.game_event == GameEvents.END_OF_REPLAY:
            self.autoplay = False
            self._load_next_replay()
            return True
        return False

    def draw_to_canvas(self, canvas):
        """Overrides InGameScreen.draw_to_canvas()"""
        super().draw_to_canvas(canvas)
        font = pygame.font.SysFont("Arial", 13)
        text = font.render("Replay Viewer Test", 1, (0, 0, 0))
        canvas.blit(text, (0, 0))

    def _load_next_replay(self):
        path = os.path.join(get_resource_dir(), "replays", self.replays[self.replayidx])
        self.replayidx += 1
        self.client.game_manager.load_replay(path)
        self.autoplay = True
