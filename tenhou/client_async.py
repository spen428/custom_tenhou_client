# -*- coding: utf-8 -*-
import datetime
import logging
import re
import socket
from queue import Queue
from threading import Thread
from time import sleep, time
from urllib.parse import quote

import pygame

from mahjong.client import Client
from mahjong.constants import WINDS_TO_STR
from mahjong.meld import Meld
from mahjong.tile import TilesConverter
from tenhou.decoder import TenhouDecoder
from tenhou.events import GameEvents, GameEvent
from utils.settings_handler import settings

logger = logging.getLogger('tenhou')


def post_event(game_event: GameEvents, data: dict = None):
    pygame.event.post(GameEvent(game_event, data))


class TenhouClient(Client):
    """This is an asynchronous implementation of the previous Tenhou.net client. Methods prepended with a single
    underscore are synchronous, and methods prepended with two underscores are synchronous methods used by the single
    underscore methods. To use the async functionality therefore, call only the methods without an underscore prefix.
    These methods can take an optional callback function, which should take a single argument that will be the return
    value of the asynchronous task. See the individual methods' documentation for more details."""

    def __init__(self, socket_object):
        super(TenhouClient, self).__init__()
        self.socket = socket_object
        self.game_is_continue = True
        self.looking_for_game = True
        self.connection_thread = Thread(target=self.__connection_target)
        self.connection_thread_message_queue = Queue()
        self.connection_thread_running = False
        self.keep_alive_thread = None
        self.user_id = None
        self.is_tournament = None
        self.decoder = TenhouDecoder()

    def close(self):
        """Close the client, stopping any background threads. This MUST be called when the client is no longer in 
        use."""
        self.connection_thread_running = False
        self.game_is_continue = False
        self.connection_thread.join()
        self.keep_alive_thread.join()

    def on_event(self, event):
        """Method for receiving game events."""
        pass

    def authenticate(self, user_id, is_tournament=False, callback=None):
        """Attempt to log in with the given user id. Callback function is passed a boolean value
        indicating whether the authentication succeeded or failed."""
        self._put_task(self._authenticate, (user_id, is_tournament), callback)

    def start_game(self, callback=None):
        self._put_task(self._start_game, None, callback)

    def end_game(self, callback=None):
        self._put_task(self._end_game, None, callback)

    def _authenticate(self, user_id, is_tournament):
        self.user_id = user_id
        self.is_tournament = is_tournament
        self.__send_login_request(user_id)
        auth_message = self._read_message()

        auth_string = self.decoder.parse_auth_string(auth_message)
        if not auth_string:
            post_event(GameEvents.LOGIN_REQUEST_FAILED, {'user_id': user_id})
            return False

        auth_token = self.decoder.generate_auth_token(auth_string)
        self.__send_auth_token(auth_token)

        # sometimes tenhou send an empty tag after authentication (in tournament mode)
        # and bot thinks that he was not auth
        # to prevent it lets wait a little
        # and read a group of tags
        sleep(3)
        authenticated = False
        messages = self._get_multiple_messages()
        for message in messages:
            if '<ln' in message:
                authenticated = True
                post_event(GameEvents.RECV_AUTH_SUCCESSFUL, {'message': message})
                break

        if authenticated:
            self._send_keep_alive_ping()
            logger.info("Authentication successful")
            return True
        else:
            logger.info('Failed to authenticate')
            post_event(GameEvents.AUTH_FAILED,
                       {'user_id': user_id, 'auth_string': auth_string, 'auth_token': auth_token})
            return False

    def _start_game(self):
        log_link = ''

        if settings.LOBBY != '0':
            if settings.IS_TOURNAMENT:
                logger.info('Go to the tournament lobby: {0}'.format(settings.LOBBY))
                self._send_message('<CS lobby="{0}" />'.format(settings.LOBBY))
                sleep(2)
                self._send_message('<DATE />')
            else:
                logger.info('Go to the lobby: {0}'.format(settings.LOBBY))
                self._send_message('<CHAT text="{0}" />'.format(quote('/lobby {0}'.format(settings.LOBBY))))
                sleep(2)

        game_type = '{0},{1}'.format(settings.LOBBY, settings.GAME_TYPE)

        if not settings.IS_TOURNAMENT:
            self._send_message('<JOIN t="{0}" />'.format(game_type))
            logger.info('Looking for the game...')

        start_time = datetime.datetime.now()

        while self.looking_for_game:
            sleep(1)

            messages = self._get_multiple_messages()

            for message in messages:

                if '<rejoin' in message:
                    # game wasn't found, continue to wait
                    self._send_message('<JOIN t="{0},r" />'.format(game_type))

                if '<go' in message:
                    self._send_message('<GOK />')
                    self._send_message('<NEXTREADY />')

                if '<taikyoku' in message:
                    self.looking_for_game = False
                    game_id, seat = self.decoder.parse_log_link(message)
                    log_link = 'http://tenhou.net/0/?log={0}&tw={1}'.format(game_id, seat)
                    self.statistics.game_id = game_id

                if '<un' in message:
                    values = self.decoder.parse_names_and_ranks(message)
                    self.table.set_players_names_and_ranks(values)

                if '<ln' in message:
                    self._send_message(self._pxr_tag())

            current_time = datetime.datetime.now()
            time_difference = current_time - start_time

            if time_difference.seconds > 60 * settings.WAITING_GAME_TIMEOUT_MINUTES:
                break

        # we wasn't able to find the game in timeout minutes
        # sometimes it happens and we need to end process
        # and try again later
        if self.looking_for_game:
            logger.error('Game is not started. Can\'t find the game')
            self.end_game()
            return

        logger.info('Game started')
        logger.info('Log: {0}'.format(log_link))
        logger.info('Players: {0}'.format(self.table.players))

        main_player = self.table.get_main_player()

        while self.game_is_continue:
            sleep(1)

            messages = self._get_multiple_messages()

            for message in messages:

                if '<init' in message:
                    values = self.decoder.parse_initial_values(message)
                    self.table.init_round(values['round_number'], values['count_of_honba_sticks'],
                                          values['count_of_riichi_sticks'], values['dora_indicator'], values['dealer'],
                                          values['scores'], )

                    tiles = self.decoder.parse_initial_hand(message)
                    self.table.init_main_player_hand(tiles)

                    logger.info(self.table.__str__())
                    logger.info('Players: {}'.format(self.table.get_players_sorted_by_scores()))
                    logger.info('Dealer: {}'.format(self.table.get_player(values['dealer'])))
                    logger.info('Round  wind: {}'.format(WINDS_TO_STR[self.table.round_wind]))
                    logger.info('Player wind: {}'.format(WINDS_TO_STR[main_player.player_wind]))

                # draw and discard
                if '<t' in message:
                    tile = self.decoder.parse_tile(message)

                    if not main_player.in_riichi:
                        self.draw_tile(tile)
                        sleep(1)

                        logger.info('Hand: {0}'.format(TilesConverter.to_one_line_string(main_player.tiles)))

                        self.discard_tile(tile)

                    if 't="16"' in message:
                        # we win by self draw (tsumo)
                        self._send_message('<N type="7" />')
                    else:
                        # let's call riichi and after this discard tile
                        if main_player.can_call_riichi():
                            self._send_message('<REACH hai="{0}" />'.format(tile))
                            sleep(2)
                            main_player.in_riichi = True

                        # tenhou format: <D p="133" />
                        self._send_message('<D p="{0}"/>'.format(tile))

                        logger.info('Remaining tiles: {0}'.format(self.table.count_of_remaining_tiles))

                # new dora indicator after kan
                if '<dora' in message:
                    tile = self.decoder.parse_dora_indicator(message)
                    self.table.add_dora_indicator(tile)
                    logger.info('New dora indicator: {0}'.format(tile))

                if '<reach' in message and 'step="2"' in message:
                    who_called_riichi = self.decoder.parse_who_called_riichi(message)
                    self.enemy_riichi(who_called_riichi)
                    logger.info('Riichi called by {0} player'.format(who_called_riichi))

                # the end of round
                if 'agari' in message or 'ryuukyoku' in message:
                    sleep(2)
                    self._send_message('<NEXTREADY />')

                # t="7" - suggest to open kan
                open_sets = ['t="1"', 't="2"', 't="3"', 't="4"', 't="5"', 't="7"']
                if any(i in message for i in open_sets):
                    sleep(1)
                    self._send_message('<N />')

                # set call
                if '<n who=' in message:
                    meld = self.decoder.parse_meld(message)
                    self.call_meld(meld)
                    logger.info('Meld: {0}, who {1}'.format(meld.type, meld.who))

                    # other player upgraded pon to kan, and it is our winning tile
                    if meld.type == Meld.CHAKAN and 't="8"' in message:
                        # actually I don't know what exactly client response should be
                        # let's try usual ron response
                        self._send_message('<N type="6" />')

                # other players discards: <e, <f, <g + tile number
                match_discard = re.match(r"^<[efg]+\d.*", message)
                if match_discard:
                    # we win by other player's discard
                    if 't="8"' in message:
                        self._send_message('<N type="6" />')

                    tile = self.decoder.parse_tile(message)

                    if '<e' in message:
                        player_seat = 1
                    elif '<f' in message:
                        player_seat = 2
                    else:
                        player_seat = 3

                    self.enemy_discard(player_seat, tile)

                if 'owari' in message:
                    values = self.decoder.parse_final_scores_and_uma(message)
                    self.table.set_players_scores(values['scores'], values['uma'])

                if '<prof' in message:
                    self.game_is_continue = False

        logger.info('Final results: {0}'.format(self.table.get_players_sorted_by_scores()))

        # we need to finish the game, and only after this try to send statistics
        # if order will be different, tenhou will return 404 on log download endpoint
        self.end_game()

        # sometimes log is not available just after the game
        # let's wait one minute before the statistics update
        if settings.STAT_SERVER_URL:
            sleep(60)
            result = self.statistics.send_statistics()
            logger.info('Statistics sent: {0}'.format(result))

    def _end_game(self):
        self.game_is_continue = False
        self._send_message('<BYE />')

        if self.keep_alive_thread:
            self.keep_alive_thread.join()

        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

        logger.info('End of the game')

    def _send_message(self, message):
        # tenhou required the empty byte in the end of each sending message
        logger.debug('Send: {0}'.format(message))
        message += '\0'
        self.socket.sendall(message.encode())

    def _read_message(self):
        message = self.socket.recv(1024)
        logger.debug('Get: {0}'.format(message.decode('utf-8').replace('\x00', ' ')))

        message = message.decode('utf-8')
        # sometimes tenhou send messages in lower case, sometime in upper case, let's unify the behaviour
        message = message.lower()

        return message

    def _get_multiple_messages(self):
        # tenhou can send multiple messages in one request
        messages = self._read_message()
        messages = messages.split('\x00')
        # last message always is empty after split, so let's exclude it
        messages = messages[0:-1]

        return messages

    def _send_keep_alive_ping(self):
        def __keep_alive_target():
            while self.game_is_continue:
                self._send_message('<Z />')
                post_event(GameEvents.SENT_KEEP_ALIVE)
                sleep(15)

        self.keep_alive_thread = Thread(target=__keep_alive_target)
        self.keep_alive_thread.start()

    def _pxr_tag(self):
        # I have no idea why we need to send it, but better to do it
        if self.is_tournament:
            return '<PXR V="-1" />'
        if self.user_id == 'NoName':
            return '<PXR V="1" />'
        else:
            return '<PXR V="9" />'

    def __send_login_request(self, user_id):
        self._send_message('<HELO name="{0}" tid="f0" sx="M" />'.format(quote(user_id)))
        post_event(GameEvents.SENT_LOGIN_REQUEST, {'user_id': user_id})

    def __send_auth_token(self, auth_token):
        self._send_message('<AUTH val="{0}"/>'.format(auth_token))
        self._send_message(self._pxr_tag())
        post_event(GameEvents.SENT_AUTH_TOKEN, {'auth_token': auth_token})

    def __connection_target(self):
        self.connection_thread_running = True
        while self.connection_thread_running:
            message = self.connection_thread_message_queue.get()
            timestamp, func, params, callback = message
            logger.debug('Executing async task ' + func.__name__ + ' with timestamp ' + str(timestamp))
            ret = func(*params)
            if callback is not None:
                logger.debug('Executing callback for task ' + func.__name__)
                callback(ret)

    def _put_task(self, func, params, callback):
        if not self.connection_thread_running:
            self.connection_thread.start()
        message = (time(), func, params, callback)
        self.connection_thread_message_queue.put(message)
