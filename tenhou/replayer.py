# -*- coding: utf-8 -*-
import logging

import pygame

from mahjong.table import Table
from tenhou.decoder import TenhouDecoder
from tenhou.events import GameEvents
from tenhou.gui.screens import EventListener

logger = logging.getLogger('tenhou')


class ReplayClient(EventListener):
    def __init__(self, replay_file_path):
        self.table = Table()
        self.decoder = TenhouDecoder()
        self.current_line_idx = 0
        self.lines = []
        logger.debug('Began reading replay file')
        with open(replay_file_path, 'r') as f:
            tmp_lines = [line.strip() for line in f.readlines()]
            for line in tmp_lines:
                # Ensure there is only one tag per line
                sep_lines = line.replace('><', '>\n<').split('\n')
                # Add lines to list
                logger.debug(sep_lines)
                self.lines.extend(sep_lines)

    def step(self, steps=1):
        """
        Step the replay forward, causing an event to be posted.
        :arg steps: number of steps to advance, can be negative.
        :return: True if the next game event was successfully posted, else False if the current line of the replay
        could not be parsed into an event.
        """
        if self.end_of_replay():
            return False
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

    def end_of_replay(self):
        return self.current_line_idx >= len(self.lines) - 1

    # Event methods #

    def on_event(self, event):
        if event.type == pygame.USEREVENT:
            self.on_user_event(event)

    def on_user_event(self, event):
        if event.game_event == GameEvents.CALL_STEP_FORWARD:
            self.step(1)
        elif event.game_event == GameEvents.CALL_STEP_BACKWARD:
            pass # TODO: Not currently supported, as it messes up the Table state
