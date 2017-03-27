# -*- coding: utf-8 -*-
import logging

import pygame

from tenhou.decoder import TenhouDecoder
from tenhou.events import GameEvents, GameEvent, GAMEEVENT, UIEVENT, UiEvents
from tenhou.gui.screens import EventListener

logger = logging.getLogger('tenhou')


class ReplayClient(EventListener):
    TENHOU_LOG_URLS = ['http://e.mjv.jp/0/log/?', 'http://ee.mjv.jp/0/log/?', 'http://ff.mjv.jp/0/log/?']

    def __init__(self, replay_file_path=None):
        self.decoder = TenhouDecoder()
        self.current_line_idx = 0
        self.lines = []
        self.current_replay = None
        if replay_file_path is not None:
            self.load_replay(replay_file_path)

    def _erase_state(self):
        self.current_line_idx = 0
        self.lines.clear()
        self.current_replay = None

    def reload_replay(self):
        if self.current_replay is not None:
            self.load_replay(self.current_replay)

    def load_replay(self, replay_file_path, autoskip=True):
        """Load a replay file for viewing.

        :param replay_file_path: The path to the replay file
        :param autoskip: Whether to step past all of the game initialisation steps automatically
        :return: None
        """
        self._erase_state()
        self.current_replay = replay_file_path
        logger.info('Loading replay file: ' + replay_file_path)
        with open(replay_file_path, 'r') as f:
            tmp_lines = [line.strip() for line in f.readlines()]
            for line in tmp_lines:
                # Ensure there is only one tag per line
                sep_lines = line.replace('><', '>\n<').split('\n')
                # Add lines to list
                self.lines.extend(sep_lines)
        if autoskip:
            self.step(5)

    def step(self, steps=1):
        """
        Step the replay forward, causing an event to be posted.

        :param steps: number of steps to advance
        :return: True if the next game event was successfully posted, else False if the current line of the replay
        could not be parsed into an event.
        """
        if steps < 0:
            return False
        if self.end_of_replay():
            pygame.event.post(GameEvent(GameEvents.END_OF_REPLAY))
            return False
        elif self.current_line_idx + steps >= len(self.lines) - 1:
            steps = len(self.lines) - 1 - self.current_line_idx

        while steps > 0:
            self.current_line_idx += 1
            message = self.lines[self.current_line_idx]
            event = self.decoder.message_to_event(message)
            if event is not None:
                pygame.event.post(event)
            steps -= 1
        return True

    def end_of_replay(self) -> bool:
        return self.current_line_idx >= len(self.lines) - 1

    def end_game(self):
        pass  # Required for gui -> self.game_manager.end_game() call

    # Event methods #

    def on_event(self, event):
        if event.type == GAMEEVENT:
            self.on_game_event(event)
        elif event.type == UIEVENT:
            if event.ui_event == UiEvents.RELOAD_REPLAY:
                self.reload_replay()

    def on_game_event(self, event):
        if event.game_event == GameEvents.CALL_STEP_FORWARD:
            self.step(1)
        elif event.game_event == GameEvents.CALL_STEP_BACKWARD:
            raise NotImplementedError()  # Not currently supported, as it messes up the Table state
