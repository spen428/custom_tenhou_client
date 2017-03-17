# -*- coding: utf-8 -*-
import urllib
from urllib.parse import unquote

from bs4 import BeautifulSoup
from pygame.event import Event

from mahjong.meld import Meld
from mahjong.tile import Tile
from tenhou.events import GameEvents


def _bs(message, tag_name):
    soup = BeautifulSoup(message, 'html.parser')
    return soup.find(tag_name)


class TenhouDecoder(object):
    RANKS = [u'新人', u'9級', u'8級', u'7級', u'6級', u'5級', u'4級', u'3級', u'2級', u'1級', u'初段', u'二段', u'三段', u'四段', u'五段',
             u'六段', u'七段', u'八段', u'九段', u'十段', u'天鳳位']

    def parse_auth_string(self, message):
        tag = _bs('helo')
        if tag and 'auth' in tag.attrs:
            return tag.attrs['auth']
        else:
            return None

    def parse_initial_values(self, message):
        """
        Six element list:
            - Round number,
            - Number of honba sticks,
            - Number of riichi sticks,
            - First dice minus one,
            - Second dice minus one,
            - Dora indicator.
        """

        tag = _bs('init')

        seed = tag.attrs['seed'].split(',')
        seed = [int(i) for i in seed]

        round_number = seed[0]
        count_of_honba_sticks = seed[1]
        count_of_riichi_sticks = seed[2]
        dora_indicator = seed[5]
        dealer = int(tag.attrs['oya'])

        scores = tag.attrs['ten'].split(',')
        scores = [int(i) for i in scores]

        return {'round_number': round_number, 'count_of_honba_sticks': count_of_honba_sticks,
                'count_of_riichi_sticks': count_of_riichi_sticks, 'dora_indicator': dora_indicator, 'dealer': dealer,
                'scores': scores}

    def parse_initial_hand(self, message):
        tag = _bs('init')

        tiles = tag.attrs['hai']
        tiles = [int(i) for i in tiles.split(',')]

        return tiles

    def parse_init(self, message):
        tag = _bs('init')

        seed = [int(s) for s in tag.attrs['seed'].split(',')]
        ten = [int(p) * 100 for p in tag.attrs['ten'].split(',')]  # Points are sent divided by 100; reverse that
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
            tiles = [int(i) for i in tiles.split(',')]
            haipai.append(tiles)

        return seed, ten, oya, haipai

    def parse_final_scores_and_uma(self, message):
        tag = _bs('agari')
        if not tag:
            tag = _bs('ryuukyoku')

        data = tag.attrs['owari']
        data = [float(i) for i in data.split(',')]

        # start at the beginning at take every second item (even)
        scores = data[::2]
        # start at second item and take every second item (odd)
        uma = data[1::2]

        return {'scores': scores, 'uma': uma}

    def parse_names_and_ranks(self, message):
        tag = _bs('un')

        ranks = [TenhouDecoder.RANKS[int(rank)] for rank in tag.attrs['dan'].split(',')]
        names = [urllib.parse.unquote(tag.attrs['n{}'.format(n)]) for n in range(len(ranks))]
        rates = [float(rate) for rate in tag.attrs['rate'].split(',')]
        sexes = tag.attrs['sx'].split(',')

        return [{'name': names[n], 'rank': ranks[n], 'rate': rates[n], 'sex': sexes[n]} for n in range(len(ranks))]

    def parse_agari(self, message):
        tag = _bs('agari')

        ba = [int(b) for b in tag.attrs['ba'].split(',')]
        hai = [int(t) for t in tag.attrs['hai'].split(',')]
        machi = int(tag.attrs['machi'])
        ten = [int(t) for t in tag.attrs['ten'].split(',')]
        yaku = [int(t) for t in tag.attrs['yaku'].split(',')]
        dora_hai = [int(t) for t in tag.attrs['doraHai'].split(',')]
        dora_hai_ura = [int(t) for t in tag.attrs['doraHaiUra'].split(',')]
        # TODO : Multiple ron?
        who = int(tag.attrs['who'])
        from_who = int(tag.attrs['fromWho'])
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

        return {'ba': ba, 'hai': hai, 'machi': machi, 'ten': ten, 'yaku': yaku, 'dora_hai': dora_hai,
                'dora_hai_ura': dora_hai_ura, 'who': who, 'from_who': from_who, 'points': points,
                'point_exchange': point_exchange, 'owari': owari}

    def parse_ryuukyoku(self, message):
        tag = _bs(message, 'ryuukyoku')
        raise NotImplementedError()

    def parse_shuffle(self, message):
        tag = _bs(message, 'shuffle')
        seed = tag.attrs['seed']
        ref = tag.attrs['ref']
        return {'seed': seed, 'ref': ref}

    def parse_taikyoku(self, message):
        tag = _bs(message, 'taikyoku')
        oya = int(tag.attrs['oya'])
        return {'oya': oya}

    def parse_go(self, message):
        tag = _bs(message, 'go')
        game_type = int(tag.attrs['type'])
        lobby_id = int(tag.attrs['lobby'])
        return {'type': game_type, 'lobby': lobby_id}

    def parse_log_link(self, message):
        tag = _bs(message, 'taikyoku')

        seat = int(tag.attrs['oya'])
        seat = (4 - seat) % 4
        game_id = tag.attrs['log']

        return game_id, seat

    def parse_tile(self, message):
        # tenhou format: <t23/>, <e23/>, <f23 t="4"/>, <f23/>, <g23/>
        soup = BeautifulSoup(message, 'html.parser')
        tag = soup.findChildren()[0].name
        tile = tag.replace('t', '').replace('e', '').replace('f', '').replace('g', '')
        return int(tile)

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
        tag = _bs('dora')
        return int(tag.attrs['hai'])

    def parse_who_called_riichi(self, message):
        tag = _bs('reach')
        return int(tag.attrs['who'])

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
        lower_msg = message.lower()
        if lower_msg.startswith('<shuffle'):
            data = self.parse_shuffle(message)
            return Event(GameEvents.RECV_SHUFFLE_SEED, data)
        elif lower_msg.startswith('<go'):
            data = self.parse_go(message)
            return Event(GameEvents.RECV_JOIN_TABLE, data)
        elif lower_msg.startswith('<un'):
            data = self.parse_names_and_ranks(message)
            return Event(GameEvents.RECV_PLAYER_DETAILS, data)
        elif lower_msg.startswith('<taikyoku'):
            data = self.parse_taikyoku(message)
            return Event(GameEvents.RECV_BEGIN_GAME, data)
        elif lower_msg.startswith('<init'):
            seed, ten, oya, haipai = self.parse_init(message)
            return Event(GameEvents.RECV_BEGIN_HAND, {'seed': seed, 'ten': ten, 'oya': oya, 'haipai': haipai})
        elif lower_msg.startswith('<reach'):
            who_called_riichi = self.parse_who_called_riichi(message)
            return Event(GameEvents.RECV_RIICHI_DECLARED, {'player': who_called_riichi})
        elif lower_msg.startswith('<dora'):
            tile = self.parse_dora_indicator(message)
            return Event(GameEvents.RECV_DORA_FLIPPED, {'tile': tile})
        elif lower_msg.startswith('<agari'):
            data = self.parse_agari(message)
            return Event(GameEvents.RECV_AGARI, data)
        elif lower_msg.startswith('<ryuukyoku'):  # TODO: What about abortive draws?
            data = self.parse_ryuukyoku(message)
            return Event(GameEvents.RECV_RYUUKYOKU, data)
        elif lower_msg.startswith('<n'):
            raise NotImplementedError()
        elif lower_msg.startswith('<'):
            return None
