# -*- coding: utf-8 -*-
import logging
import socket
from enum import Enum
from queue import Queue
from threading import Thread
from time import sleep
from urllib.parse import quote

from tenhou.decoder import TenhouDecoder

logger = logging.getLogger('tenhou')

TENHOU_IP = '133.242.10.78'
TENHOU_PORT = 10080
DEFAULT_USER_ID = 'NoName'
DEFAULT_GAME_LOBBY = 0

"""
  0 - 1 - online, 0 - bots
  1 - aka forbidden
  2 - kuitan forbidden
  3 - hanchan
  4 - 3man
  5 - dan flag
  6 - fast game
  7 - dan flag

  Combine them as:
  76543210

  00001001 = 9 = hanchan ari-ari
  00000001 = 1 = tonpu-sen ari-ari
"""
DEFAULT_GAME_TYPE_ID = '1'


class Error(Enum):
    AUTH_FAILED = 0
    LOGIN_FAILED = 1
    LOGIN_SUCCESS = 2


class AsyncTenhouApi(object):
    """Async API for interacting with the Tenhou.net game servers. Every async function can take an optional callback 
    argument which should be a function that takes one argument. The callback function will be invoked on completion 
    of the async request, and the value returned by it will be passed as the first argument.
    """

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.looking_for_game = True

        self.keep_alive_thread = None
        self.keep_alive = False
        self.connection_thread = None
        self.connection_thread_queue = Queue()
        self.connection_alive = False
        self.game_thread = None
        self.in_game = False

        self.decoder = TenhouDecoder()
        self.user_id = None

    def __del__(self):
        # Let the spawned threads die
        self.connection_alive = False
        self.keep_alive = False
        self.in_game = False
        if self.game_thread:
            self.game_thread.join()
        if self.keep_alive_thread:
            self.keep_alive_thread.join()
        if self.connection_thread:
            self.connection_thread.join()

    def async_log_in(self, user_id, callback=None):
        """Send an async log in request."""

        def __log_in_as_user():
            ret = self._log_in(user_id)
            if ret == Error.LOGIN_SUCCESS:
                self.user_id = user_id
            return ret

        if not self.connection_alive:
            self._start_connection_thread()

        self._queue_function(__log_in_as_user, callback)

    def async_log_out(self, callback=None):
        """Send an async log out request."""

        def __log_out():
            self._disconnect()
            self.user_id = None
            self.connection_alive = False
            if self.connection_thread:
                self.connection_thread.join()

        self._queue_function(__log_out, callback)

    def async_join_game(self, message_handler, lobby=DEFAULT_GAME_LOBBY, game_type_id=DEFAULT_GAME_TYPE_ID,
                        callback=None):
        """Queue for and join a game.
        
        :param message_handler: function that will receive all messages sent by Tenhou.net server
        :param lobby: the lobby to join
        :param game_type_id: the game type to join
        :param callback: optional callback function
        :return: None
        """

        def __join_game():
            game_id = self._join_game(lobby, game_type_id)
            self._start_game_thread(message_handler)
            return game_id

        self._queue_function(__join_game, callback)

    def _queue_function(self, func, callback=None):
        self.connection_thread_queue.put_nowait((func, callback))

    def _start_connection_thread(self):
        def target():
            while self.connection_alive:
                func, callback = self.connection_thread_queue.get()
                ret = func()
                if callback is not None:
                    callback(ret)

        self.connection_alive = True
        self.connection_thread = Thread(target=target)
        self.connection_thread.setDaemon(True)
        self.connection_thread.start()

    def _start_keep_alive_thread(self):
        def target():
            while self.keep_alive:
                self._send_message('<Z />')
                sleep(5)

        self.keep_alive = True
        self.keep_alive_thread = Thread(target=target)
        self.keep_alive_thread.setDaemon(True)
        self.keep_alive_thread.start()

    def _start_game_thread(self, message_handler=None):
        def target():
            self.__handle_game(message_handler)

        self.in_game = True
        self.game_thread = Thread(target=target)
        self.game_thread.setDaemon(True)
        self.game_thread.start()

    def _connect(self):
        self.socket.connect((TENHOU_IP, TENHOU_PORT))

    def __send_login_request(self, user_id):
        self._send_message('<HELO name="{0}" tid="f0" sx="M" />'.format(quote(user_id)))

    def __send_auth_token(self, auth_token, user_id):
        self._send_message('<AUTH val="{0}"/>'.format(auth_token))
        self._send_message(self._get_pxr_tag(user_id, False))

    def _log_in(self, user_id):
        self._connect()
        self.__send_login_request(user_id)
        auth_message = self._read_message()

        auth_string = self.decoder.parse_auth_string(auth_message)
        if not auth_string:
            logger.info('Did not receive auth_string')
            return Error.LOGIN_FAILED

        auth_token = self.decoder.generate_auth_token(auth_string)
        self.__send_auth_token(auth_token, user_id)

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
                break

        if authenticated:
            self._start_keep_alive_thread()
            logger.info('Successfully authenticated')
            return Error.LOGIN_SUCCESS
        else:
            logger.info('Failed to authenticate')
            return Error.AUTH_FAILED

    def _join_game(self, lobby, game_type_id):
        """Queue for a game.
        
        :param lobby: the lobby id to join
        :param game_type_id: the id of the game type to join
        :return: the id of the joined game 
        """

        is_tournament = False  # TODO

        if int(lobby) != '0':
            if is_tournament:
                logger.info('Go to the tournament lobby: {0}'.format(lobby))
                self._send_message('<CS lobby="{0}" />'.format(lobby))
                sleep(2)
                self._send_message('<DATE />')
            else:
                logger.info('Go to the lobby: {0}'.format(lobby))
                self._send_message('<CHAT text="{0}" />'.format(quote('/lobby {0}'.format(lobby))))
                sleep(2)

        game_type = '{0},{1}'.format(lobby, game_type_id)

        if not is_tournament:
            self._send_message('<JOIN t="{0}" />'.format(game_type))
            logger.info('Looking for the game...')

        log_link = ''
        game_id = None

        game_messages = []  # Messages to forward to client
        while self.looking_for_game:
            sleep(1)
            messages = self._get_multiple_messages()
            for message in messages:
                if '<rejoin' in message:
                    # game wasn't found, continue to wait
                    self._send_message('<JOIN t="{0},r" />'.format(game_type))

                if '<go' in message:
                    game_messages.append(message)
                    self._send_message('<GOK />')
                    self._send_message('<NEXTREADY />')

                if '<taikyoku' in message:
                    game_messages.append(message)
                    self.looking_for_game = False
                    game_id, seat = self.decoder.parse_log_link(message)
                    log_link = 'http://tenhou.net/0/?log={0}&tw={1}'.format(game_id, seat)

                if '<un' in message:
                    game_messages.append(message)

                if '<ln' in message:
                    self._send_message(self._get_pxr_tag(self.user_id, is_tournament))

        logger.info('Game started')
        logger.info('Log: {0}'.format(log_link))
        return game_id, game_messages

    def __handle_game(self, message_handler=None):
        while self.in_game:
            sleep(1)
            messages = self._get_multiple_messages()
            for message in messages:
                if message_handler:
                    message_handler(message)
                if '<prof' in message:
                    self.in_game = False
                    logger.info('Game over')

        pass
        # self._disconnect()

    def _disconnect(self):
        self.keep_alive = False
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

    def _get_pxr_tag(self, user_id, is_tournament):
        # I have no idea why we need to send it, but better to do it
        if is_tournament:
            return '<PXR V="-1" />'

        if user_id == 'NoName':
            return '<PXR V="1" />'
        else:
            return '<PXR V="9" />'
