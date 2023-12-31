# -*- coding: utf-8 -*-
import logging
import urllib
from urllib.parse import unquote

from bs4 import BeautifulSoup
from pygame.event import Event

from mahjong.meld import Meld
from mahjong.tile import Tile
from tenhou.events import GameEvents, GameEvent

logger = logging.getLogger('tenhou')


class GameMode(object):
    # GAME_MODES = (field_name, bit_flag, display_name)
    GAME_MODES = [('multi', 0x01, '対人戦'), ('noaka', 0x02, '赤ナシ'), ('nokui', 0x04, '喰ナシ'),
                  ('nan', 0x08, '東南'), ('sanma', 0x10, 'サンマ'), ('toku', 0x20, '特上'),
                  ('saku', 0x40, '速'), ('high', 0x80, '上級')]

    def __init__(self, val):
        self.game_mode_value = val
        self.display_name = ''
        # Set attrs such that the field names above are either true or false
        # indicating their presence. e.g. if mode is sanma then self.sanma = True
        for (field_name, bit_flag, display_name) in GameMode.GAME_MODES:
            is_flag_set = (val & bit_flag == bit_flag)
            self.__setattr__(field_name, is_flag_set)
            if is_flag_set:
                if self.display_name is '':
                    self.display_name = display_name
                else:
                    self.display_name += '　' + display_name


