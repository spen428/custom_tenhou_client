import time

import pygame

from tenhou.events import GameEvents, GameEvent
from tenhou.gui.screens.in_game_ui import InGameScreen


class ReplayScreen(InGameScreen):
    def __init__(self, client):
        super().__init__(client)
        self.autoplay = False
        self.last_autoplay = 0
        self.autoplay_delay_secs = 0.1

    def on_game_event(self, event):
        """Overrides InGameScreen.on_game_event() to add replay-specific functionality.

        :return: True if the event was handled, else False
        """
        handled = super().on_game_event(event)
        if handled:
            return True

        if event.game_event == GameEvents.END_OF_REPLAY:
            self.autoplay = False
            self.client._load_next_replay()
            self.autoplay = True
            return True
        return False

    def draw_to_canvas(self, canvas):
        """Overrides InGameScreen.draw_to_canvas()"""
        super().draw_to_canvas(canvas)
        if self.autoplay and self.last_autoplay + self.autoplay_delay_secs < time.time():
            self.last_autoplay = time.time()
            pygame.event.post(GameEvent(GameEvents.CALL_STEP_FORWARD))
