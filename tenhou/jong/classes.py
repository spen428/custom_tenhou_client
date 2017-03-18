import time
from enum import Enum


class CallType(Enum):
    NUKE = 0
    CHII = 1
    PON = 2
    ANKAN = 3
    SHOUMINKAN = 4  # AKA "Extended kan"
    DAIMINKAN = 5

    @staticmethod
    def is_kantsu(call_type):
        return call_type in [CallType.ANKAN, CallType.DAIMINKAN, CallType.SHOUMINKAN]


class Call(object):
    def __init__(self, tile_ids: [int], call_tile: int, call_type: CallType):
        self.call_type = call_type
        self.tile_ids = tile_ids
        self.call_tile = call_tile


class Position(Enum):
    JIBUN = 0
    SHIMOCHA = 1
    TOIMEN = 2
    KAMICHA = 3


class Player(object):
    def __init__(self, name, rank):
        self.name = name
        self.rank = rank
        self.score = 0
        self.seat = None
        self.hand_tiles = []
        self.discards = []
        self.calls = []
        self.is_riichi = False
