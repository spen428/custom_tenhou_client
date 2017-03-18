# -*- coding: utf-8 -*-
import logging

from mahjong.constants import EAST, SOUTH, WEST, NORTH
from mahjong.tile import Tile
from utils.settings_handler import settings

logger = logging.getLogger('tenhou')


class Player(object):  # TODO: Why are some of these fields declared twice?
    # the place where is player is sitting
    # always = 0 for our player
    seat = 0
    # where is sitting dealer, based on this information we can calculate player wind
    dealer_seat = 0
    # position based on scores
    position = 0
    scores = 0
    uma = 0

    name = ''
    rank = ''
    rate = -1
    sex = ''

    discards = []
    # tiles that were discarded after player's riichi
    safe_tiles = []
    tiles = []
    melds = []
    table = None
    is_tempai = False
    is_riichi = False
    in_defence_mode = False

    def __init__(self, seat, dealer_seat, table, use_previous_ai_version=False):
        self.discards = []
        self.melds = []
        self.tiles = []
        self.safe_tiles = []
        self.seat = seat
        self.table = table
        self.dealer_seat = dealer_seat
        self.tsumohai = None
        self.riichi_tiles = set()
        self.score = 0

        if use_previous_ai_version:
            try:
                from mahjong.ai.old_version import MainAI
            # project wasn't set up properly
            # we don't have old version
            except ImportError:
                logger.error('Wasn\'t able to load old api version')
                from mahjong.ai.main import MainAI
        else:
            if settings.ENABLE_AI:
                from mahjong.ai.main import MainAI
            else:
                from mahjong.ai.random import MainAI

        self.ai = MainAI(table, self)

    def __str__(self):
        result = u'{0}'.format(self.name)
        if self.scores:
            result += u' ({:,d})'.format(int(self.scores))
            if self.uma:
                result += u' {0}'.format(self.uma)
        else:
            result += u' ({0})'.format(self.rank)
        return result

    # for calls in array
    def __repr__(self):
        return self.__str__()

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
        return tile

    def riichi_tile(self, tile_id):
        self.riichi_tiles.add(Tile(tile_id))
        self.discard_tile(tile_id)

    def call_discard(self):
        tile = self.discards[-1]
        self.discards.remove(tile)
        return tile

    def erase_state(self):
        self.discards = []
        self.melds = []
        self.tiles = []
        self.safe_tiles = []
        self.is_tempai = False
        self.is_riichi = False
        self.in_defence_mode = False
        self.dealer_seat = 0
        self.tsumohai = None
        self.riichi_tiles = set()
        self.score = 0

    def can_call_riichi(self):
        return all([self.is_tempai, not self.is_riichi, self.scores >= 1000, self.table.count_of_remaining_tiles > 4])

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
