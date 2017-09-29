# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from mahjong.stat import Statistics
from mahjong.table import Table
from tenhou.gui.screens import EventListener
from utils.general import make_random_letters_and_digit_string


class Client(EventListener, metaclass=ABCMeta):
    statistics = None
    id = ''
    position = 0

    def __init__(self, use_previous_ai_version=False):
        self.table = Table()
        self.statistics = Statistics()
        self.player = self.table.get_main_player()
        self.id = make_random_letters_and_digit_string()

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, user_id, is_tournament, callback):
        raise NotImplementedError

    @abstractmethod
    def start_game(self):
        raise NotImplementedError

    @abstractmethod
    def end_game(self):
        raise NotImplementedError

    def init_hand(self, tiles):
        self.player.init_hand(tiles)

    def draw_tile(self, tile_id):
        self.table.count_of_remaining_tiles -= 1
        self.player.draw_tile(tile_id)

    def discard_tile(self, tile_id):
        return self.player.discard_tile(tile_id)

    def call_meld(self, meld):
        # when opponent called meld it is means
        # that he will not get the tile from the wall
        # so, we need to compensate "-" from enemy discard method
        self.table.count_of_remaining_tiles += 1

        return self.table.get_player(meld.who).add_meld(meld)

    def enemy_discard(self, player_seat, tile):
        self.table.get_player(player_seat).discards.append(tile)  # TODO: Is this correct?
        self.table.count_of_remaining_tiles -= 1

        for player in self.table.players:
            if player.in_riichi:
                player.safe_tiles.append(tile)

    def enemy_riichi(self, player_seat):
        self.table.get_player(player_seat).is_riichi = True
