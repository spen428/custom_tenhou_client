import time
from random import randint

import pygame

from mahjong.constants import NORTH
from mahjong.meld import Meld
from mahjong.player import Player
from mahjong.tile import Tile
from tenhou.gui.screens.in_game_ui import InGameScreen


class TestInGameScreen(InGameScreen):
    def __init__(self, client):
        super().__init__(client)
        self._test()

    def on_key_up(self, event):
        handled = super().on_key_up(event)
        if handled:
            return True
        if event.key == pygame.K_F5:
            self._test()
            return True
        return False

    def draw_to_canvas(self, canvas):
        super().draw_to_canvas(canvas)
        font = pygame.font.SysFont("Arial", 13)
        text = font.render("InGameScreen Test", 1, (0, 0, 0))
        canvas.blit(text, (0, 0))
        self.end_dialog_start_time = time.time()

    def _test(self):
        yaku_list = ['立直', '平和', 'ドラ１枚', '裏ドラ１枚']
        self.end_dialog_data = [{'title': '和了', 'yaku': yaku_list, 'points': (30, 4, 11600), 'yakuman': None},
                                {'title': '流局', 'yaku': [], 'points': None, 'yakuman': None},
                                {'title': '途中流局', 'yaku': [], 'points': None, 'yakuman': '九種九牌'}][randint(0, 2)]

        names = ["Dave", "Adam", "Rob", "Mark"]
        ranks = ["四段", "初段", "六段", "８級"]
        rates = [randint(1300, 2400) for _ in range(4)]
        sexes = [['M', 'F'][randint(0, 1)] for _ in range(4)]
        scores = [723, 82, 115, 232]
        players = []
        oya = randint(0, 3)

        for n in range(4):
            player = Player(n, oya, self.table)
            player.score = scores[n]
            players.append(player)

        self.table.init_round(3, 2, 1, Tile(randint(0, 135)), oya, [p.score for p in players])

        for n in range(4):
            player = self.table.players[n]
            player.name = names[n]
            player.rank = ranks[n]
            player.rate = rates[n]
            player.sex = sexes[n]
            player.seat = n
            # Hand
            player.tiles = sorted([Tile(randint(0, 135)) for _ in range(13)])
            # Discards
            for _ in range(21):
                tile_id = randint(0, 135)
                tile = Tile(tile_id)
                riichi = not bool(randint(0, 10))
                player.discards.append(tile)
                if riichi:
                    player.is_riichi = True
                    player.riichi_discards.append(tile)
            # Nuki
            meld = Meld()
            meld.who = n
            meld.from_who = randint(0, 3)
            meld.tiles = [Tile(NORTH) for _ in range(3)]
            meld.type = Meld.NUKI
            player.melds.append(meld)
            # Melds
            rs = [randint(0, 135) for _ in range(3)]
            rs.append(randint(0, 135 - 4))
            ts = [[Tile(rs[0]) for _ in range(4)], [Tile(rs[1]) for _ in range(4)], [Tile(rs[2]) for _ in range(3)],
                  [Tile(rs[3] + n) for n in range(3)]]
            ms = [Meld.KAN, Meld.KAN, Meld.KAN, Meld.CHI]
            for i in range(len(rs)):
                meld = Meld()
                meld.who = n
                meld.from_who = randint(0, 3)
                meld.tiles = ts[n]
                meld.type = ms[n]
                player.melds.append(meld)

            for btn in self.call_buttons:
                btn.available = bool(randint(0, 1))
