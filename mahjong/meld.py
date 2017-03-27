# -*- coding: utf-8 -*-


class Meld(object):
    CHI = 'chi'
    PON = 'pon'
    SHOUMINKAN = 'shouminkan'
    DAIMINKAN = 'daiminkan'
    ANKAN = 'ankan'
    CHAKAN = 'chakan'
    NUKI = 'nuki'

    who = None
    tiles = []
    call_tile = None
    type = None
    from_who = None

    def __str__(self):
        return 'Who: {0}, Type: {1}, Tiles: {2}'.format(self.who, self.type, self.tiles)

    # for calls in array
    def __repr__(self):
        return self.__str__()

    def is_kan(self):
        return self.type in [Meld.ANKAN, Meld.SHOUMINKAN, Meld.DAIMINKAN]
