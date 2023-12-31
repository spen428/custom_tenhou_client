# -*- coding: utf-8 -*-
import logging
from typing import Set

from mahjong.constants import EAST, SOUTH, WEST, NORTH
from mahjong.meld import Meld
from mahjong.tile import Tile
from tenhou.jong.classes import CallType

logger = logging.getLogger('tenhou')


class Player(object):
    def __init__(self, seat, oya, table):
        self.discards: [Tile] = []
        self.melds: [Meld] = []
        self.tiles: [Tile] = []
        self.seat = seat
        self.table: 'Table' = table  # Use string literal for type as we have a cyclic dependency
        self.dealer_seat = self.set_oya(oya)
        self.tsumohai: Tile = None
        self.riichi_discards: [Tile] = []
        self.called_discards: Set[Tile] = set()
        self.score = 0
        self.not_rotated_discard = False
        self.name = ''
        self.rank = ''
        self.rate = -1
        self.sex = ''
        self.is_tempai = False
        self.is_riichi = False
        self.tiles_hidden = False  # TODO: This should be True by default, and disabled for replays?

    def add_meld(self, meld):
        self.melds.append(meld)
        # Remove used tiles from hand
        if self.tiles_hidden:
            num_to_remove = 2
            if meld.type == Meld.KAN:
                if meld.kan_type == CallType.ANKAN:
                    num_to_remove = 4
                elif meld.kan_type == CallType.SHOUMINKAN:
                    num_to_remove = 1
                elif meld.kan_type == CallType.DAIMINKAN:
                    num_to_remove = 3
            for _ in range(num_to_remove):
                self.tiles.pop()
            return
        for tile in meld.tiles:
            if self.tsumohai == tile:
                self.tsumohai = None  # Can be the case for ANKAN and SHOUMINKAN
            try:
                self.tiles.remove(tile)
            except ValueError:
                pass

    def init_hand(self, tiles):
        self.tiles = [Tile(i) for i in tiles]

    def draw_tile(self, tile_id):
        if tile_id is None:
            tile_id = -1
        tile = Tile(tile_id)
        self.tiles.append(tile)
        self.tsumohai = tile
        # we need sort it to have a better string presentation
        self.tiles = sorted(self.tiles)

    def discard_tile(self, tile_id):
        tile = Tile(tile_id)
        self.tsumohai = None
        self.discards.append(tile)
        if self.tiles_hidden:
            self.tiles.pop()  # Just remove anything
        else:
            self.tiles.remove(tile)
        if self.is_riichi and self.not_rotated_discard:
            self.riichi_discards.append(tile)
            self.not_rotated_discard = False
        return tile

    def call_discard(self):
        tile = self.discards[-1]
        self.called_discards.add(tile)
        if self.is_riichi and tile == self.riichi_discards[-1]:
            # The rotated tile was called, ensure next discard is rotated
            self.not_rotated_discard = True
        return tile

    def erase_state(self):
        self.discards = []
        self.melds = []
        self.tiles = []
        self.is_tempai = False
        self.is_riichi = False
        self.dealer_seat = 0
        self.tsumohai = None
        self.riichi_discards = []
        self.score = 0
        self.not_rotated_discard = False
        self.called_discards = set()
        self.tiles_hidden = False

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

    def set_oya(self, oya):
        self.dealer_seat = (self.seat - oya) % 4  # Dealer location relative to the player
        return self.dealer_seat
