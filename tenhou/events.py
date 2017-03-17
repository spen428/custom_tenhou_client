from enum import Enum

import pygame


class GameEvents(Enum):
    SENT_LOGIN_REQUEST = pygame.USEREVENT + 1
    RECV_LOGIN_REQUEST_ACK = pygame.USEREVENT + 2
    SENT_AUTH_TOKEN = pygame.USEREVENT + 3
    RECV_AUTH_SUCCESSFUL = pygame.USEREVENT + 4
    SENT_KEEP_ALIVE = pygame.USEREVENT + 5
    SENT_UNKNOWN = pygame.USEREVENT + 6
    RECV_UNKNOWN = pygame.USEREVENT + 7
    SENT_END_GAME = pygame.USEREVENT + 8
    DISCONNECTED = pygame.USEREVENT + 9
    LOGIN_REQUEST_FAILED = pygame.USEREVENT + 10
    AUTH_FAILED = pygame.USEREVENT + 11
