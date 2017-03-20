import time

import pygame

from tenhou.events import GameEvents, GameEvent
from tenhou.gui.screens.in_game_ui import InGameScreen


class ReplayScreen(InGameScreen):
    def __init__(self, client):
        super().__init__(client)
        self.autoplay = False
        self.last_autoplay = 0
        self.autoplay_delay_secs = 0.01

    def on_key_up(self, event):
        handled = super().on_key_up(event)
        if handled:
            return True
        if event.key == pygame.K_s:
            pygame.event.post(GameEvent(GameEvents.CALL_STEP_FORWARD))
        elif event.key == pygame.K_a:
            pygame.event.post(GameEvent(GameEvents.CALL_STEP_BACKWARD))
        elif event.key == pygame.K_d:
            self.autoplay = not self.autoplay
        elif event.key == pygame.K_r:
            self.client.game_manager.reload_replay()
        return False

    def on_game_event(self, event):
        """Overrides InGameScreen.on_game_event() to add replay-specific functionality.

        :return: True if the event was handled, else False
        """
        handled = super().on_game_event(event)
        if handled:
            return True

        if event.game_event == GameEvents.END_OF_REPLAY:
            self.autoplay = False
            return True
        return False

    def draw_to_canvas(self, canvas):
        """Overrides InGameScreen.draw_to_canvas()"""
        super().draw_to_canvas(canvas)
        font = pygame.font.SysFont("Arial", 13)
        text = font.render("Replay Viewer: Press S to step forward, D to toggle autostep, R to restart replay", 1,
                           (0, 0, 0))
        canvas.blit(text, (canvas.get_width() / 2 - text.get_width() / 2, 10))

        if not self.is_esc_menu_open and self.autoplay and self.last_autoplay + self.autoplay_delay_secs < time.time():
            self.last_autoplay = time.time()
            pygame.event.post(GameEvent(GameEvents.CALL_STEP_FORWARD))
