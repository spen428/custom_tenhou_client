import pygame

from tenhou.decoder import TenhouDecoder
from tenhou.events import UiEvent, UiEvents, GAMEEVENT, GameEvents, GameEvent
from tenhou.gui.screens import EventListener
from tenhou.tenhou_async_api import AsyncTenhouApi, Error


class GameClient(EventListener):
    """Responsible for firing pygame events when interacting with the game/Tenhou server."""

    def on_event(self, event):
        if event.type == GAMEEVENT:
            if event.game_event == GameEvents.DISCARD:
                self.tenhou_client.async_discard_tile(event.tile)
                pygame.event.post(GameEvent(GameEvents.SENT_DISCARD, {'tile': event.tile}))
            elif event.game_event == GameEvents.CALL:
                self.tenhou_client.async_call(event.call_type)
                pygame.event.post(GameEvent(GameEvents.SENT_CALL, {'call_type': event.call_type}))

    def __init__(self):
        self.tenhou_decoder = TenhouDecoder()
        self.tenhou_client = AsyncTenhouApi()

    def log_in(self, user_id):
        def callback(data):
            if data == Error.LOGIN_SUCCESS:
                pygame.event.post(UiEvent(UiEvents.LOGGED_IN))
            elif data == Error.LOGIN_FAILED or data == Error.AUTH_FAILED:
                pygame.event.post(UiEvent(UiEvents.LOGIN_FAILED))
            elif type(data) == tuple:
                err, messages = data
                if err == Error.REJOINED_GAME:
                    pygame.event.post(UiEvent(UiEvents.LOGGED_IN))
                    data = self.tenhou_client.rejoin_game(messages, self._game_message_handler)
                    lobby, game_type_id, game_id, game_messages = data
                    pygame.event.post(UiEvent(UiEvents.JOINED_GAME,
                                              {'lobby': lobby, 'game_type_id': game_type_id, 'game_id': game_id}))
                    for message in game_messages:
                        self._game_message_handler(message)
            else:
                print(data)

        self.tenhou_client.async_log_in(user_id, callback)

    def cancel_login(self):
        self.tenhou_client.terminate()

    def log_out(self):
        def callback(data):
            pygame.event.post(UiEvent(UiEvents.LOGGED_OUT))

        self.tenhou_client.async_log_out(callback)

    def _game_message_handler(self, message):
        event = self.tenhou_decoder.message_to_event(message)
        if event is not None:
            pygame.event.post(event)

    def join_game(self, lobby, game_type_id):

        def callback(data):
            if data is not None:
                game_id, _, _, game_messages = data
                pygame.event.post(
                    UiEvent(UiEvents.JOINED_GAME, {'lobby': lobby, 'game_type_id': game_type_id, 'game_id': game_id}))
                for message in game_messages:
                    self._game_message_handler(message)
            pygame.event.post(UiEvent(UiEvents.FAILED_TO_JOIN_GAME))

        self.tenhou_client.async_join_game(self._game_message_handler, lobby, game_type_id, callback)
        pygame.event.post(UiEvent(UiEvents.JOINED_GAME_QUEUE, {'lobby': lobby, 'game_type_id': game_type_id}))

    def leave_game(self):
        self.tenhou_client._disconnect()

    def cancel_join_game(self):
        self.tenhou_client.cancel_join_game()
