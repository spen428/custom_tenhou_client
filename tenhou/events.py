from enum import Enum

import pygame


class GameEvents(Enum):  # TODO: Sort these nicely
    RECV_DRAW = 0
    SENT_LOGIN_REQUEST = 1
    RECV_LOGIN_REQUEST_ACK = 2
    SENT_AUTH_TOKEN = 3
    RECV_AUTH_SUCCESSFUL = 4
    SENT_KEEP_ALIVE = 5
    SENT_UNKNOWN = 6
    RECV_UNKNOWN = 7
    SENT_END_GAME = 8
    DISCONNECTED = 9
    LOGIN_REQUEST_FAILED = 10
    AUTH_FAILED = 11
    RECV_SHUFFLE_SEED = 12
    RECV_JOIN_TABLE = 13
    RECV_PLAYER_DETAILS = 14
    RECV_BEGIN_HAND = 15
    RECV_RIICHI_DECLARED = 16
    RECV_DORA_FLIPPED = 17
    RECV_AGARI = 18
    RECV_RYUUKYOKU = 19
    RECV_CALL = 20
    RECV_BEGIN_GAME = 21
    RECV_DISCARD = 22
    END_OF_GAME = 23
    RECV_CALL_AVAILABLE = 24
    CALL_STEP_FORWARD = 25
    CALL_STEP_BACKWARD = 26


def GameEvent(game_event: GameEvents, data: dict = None):
    if data is None:
        data = {}
    data['game_event'] = game_event
    return pygame.event.Event(pygame.USEREVENT, data)
