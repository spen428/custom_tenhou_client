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

RYUUKYOKU_EXHAUSTIVE_DRAW = None
RYUUKYOKU_KYUUSHU = 'yao9'
RYUUKYOKU_FOUR_RIICHI = 'reach4'
RYUUKYOKU_TRIPLE_RON = 'ron3'
RYUUKYOKU_FOUR_KAN = 'kan4'
RYUUKYOKU_FOUR_WINDS = 'kaze4'
RYUUKYOKU_NAGASHI_MANGAN = 'nm'


# http://arcturus.su/~alvin/docs/tenhoudoc/commands.html
# http://arcturus.su/~alvin/docs/tenhoudoc/values.html

class TenhouDecoder(object):
    RANKS = [u'新人', u'9級', u'8級', u'7級', u'6級', u'5級', u'4級', u'3級', u'2級', u'1級', u'初段', u'二段', u'三段', u'四段', u'五段',
             u'六段', u'七段', u'八段', u'九段', u'十段', u'天鳳位']

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

    def parse_reinit(self, message):
        pass

    def parse_init(self, message, reinit=False):
        if reinit:
            tag = self._bs(message, 'reinit')
        else:
            tag = self._bs(message, 'init')

        seed = [int(s) for s in tag.attrs['seed'].split(',')]
        round_number = seed[0]
        count_of_honba_sticks = seed[1]
        count_of_riichi_sticks = seed[2]
        dora_indicator = seed[5]
        kawa = []

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

        if reinit:
            kawas = ['kawa{}'.format(n) for n in range(len(ten))]
            for k in kawas:
                try:
                    tiles = tag.attrs[k]
                    if tiles == "":
                        tiles = []
                    else:
                        tiles = [int(i) for i in tiles.split(',')]
                except KeyError:
                    tiles = []
                kawa.append(tiles)

        return {'seed': seed, 'ten': ten, 'oya': oya, 'haipai': haipai, 'round_number': round_number,
                'count_of_honba_sticks': count_of_honba_sticks, 'count_of_riichi_sticks': count_of_riichi_sticks,
                'dora_indicator': dora_indicator, 'kawa': kawa}

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
            try:
                yakulist = [int(t) for t in tag.attrs['yaku'].split(',')]
                yaku_ids = yakulist[::2]
                yaku_han = yakulist[1::2]
                yaku = list(zip(yaku_ids, yaku_han))
            except KeyError:
                # In the case of a yakuman, yaku is not present
                yaku = []
            try:
                yakuman = [int(t) for t in tag.attrs['yakuman'].split(',')]
            except KeyError:
                yakuman = []
            dora_hai = [int(t) for t in tag.attrs['dorahai'].split(',')]
            try:
                dora_hai_ura = [int(t) for t in tag.attrs['dorahaiura'].split(',')]
            except KeyError:
                # No ura dora, probably because no riichi
                dora_hai_ura = []
            who = int(tag.attrs['who'])
            from_who = int(tag.attrs['fromwho'])
            # Init unused
            ryuukyoku_type = None
        else:
            # Present 'hai' tags are tenpai players showing their hands
            hai = [None for _ in range(4)]
            for n in range(4):
                hai_n = 'hai{}'.format(n)
                if hai_n in tag.attrs:
                    hai[n] = [int(t) for t in tag.attrs[hai_n].split(',')]
            # Try to get 'type' tag, which exists for abortive draws
            try:
                ryuukyoku_type = tag.attrs['type']
            except KeyError:
                ryuukyoku_type = None
            # Initialise unused vars
            machi = yaku = yakuman = dora_hai = dora_hai_ura = who = from_who = ten = None

        ba = [int(b) for b in tag.attrs['ba'].split(',')]
        sc = [int(t) for t in tag.attrs['sc'].split(',')]
        # start at the beginning at take every second item (even)
        points = sc[::2]
        # start at the beginning at take every second item (odd)
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
                'point_exchange': point_exchange, 'owari': owari, 'ryuukyoku_type': ryuukyoku_type}

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
        game_type = int(tag.attrs['type'])
        lobby_id = int(tag.attrs['lobby'])
        return {'type': game_type, 'lobby': lobby_id}

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

    def parse_tile_new(self, message):
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
        elif data & 2:
            # 0b1100100001110010 = chun shouminkan, extended middle
            meld.type = Meld.SHOUMINKAN
            meld.tiles = [Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base)]

    def parse_kan(self, data, meld):
        base_and_called = data >> 8
        base = base_and_called // 4
        if data & 3:
            meld.type = Meld.DAIMINKAN
        else:
            meld.type = Meld.ANKAN
        meld.tiles = [Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base)]
        # 0b0111111000000011 = haku daiminkan, stole from left
        # 0b0110010000000000 = ankan

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
        elif lower_msg.startswith('reinit'):
            data = self.parse_reinit(message)
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
        elif lower_msg.startswith('ryuukyoku'):
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
