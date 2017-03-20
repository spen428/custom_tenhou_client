# -*- coding: utf-8 -*-
import logging

import pygame

from tenhou.decoder import TenhouDecoder
from tenhou.events import GameEvents, GameEvent
from tenhou.gui.screens import EventListener

logger = logging.getLogger('tenhou')


class ReplayClient(EventListener):
    def __init__(self, replay_file_path=None):
        self.decoder = TenhouDecoder()
        self.current_line_idx = 0
        self.lines = []
        if replay_file_path is not None:
            self.load_replay(replay_file_path)

    def _erase_state(self):
        self.current_line_idx = 0
        self.lines.clear()

    def load_replay(self, replay_file_path):
        self._erase_state()
        logger.debug('Loading replay file: ' + replay_file_path)
        with open(replay_file_path, 'r') as f:  # TODO: Verify replay
            tmp_lines = [line.strip() for line in f.readlines()]
            for line in tmp_lines:
                # Ensure there is only one tag per line
                sep_lines = line.replace('><', '>\n<').split('\n')
                # Add lines to list
                self.lines.extend(sep_lines)

    def step(self, steps=1):
        """
        Step the replay forward, causing an event to be posted.

        :param steps: number of steps to advance, can be negative.
        :return: True if the next game event was successfully posted, else False if the current line of the replay
        could not be parsed into an event.
        """
        if self.end_of_replay():
            return pygame.event.post(GameEvent(GameEvents.END_OF_REPLAY))
        elif self.current_line_idx + steps >= len(self.lines) - 1:
            self.current_line_idx = len(self.lines) - 1
        elif self.current_line_idx + steps < 0:
            self.current_line_idx = 0
        else:
            self.current_line_idx += steps

        message = self.lines[self.current_line_idx]
        event = self.decoder.message_to_event(message)
        if event is not None:
            pygame.event.post(event)
            return True

    def end_of_replay(self) -> bool:
        return self.current_line_idx >= len(self.lines) - 1

    def end_game(self):
        pass  # Required for gui -> self.game_manager.end_game() call

    # Event methods #

    def on_event(self, event):
        if event.type == pygame.USEREVENT:
            self.on_user_event(event)

    def on_user_event(self, event):
        if event.game_event == GameEvents.CALL_STEP_FORWARD:
            self.step(1)
        elif event.game_event == GameEvents.CALL_STEP_BACKWARD:
            pass  # TODO: Not currently supported, as it messes up the Table state
