from enum import Enum

import pygame

GAMEEVENT = pygame.USEREVENT + 0
UIEVENT = pygame.USEREVENT + 1


class GameEvents(Enum):  # TODO: Sort these nicely
    RECV_DRAW = 0
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
    RECV_RIICHI_STICK_PLACED = 27
    END_OF_REPLAY = 28
    RECV_DISCONNECTED = 29
    RECV_RECONNECTED = 30


class UiEvents(Enum):
    SENT_LOGIN_REQUEST = 1
    RECV_LOGIN_REQUEST_ACK = 2
    SENT_AUTH_TOKEN = 3
    RECV_AUTH_SUCCESSFUL = 4
    SENT_KEEP_ALIVE = 5
    RECV_UNKNOWN = 7
    SENT_END_GAME = 8
    LOGIN_REQUEST_FAILED = 10
    DISCONNECTED = 9
    AUTH_FAILED = 11

    EXIT_GAME = -1
    LEAVE_GAME = 0
    LOG_IN = 1
    LOG_OUT = 2
    OPEN_REPLAY = 3
    JOIN_GAME = 4
    TEST_INGAMEUI = 5
    TEST_REPLAY = 6
    TEST_LG = 7
    TEST_LGR = 8
    LOGGED_IN = 9
    LOGGED_OUT = 10
    LOGIN_FAILED = 11
    RELOAD_REPLAY = 12


def GameEvent(game_event: GameEvents, data: dict = None):
    if data is None:
        data = {}
    data['game_event'] = game_event
    return pygame.event.Event(GAMEEVENT, data)


def UiEvent(ui_event: UiEvents, data: dict = None):
    if data is None:
        data = {}
    data['ui_event'] = ui_event
    return pygame.event.Event(UIEVENT, data)
