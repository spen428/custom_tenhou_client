# -*- coding: utf-8 -*-
import logging

import pygame

from tenhou.decoder import TenhouDecoder

logger = logging.getLogger('replay')


class ReplayClient(object):
    def __init__(self, replay_file_path):
        self.decoder = TenhouDecoder()
        self.current_line_idx = 0
        self.lines = []
        with open(replay_file_path, 'r') as f:
            tmp_lines = [line.strip() for line in f.readlines()]
            for line in tmp_lines:
                # Ensure there is only one tag per line
                sep_line = line.replace('><', '>\n<')
                # Add lines to list
                self.lines.extend(sep_line.split('\n'))

    def step(self):
        """
        Step the replay forward, causing an event to be posted.
        :return: True if the next game event was successfully posted, else False if the current line of the replay
        could not be parsed into an event.
        """
        if self.end_of_replay():
            return False

        self.current_line_idx += 1
        message = self.lines[self.current_line_idx]
        event = self.decoder.message_to_event(message)
        if event is not None:
            pygame.event.post(event)
            return True

    def end_of_replay(self):
        return self.current_line_idx >= len(self.lines) - 1
