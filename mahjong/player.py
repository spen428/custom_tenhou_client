# -*- coding: utf-8 -*-
import logging
from typing import Set

from mahjong.constants import EAST, SOUTH, WEST, NORTH
from mahjong.meld import Meld
from mahjong.tile import Tile

logger = logging.getLogger('tenhou')


class Player(object):
    def __init__(self, seat, dealer_seat, table):
        self.discards: [Tile] = []
        self.melds: [Meld] = []
        self.tiles: [Tile] = []
        self.seat = seat
        self.table: 'Table' = table  # Use string literal for type as we have a cyclic dependency
        self.dealer_seat = dealer_seat
        self.tsumohai: Tile = None
        self.riichi_discards: Set[Tile] = set()
        self.called_discards: Set[Tile] = set()
        self.score = 0
        self.declaring_riichi = False
        self.name = ''
        self.rank = ''
        self.rate = -1
        self.sex = ''
        self.is_tempai = False
        self.is_riichi = False

    def add_meld(self, meld):
        self.melds.append(meld)

    def init_hand(self, tiles):
        self.tiles = [Tile(i) for i in tiles]

    def draw_tile(self, tile_id):
        tile = Tile(tile_id)
        self.tiles.append(tile)
        self.tsumohai = tile
        # we need sort it to have a better string presentation
        self.tiles = sorted(self.tiles)

    def discard_tile(self, tile_id):
        tile = Tile(tile_id)
        self.tsumohai = None
        self.discards.append(tile)
        self.tiles.remove(tile)
        if self.declaring_riichi:
            self.riichi_discards.add(tile)
            self.declaring_riichi = False
        return tile

    def declare_riichi(self):
        self.is_riichi = True
        self.declaring_riichi = True  # Set to true will ensure next discard is rotated
        self.score -= 1000

    def call_discard(self):
        tile = self.discards[-1]
        # self.discards.remove(tile)
        self.called_discards.add(tile)
        if tile in self.riichi_discards:  # The rotated tile was called, ensure next discard is rotated
            self.declaring_riichi = True
        return tile

    def erase_state(self):
        self.discards = []
        self.melds = []
        self.tiles = []
        self.is_tempai = False
        self.is_riichi = False
        self.dealer_seat = 0
        self.tsumohai = None
        self.riichi_discards = set()
        self.score = 0
        self.declaring_riichi = False
        self.called_discards = set()

    def can_call_riichi(self):
        return all([self.is_tempai, not self.is_riichi, self.score >= 1000, self.table.count_of_remaining_tiles > 4])

    def get_only_hand_tiles(self):
        """Return a list of tiles in the player's hand, filtering out the tsumohai and called melds."""
        filtered_tiles = self.tiles[:]
        if self.tsumohai is not None:
            filtered_tiles.remove(self.tsumohai)
        for meld in self.melds:
            for tile in meld.tiles:
                try:
                    filtered_tiles.remove(tile)
                except ValueError:
                    pass  # Thrown when trying to remove the called tile, which was never in the player's hand
        return filtered_tiles

    @property
    def player_wind(self):
        position = self.dealer_seat
        if position == 0:
            return EAST
        elif position == 1:
            return NORTH
        elif position == 2:
            return WEST
        else:
            return SOUTH

    @property
    def is_dealer(self):
        return self.seat == self.dealer_seat