class TenhouDecoder(object):
    RANKS = [u'新人', u'9級', u'8級', u'7級', u'6級', u'5級', u'4級', u'3級', u'2級', u'1級', u'初段', u'二段', u'三段', u'四段', u'五段',
             u'六段', u'七段', u'八段', u'九段', u'十段', u'天鳳位']
    YAKU_NAMES = ['門前清自摸和', '立直', '一発', '槍槓', '嶺上開花', '海底摸月', '河底撈魚', '平和',
                  '断幺九', '一盃口', '自風 東', '自風 南', '自風 西', '自風 北', '場風 東', '場風 南',
                  '場風 西', '場風 北', '役牌 白', '役牌 發', '役牌 中', '両立直', '七対子', '混全帯幺九',
                  '一気通貫', '三色同順', '三色同刻', '三槓子', '対々和', '三暗刻', '小三元', '混老頭',
                  '二盃口', '純全帯幺九', '混一色', '清一色', '人和', '天和', '地和', '大三元', '四暗刻',
                  '四暗刻単騎', '字一色', '緑一色', '清老頭', '九蓮宝燈', '純正九蓮宝燈', '国士無双',
                  '国士無双１３面', '大四喜', '小四喜', '四槓子', 'ドラ', '裏ドラ', '赤ドラ']

    def _bs(self, message, tag_name):
        soup = BeautifulSoup(message, 'html.parser')
        return soup.find(tag_name)

    def parse_auth_string(self, message):
        tag = self._bs(message, 'helo')
        if tag and 'auth' in tag.attrs:
            return tag.attrs['auth']
        else:
            return None

    def parse_initial_hand(self, message):
        tag = self._bs(message, 'init')

        tiles = tag.attrs['hai']
        tiles = [int(i) for i in tiles.split(',')]

        return tiles

    def parse_init(self, message):
        tag = self._bs(message, 'init')

        seed = [int(s) for s in tag.attrs['seed'].split(',')]
        round_number = seed[0]
        count_of_honba_sticks = seed[1]
        count_of_riichi_sticks = seed[2]
        dora_indicator = seed[5]

        ten = [int(p) for p in tag.attrs['ten'].split(',')]
        oya = int(tag.attrs['oya'])

        # In replays there will be 'hai0' through 'hai3', but in live games you can of course only see your own
        # haipai, whose attr will be 'hai'
        if 'hai0' in tag.attrs:
            hais = ['hai{}'.format(n) for n in range(len(ten))]
        else:
            hais = ['hai']
        haipai = []
        for hai in hais:
            tiles = tag.attrs[hai]
            if tiles == "":  # Is the case for the 4th player in 3-player mahjong
                tiles = []
            else:
                tiles = [int(i) for i in tiles.split(',')]
            haipai.append(tiles)

        return {'seed': seed, 'ten': ten, 'oya': oya, 'haipai': haipai, 'round_number': round_number,
                'count_of_honba_sticks': count_of_honba_sticks, 'count_of_riichi_sticks': count_of_riichi_sticks,
                'dora_indicator': dora_indicator}

    def parse_final_scores_and_uma(self, message):
        tag = self._bs(message, 'agari')
        if not tag:
            tag = self._bs(message, 'ryuukyoku')

        data = tag.attrs['owari']
        data = [float(i) for i in data.split(',')]

        # start at the beginning at take every second item (even)
        scores = data[::2]
        # start at second item and take every second item (odd)
        uma = data[1::2]

        return {'scores': scores, 'uma': uma}

    def parse_un(self, message):
        tag = self._bs(message, 'un')

        is_reconnect = False
        ranks = []
        rates = []
        sexes = []
        try:
            ranks = [TenhouDecoder.RANKS[int(rank)] for rank in tag.attrs['dan'].split(',')]
            rates = [float(rate) for rate in tag.attrs['rate'].split(',')]
            sexes = tag.attrs['sx'].split(',')
        except KeyError:
            is_reconnect = True

        if not is_reconnect:
            names = [urllib.parse.unquote(tag.attrs['n{}'.format(n)]) for n in range(len(ranks))]
            return {'data': [{'name': names[n], 'rank': ranks[n], 'rate': rates[n], 'sex': sexes[n]} for n in
                             range(len(ranks))], 'is_reconnect': is_reconnect}
        else:
            names = [None for _ in range(4)]
            who = []
            for n in range(4):
                try:
                    urllib.parse.unquote(tag.attrs['n{}'.format(n)])
                    who.append(n)
                except KeyError:
                    pass
            return {'names': names, 'who': who, 'is_reconnect': is_reconnect}

    def parse_agari(self, message):
        return self._parse_end_of_hand(message, False)

    def parse_ryuukyoku(self, message):
        return self._parse_end_of_hand(message, True)

    def _parse_end_of_hand(self, message, ryuukyoku):
        tag = self._bs(message, 'ryuukyoku' if ryuukyoku else 'agari')

        if not ryuukyoku:
            hai = [[int(t) for t in tag.attrs['hai'].split(',')]]
            machi = int(tag.attrs['machi'])
            ten = [int(t) for t in tag.attrs['ten'].split(',')]
            yaku = []
            yakuman = []
            try:
                ykr = [int(t) for t in tag.attrs['yaku'].split(',')]
                # list is actually an (id, value) pair so let's turn that into a tuple list
                for idx in range(0, len(ykr), 2):
                    yaku.append((ykr[idx], ykr[idx + 1]))
            except KeyError:
                # In the case of a yakuman, yaku is not present
                pass
            try:
                ykr = [int(t) for t in tag.attrs['yakuman'].split(',')]
                # as above
                for idx in range(0, len(ykr), 2):
                    yakuman.append((ykr[idx], ykr[idx + 1]))
            except KeyError:
                pass
            dora_hai = [int(t) for t in tag.attrs['dorahai'].split(',')]
            try:
                dora_hai_ura = [int(t) for t in tag.attrs['dorahaiura'].split(',')]
            except KeyError:
                # No ura dora, probably because no riichi
                dora_hai_ura = []
            # TODO : Multiple ron?
            who = int(tag.attrs['who'])
            from_who = int(tag.attrs['fromwho'])
        else:
            # Present 'hai' tags are tenpai players showing their hands
            hai = [None for _ in range(4)]
            for n in range(4):
                hai_n = 'hai{}'.format(n)
                if hai_n in tag.attrs:
                    hai[n] = [int(t) for t in tag.attrs[hai_n].split(',')]
            # Initialise unused vars
            machi = yaku = yakuman = dora_hai = dora_hai_ura = who = from_who = ten = None

        ba = [int(b) for b in tag.attrs['ba'].split(',')]
        sc = [int(t) for t in tag.attrs['sc'].split(',')]
        # start at the beginning at take every second item (even)
        points = sc[::2]
        # start at the beginning at take every second item (even)
        point_exchange = sc[1::2]
        # owari tag is present if it is the end of the game
        owari = None
        if 'owari' in tag.attrs:
            data = [float(i) for i in tag.attrs['owari'].split(',')]
            # start at the beginning at take every second item (even)
            scores = data[::2]
            # start at second item and take every second item (odd)
            uma = data[1::2]
            owari = {'final_scores': scores, 'uma': uma}

        return {'ba': ba, 'hai': hai, 'machi': machi, 'ten': ten, 'yaku': yaku, 'yakuman': yakuman,
                'dora_hai': dora_hai, 'dora_hai_ura': dora_hai_ura, 'who': who, 'from_who': from_who, 'points': points,
                'point_exchange': point_exchange, 'owari': owari}

    def parse_shuffle(self, message):
        tag = self._bs(message, 'shuffle')
        seed = tag.attrs['seed']
        ref = tag.attrs['ref']
        return {'seed': seed, 'ref': ref}

    def parse_taikyoku(self, message):
        tag = self._bs(message, 'taikyoku')
        oya = int(tag.attrs['oya'])
        return {'oya': oya}

    def parse_go(self, message):
        tag = self._bs(message, 'go')
        game_mode = GameMode(int(tag.attrs['type']))
        lobby_id = int(tag.attrs['lobby'])
        return {'game_mode': game_mode, 'lobby_id': lobby_id}

    def parse_log_link(self, message):
        tag = self._bs(message, 'taikyoku')

        seat = int(tag.attrs['oya'])
        seat = (4 - seat) % 4
        game_id = tag.attrs['log']

        return game_id, seat

    def parse_tile(self, message):
        # tenhou format: <t23/>, <e23/>, <f23 t="4"/>, <f23/>, <g23/>
        # in live games, enemy draws will have no number, e.g. <u />, in those cases return `None`
        soup = BeautifulSoup(message, 'html.parser')
        tag = soup.findChildren()[0].name
        tile = tag.replace('t', '').replace('e', '').replace('f', '').replace('g', '').replace('u', '')
        tile = tile.replace('v', '').replace('w', '')
        try:
            return int(tile)
        except ValueError:
            return None

    def parse_tile_new(self, message):  # TODO: This method could be simplified
        # tenhou format: <t23/>, <e23/>, <f23 t="4"/>, <f23/>, <g23/>
        # in live games, enemy draws will have no number, e.g. <u />
        soup = BeautifulSoup(message, 'html.parser')
        tag = soup.findChildren()[0].name.lower()

        # Determine what tile it was
        tile = tag.replace('d', '').replace('e', '').replace('f', '').replace('g', '')
        tile = tile.replace('t', '').replace('u', '').replace('v', '').replace('w', '')
        try:
            tile_id = int(tile)
        except ValueError:
            tile_id = None

        # Determine who drew/discarded the tile
        if tag[0] in 'dt':
            who = 0
        elif tag[0] in 'eu':
            who = 1
        elif tag[0] in 'fv':
            who = 2
        elif tag[0] in 'gw':
            who = 3
        else:
            who = None

        # Determine whether it was a draw or a discard
        if tag[0] in 'tuvw':
            action = 'draw'
        elif tag[0] in 'defg':
            action = 'discard'
        else:
            action = None

        return {'tile': tile_id, 'who': who, 'action': action}

    def parse_meld(self, message):
        soup = BeautifulSoup(message, 'html.parser')
        data = soup.find('n').attrs['m']
        data = int(data)

        meld = Meld()
        meld.who = int(soup.find('n').attrs['who'])
        meld.from_who = data & 0x3

        if data & 0x4:
            self.parse_chi(data, meld)
        elif data & 0x18:
            self.parse_pon(data, meld)
        elif data & 0x20:
            self.parse_nuki(data, meld)
        else:
            self.parse_kan(data, meld)

        return meld

    def parse_chi(self, data, meld):
        meld.type = Meld.CHI
        t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
        base_and_called = data >> 10
        base = base_and_called // 3
        base = (base // 7) * 9 + base % 7
        meld.tiles = [Tile(t0 + 4 * (base + 0)), Tile(t1 + 4 * (base + 1)), Tile(t2 + 4 * (base + 2))]

    def parse_pon(self, data, meld):
        t4 = (data >> 5) & 0x3
        t0, t1, t2 = ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2))[t4]
        base_and_called = data >> 9
        base = base_and_called // 3
        if data & 0x8:
            meld.type = Meld.PON
            meld.tiles = [Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base)]
        else:
            meld.type = Meld.CHAKAN
            meld.tiles = [Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base)]

    def parse_kan(self, data, meld):
        base_and_called = data >> 8
        base = base_and_called // 4
        meld.type = Meld.KAN
        meld.tiles = [Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base)]

    def parse_nuki(self, data, meld):
        meld.type = Meld.NUKI
        meld.tiles = [Tile(data >> 8)]

    def parse_dora_indicator(self, message):
        tag = self._bs(message, 'dora')
        return int(tag.attrs['hai'])

    def parse_who_called_riichi(self, message):
        tag = self._bs(message, 'reach')
        return int(tag.attrs['who'])

    def parse_riichi(self, message):
        tag = self._bs(message, 'reach')
        who = int(tag.attrs['who'])
        step = int(tag.attrs['step'])
        if step == 2:
            ten = [int(x) for x in tag.attrs['ten'].split(',')]
        else:
            ten = None
        return {'who': who, 'step': step, 'ten': ten}

    def parse_bye(self, message):
        tag = self._bs(message, 'bye')
        who = int(tag.attrs['who'])
        return {'who': who}

    def generate_auth_token(self, auth_string):
        translation_table = [63006, 9570, 49216, 45888, 9822, 23121, 59830, 51114, 54831, 4189, 580, 5203, 42174, 59972,
                             55457, 59009, 59347, 64456, 8673, 52710, 49975, 2006, 62677, 3463, 17754, 5357]

        parts = auth_string.split('-')
        if len(parts) != 2:
            return False

        first_part = parts[0]
        second_part = parts[1]
        if len(first_part) != 8 and len(second_part) != 8:
            return False

        table_index = int('2' + first_part[2:8]) % (12 - int(first_part[7:8])) * 2

        a = translation_table[table_index] ^ int(second_part[0:4], 16)
        b = translation_table[table_index + 1] ^ int(second_part[4:8], 16)

        postfix = format(a, '2x') + format(b, '2x')

        result = first_part + '-' + postfix

        return result

    def message_to_event(self, message: str) -> Event:
        """Convert a Tenhou.net server (or replay) message into an event."""
        try:
            return self._message_to_event(message)
        except:
            logger.error('Error processing message: ' + message)
            raise

    def _message_to_event(self, message: str) -> Event:
        lower_msg = message.lower()
        if not lower_msg[0] == '<':  # They should all start with a <, ignore the ones that don't
            return None

        lower_msg = lower_msg[1:]  # Cut off the <
        if lower_msg.startswith('shuffle'):
            data = self.parse_shuffle(message)
            return GameEvent(GameEvents.RECV_SHUFFLE_SEED, data)
        elif lower_msg.startswith('go'):
            data = self.parse_go(message)
            return GameEvent(GameEvents.RECV_JOIN_TABLE, data)
        elif lower_msg.startswith('un'):
            data = self.parse_un(message)
            if data['is_reconnect']:
                return GameEvent(GameEvents.RECV_RECONNECTED, data)
            return GameEvent(GameEvents.RECV_PLAYER_DETAILS, data)
        elif lower_msg.startswith('taikyoku'):
            data = self.parse_taikyoku(message)
            return GameEvent(GameEvents.RECV_BEGIN_GAME, data)
        elif lower_msg.startswith('init'):
            data = self.parse_init(message)
            return GameEvent(GameEvents.RECV_BEGIN_HAND, data)
        elif lower_msg.startswith('reach'):
            data = self.parse_riichi(message)
            if data['step'] == 1:
                return GameEvent(GameEvents.RECV_RIICHI_DECLARED, data)
            elif data['step'] == 2:
                return GameEvent(GameEvents.RECV_RIICHI_STICK_PLACED, data)
        elif lower_msg.startswith('dora'):
            tile = self.parse_dora_indicator(message)
            return GameEvent(GameEvents.RECV_DORA_FLIPPED, {'tile': tile})
        elif lower_msg.startswith('agari'):
            data = self.parse_agari(message)
            return GameEvent(GameEvents.RECV_AGARI, data)
        elif lower_msg.startswith('ryuukyoku'):  # TODO: What about abortive draws?
            data = self.parse_ryuukyoku(message)
            return GameEvent(GameEvents.RECV_RYUUKYOKU, data)
        elif lower_msg.startswith('/mjloggm'):
            return GameEvent(GameEvents.END_OF_REPLAY)
        elif lower_msg.startswith('prof'):
            # Not sure what this msg does, but it seems to be safe to ignore
            return
        elif lower_msg.startswith('bye'):
            data = self.parse_bye(message)
            return GameEvent(GameEvents.RECV_DISCONNECTED, data)
        elif lower_msg[0] in 'n':  # MAKE SURE THESE BRANCHES ARE PROCESSED LAST
            meld = self.parse_meld(message)
            data = {'meld': meld}
            return GameEvent(GameEvents.RECV_CALL, data)
        elif lower_msg[0] in 'defgtuvw':  # MAKE SURE THESE BRANCHES ARE PROCESSED LAST
            data = self.parse_tile_new(message)
            if data['action'] == 'draw':
                return GameEvent(GameEvents.RECV_DRAW, data)
            elif data['action'] == 'discard':
                return GameEvent(GameEvents.RECV_DISCARD, data)
        raise NotImplementedError(message)
