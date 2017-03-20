# -*- coding: utf-8 -*-

from mahjong.constants import EAST, SOUTH, WEST, NORTH
from mahjong.player import Player
from mahjong.tile import Tile
from mahjong.utils import plus_dora, is_aka_dora


class Table(object):
    def __init__(self):
        self.dora_indicators: [Tile] = []
        self.players: [Player] = []
        self.dealer_seat = 0
        self.round_number = 0
        self.count_of_riichi_sticks = 0
        self.count_of_honba_sticks = 0
        self.count_of_remaining_tiles = 0
        self.count_of_players = 4

        self._init_players()

    def __str__(self):
        return 'Round: {0}, Honba: {1}, Dora Indicators: {2}'.format(self.round_number, self.count_of_honba_sticks,
                                                                     self.dora_indicators)

    def init_round(self, round_number, count_of_honba_sticks, count_of_riichi_sticks, dora_indicator, dealer_seat,
                   scores):

        self.round_number = round_number
        self.count_of_honba_sticks = count_of_honba_sticks
        self.count_of_riichi_sticks = count_of_riichi_sticks

        self.dora_indicators = []
        self.add_dora_indicator(dora_indicator)

        # erase players state
        for player in self.players:
            player.erase_state()
            player.dealer_seat = dealer_seat

        self.set_players_scores(scores)

        # 136 - total count of tiles
        # 14 - tiles in dead wall
        # 13 - tiles in each player hand
        self.count_of_remaining_tiles = 136 - 14 - self.count_of_players * 13

    def init_main_player_hand(self, tiles):
        self.get_main_player().init_hand(tiles)

    def add_open_set(self, meld):
        self.get_player(meld.who).add_meld(meld)

    def add_dora_indicator(self, tile):
        self.dora_indicators.append(tile)

    def is_dora(self, tile):
        return plus_dora(tile, self.dora_indicators) or is_aka_dora(tile)

    def set_players_scores(self, scores):
        for i in range(len(scores)):
            self.get_player(i).score = scores[i] * 100
        self.recalculate_players_position()

    def recalculate_players_position(self):
        temp_players = self.get_players_sorted_by_scores()
        for i in range(len(temp_players)):
            temp_player = temp_players[i]
            self.get_player(temp_player.seat).position = i + 1

    def set_players_names_and_ranks(self, values):
        for x in range(len(values)):
            self.get_player(x).name = values[x]['name']
            self.get_player(x).rank = values[x]['rank']

    def get_player(self, player_seat) -> Player:
        return self.players[player_seat]

    def get_main_player(self) -> Player:
        return self.players[0]

    def get_players_sorted_by_scores(self):
        return sorted(self.players, key=lambda x: x.score, reverse=True)

    def _init_players(self):
        self.players = []

        for seat in range(0, self.count_of_players):
            player = Player(seat=seat, dealer_seat=0, table=self)
            self.players.append(player)

    @property
    def round_wind(self):
        if self.round_number < 4:
            return EAST
        elif 4 <= self.round_number < 8:
            return SOUTH
        elif 8 <= self.round_number < 12:
            return WEST
        else:
            return NORTH

    @property
    def is_oorasu(self):
        return False  # TODO

    @property
    def table_name(self):
        return ''  # TODO
