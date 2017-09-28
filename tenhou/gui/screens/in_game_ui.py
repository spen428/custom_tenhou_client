# coding: utf-8
import logging
import math
import os
import time

import pygame

import tenhou.gui
import tenhou.gui.gui
from mahjong.constants import WINDS_TO_STR
from mahjong.meld import Meld
from mahjong.table import Table
from mahjong.tile import Tile
from tenhou.decoder import GameMode
from tenhou.events import GameEvents, GAMEEVENT
from tenhou.gui.screens import MenuButton, AbstractScreen, EventListener
from tenhou.gui.screens.esc_menu import EscMenuScreen
from tenhou.jong.classes import CallType, Position
from tenhou.utils import seconds_to_time_string, calculate_score_deltas

logger = logging.getLogger('tenhou')


def rotate(origin, point, degrees):
    angle = math.radians(degrees)
    ox, oy = origin
    px, py = point
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def rotate_center(image, degrres):
    """Rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, degrres)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


def rotate_about(image, origin, degrees):
    """Rotate an image about a point"""
    raise NotImplementedError()


def _load_64px_tile_sprites():
    return __load_tile_sprites(False)


def _load_38px_tile_sprites():
    return __load_tile_sprites(True)


def __load_tile_sprites(small):
    """Load tile sprites from the resource directory. The tiles should be loaded in the following order: 1s 2s 3s 4s
    5s 6s 7s 8s 9s 1p 2p 3p 4p 5p 6p 7p 8p 9p 1m 2m 3m 4m 5m 6m 7m 8m 9m ton nan shaa pei haku hatsu chun 5sd 5pd 5md
    back

    :param small: whether to load the small tiles or the large tiles
    :return: a list of pygame images
    """
    tiles = []
    tile_dir = os.path.join(tenhou.gui.get_resource_dir(), "tiles_38" if small else "tiles_64")
    ext = "gif" if small else "png"
    for name in ('1s 2s 3s 4s 5s 6s 7s 8s 9s 1p 2p 3p 4p 5p 6p 7p 8p 9p 1m 2m 3m 4m 5m 6m 7m 8m '
                 '9m ton nan shaa pei haku hatsu chun 5sd 5pd 5md back').split():
        filename = "{}.{}".format(name, ext)
        img = pygame.image.load(os.path.join(tile_dir, filename)).convert_alpha()
        tiles.append(img)
    return tiles


def _load_wind_sprites():
    winds = []
    resource_dir = tenhou.gui.get_resource_dir()
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(os.path.join(resource_dir, wind + ".png")).convert_alpha()
        winds.append(img)
    return winds


class InGameScreen(AbstractScreen, EventListener):
    def __init__(self):
        self.table_name = None
        self.round_name = None
        self.game_mode = None
        self.game_mode_display_name = '麻雀'  # Placeholder name
        self.lobby_id = None
        self.has_red_fives = False

        # TILES
        self.tiles_64px = _load_64px_tile_sprites()
        self.tiles_38px = _load_38px_tile_sprites()

        # WINDS
        self.wind_sprites = _load_wind_sprites()
        self.riichi_stick_sprite = pygame.image.load(
            os.path.join(tenhou.gui.get_resource_dir(), "riichi_stick.png")).convert_alpha()

        # Call buttons
        self.call_buttons = [MenuButton("ロン", self._call_ron), MenuButton("ツモ", self._call_tsumo),
                             MenuButton("九種九牌", self._call_kyuushukyuuhai), MenuButton("抜く", self._call_nuku),
                             MenuButton("チー", self._call_chii), MenuButton("ポン", self._call_pon),
                             MenuButton("カン", self._call_kan), MenuButton("パス", self._call_pasu)]
        for btn in self.call_buttons:
            setattr(btn, "available", False)
        self._call_button_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 14)
        self._call_button_width_px = 120
        self._call_button_height_px = 40
        self._call_button_color_normal = (255, 255, 255)  # White
        self._call_button_color_hover = (255, 255, 100)  # Pale yellow

        # Graphics Consts
        self.tile_width = self._get_tile_image(0, True).get_width()
        self.tile_height = self._get_tile_image(0, True).get_height()
        self.hand_tile_width = self._get_tile_image(0, False).get_width()
        self.hand_tile_height = self._get_tile_image(0, False).get_height()
        self.tile_highlights = [
            pygame.image.load(os.path.join(tenhou.gui.get_resource_dir(), file_name)).convert_alpha() for file_name in
            "highlight-green.png highlight-red.png highlight-yellow.png highlight-grey.png 70perc-black.png".split()]
        self.tile_hover_colour = (255, 0, 0)
        self.corner_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 15)
        self.score_font = pygame.font.SysFont("Arial", 16)
        self.discard_timer_font = pygame.font.SysFont("Arial", 10)
        self.name_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 12)
        self.centre_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 12)
        self.call_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 28)
        self.end_dialog_title_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 34)
        self.end_dialog_yaku_font = pygame.font.Font(os.path.join(tenhou.gui.get_resource_dir(), "meiryo.ttc"), 16)

        # Graphics Vars
        self.tile_rects = []
        self.centre_hover = False
        self.centre_square = None
        self.hover_tile = None
        self.is_esc_menu_open = False
        self.start_time_secs = time.time()
        self.end_dialog_start_time = 0
        self.end_dialog_data = {}
        self._set_end_dialog()
        self.call_data = [None for _ in range(4)]

        # Consts
        self.END_DIALOG_SHOW_TIME_SECS = 5
        self.CALL_SHOW_TIME_SECS = 0.5

        # Test vars
        self.discard_start_secs = time.time()
        self.last_discarder = -1

        # Other
        self.esc_menu = EscMenuScreen()
        self.table: Table = Table()

    # Private methods #

    def _call_ron(self):
        pass

    def _call_tsumo(self):
        pass

    def _call_kyuushukyuuhai(self):
        pass

    def _call_nuku(self):
        pass

    def _call_chii(self):
        pass

    def _call_pon(self):
        pass

    def _call_kan(self):
        pass

    def _call_pasu(self):
        pass

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles_38px[tile_id]
        return self.tiles_64px[tile_id]

    def _get_tile_back(self, small=False):
        return self._get_tile_image(-1, small)

    def _toggle_esc_menu(self):
        self.hover_tile = None
        self.centre_hover = False
        self.is_esc_menu_open = not self.is_esc_menu_open

    def on_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.on_key_down(event)
        elif event.type == pygame.KEYUP:
            self.on_key_up(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.on_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            self.on_mouse_motion(event)
        elif event.type == pygame.VIDEORESIZE:
            self.on_window_resized(event)
        elif event.type == GAMEEVENT:
            self.on_game_event(event)

    def on_key_down(self, event):
        pass

    def on_key_up(self, event):
        if event.key == pygame.K_ESCAPE:
            self._toggle_esc_menu()
            return True
        return False

    def on_mouse_down(self, event):
        if self.is_esc_menu_open:
            self.esc_menu.on_mouse_down(event)

    def on_mouse_up(self, event):
        if self.is_esc_menu_open:
            self.esc_menu.on_mouse_up(event)
            return

        pos = pygame.mouse.get_pos()
        for btn in self.call_buttons:
            if btn.rect is not None and btn.rect.collidepoint(pos):
                if callable(btn.on_click):
                    btn.on_click()
                    break

    def on_mouse_motion(self, event):
        pos = pygame.mouse.get_pos()

        if self.is_esc_menu_open:
            self.esc_menu.on_mouse_motion(event)
            return

        # Clear hover state before starting search
        for btn in self.call_buttons:
            btn.hover = False
        self.hover_tile = None
        self.centre_hover = False

        # Search for hover state
        for btn in self.call_buttons:
            if btn.rect is not None and btn.rect.collidepoint(pos):
                btn.hover = True
                return

        if self.centre_square is not None:
            self.centre_hover = self.centre_square.collidepoint(pos)
            if self.centre_hover:
                return

        for rect in reversed(self.tile_rects):
            if rect.collidepoint(pos):
                self.hover_tile = rect
                return

    def on_window_resized(self, event):
        self.centre_square = None
        self.esc_menu.on_window_resized(event)

    def on_game_event(self, event):
        """Handle GameEvent events.

        :return: True if the event was handled, else False
        """
        logger.debug(event)
        if event.game_event == GameEvents.RECV_JOIN_TABLE:
            self.game_mode: GameMode = event.game_mode
            self.lobby_id = event.lobby_id
            self.has_red_fives = (not self.game_mode.noaka)
            self.game_mode_display_name = self.game_mode.display_name
        elif event.game_event == GameEvents.RECV_BEGIN_HAND:
            self.table.init_round(event.round_number, event.count_of_honba_sticks, event.count_of_riichi_sticks,
                                  event.dora_indicator, event.oya, event.ten)
            # If this is a live game, len(haipai) will be 1, in a replay it will be 4
            if len(event.haipai) == 1:
                # Extend with tile backs for other players' unknown tiles
                for n in range(1, 4):
                    event.haipai.append([-1 for _ in range(13)])
                # Mark player as invisibles
                    self.table.players[n].tiles_hidden = True
            for n in range(len(event.haipai)):
                self.table.players[n].init_hand(event.haipai[n])
            return True
        elif event.game_event == GameEvents.RECV_PLAYER_DETAILS:
            for n in range(len(event.data)):
                self.table.players[n].name = event.data[n]['name']
                self.table.players[n].rank = event.data[n]['rank']
                self.table.players[n].rate = event.data[n]['rate']
                self.table.players[n].sex = event.data[n]['sex']
            if len(event.data) == 3 or event.data[3]['name'] == '':
                # This is a 3-player game
                self.table.count_of_players = 3
            return True
        elif event.game_event == GameEvents.RECV_DISCARD:
            self.table.get_player(event.who).discard_tile(event.tile)
            self.last_discarder = event.who
            return True
        elif event.game_event == GameEvents.RECV_DRAW:
            self.table.get_player(event.who).draw_tile(event.tile)
            self.table.count_of_remaining_tiles -= 1
            if self.table.count_of_remaining_tiles < 0:
                raise ValueError('Wall count dropped below zero!')
            return True
        elif event.game_event == GameEvents.RECV_CALL:
            if event.meld.type in [Meld.CHI, Meld.PON, Meld.KAN]:
                self.table.get_player(self.last_discarder).call_discard()
            self.table.get_player(event.meld.who).add_meld(event.meld)
            string = {Meld.CHI: 'チー', Meld.PON: 'ポン', Meld.KAN: 'カン', Meld.NUKI: '北'}[event.meld.type]
            self._add_call(event.meld.who, string)
            return True
        elif event.game_event == GameEvents.RECV_RIICHI_DECLARED:
            player = self.table.get_player(event.who)
            player.is_riichi = True
            player.not_rotated_discard = True
            self._add_call(event.who, 'リーチ')
            return True
        elif event.game_event == GameEvents.RECV_RIICHI_STICK_PLACED:
            self.table.get_player(event.who).score -= 1000
            return True
        elif event.game_event == GameEvents.RECV_AGARI:
            fu = event.ten[0]
            han = 0  # TODO
            points = event.ten[1]
            yaku_list = ['Yaku #{}'.format(x) for x in event.yaku]
            yakuman_string = None  # TODO
            self._set_end_dialog('和了', yaku_list, fu, han, points, yakuman_string)
            self._add_call(event.who, 'ロン' if event.who != event.from_who else 'ツモ')
            return True
        elif event.game_event == GameEvents.RECV_RYUUKYOKU:
            for n in range(len(event.hai)):
                hai = event.hai[n]
                if hai is not None:
                    self.table.players[n].tiles = hai
                    self._add_call(n, 'テンパイ')
            self._set_end_dialog('流局')
            return True
        elif event.game_event == GameEvents.RECV_DORA_FLIPPED:
            self.table.add_dora_indicator(event.tile)
        return False

    def _get_round_name(self):
        round_num = (self.table.round_number % 4) + 1  # it starts from 0, so +1
        return '{}{}局'.format(WINDS_TO_STR[self.table.round_wind], round_num)

    def _get_discard_time(self):
        now = time.time()
        discard_time_secs = 4.0  # TODO
        return self.discard_start_secs + discard_time_secs - now

    def _get_bonus_name(self):
        if self.table.count_of_honba_sticks <= 0:
            return ""
        return "{}本場".format(self.table.count_of_honba_sticks)

    # Drawing methods #

    def draw_to_canvas(self, canvas):
        canvas_width = canvas.get_width()
        canvas_height = canvas.get_height()
        centre_x = canvas_width / 2
        centre_y = canvas_height / 2

        # Clear storage
        self.tile_rects = []
        if self._get_discard_time() <= 0:
            self.discard_start_secs = time.time()

        # initialise centre square shape
        if self.centre_square is None:
            width = self.tile_width * 6
            x = centre_x - width / 2
            y = centre_y - width / 2
            self.centre_square = pygame.Rect(x, y, width, width)

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2, canvas.get_height() - 25))

        # Render game
        self._draw_discards(canvas)
        self._draw_calls(canvas)
        self._draw_hand(canvas)
        self._draw_enemy_hands(canvas)
        self._draw_centre_console(canvas)

        if self.hover_tile is not None:
            self._draw_highlight(canvas, self.hover_tile, 0)

        self._draw_corner_info(canvas)
        self._draw_corner_text(canvas)

        # Draw call text
        self._draw_call_text(canvas)

        # Draw call buttons
        x = canvas_width - self._call_button_width_px - 20
        y = centre_y + self.tile_width * 6
        btn_h_spacing = 10  # Horizontal space between buttons
        for btn in reversed(self.call_buttons):
            if not btn.available:
                continue

            btn_color = self._call_button_color_hover if btn.hover else self._call_button_color_normal
            btn.rect = pygame.draw.rect(canvas, btn_color,
                                        (x, y, self._call_button_width_px, self._call_button_height_px), 0)
            btn_label = self._call_button_font.render(btn.text, 1, (0, 0, 0))
            label_x = x + (self._call_button_width_px / 2 - btn_label.get_width() / 2)
            label_y = y + (self._call_button_height_px / 2 - btn_label.get_height() / 2)
            canvas.blit(btn_label, (label_x, label_y))
            x -= btn_h_spacing + self._call_button_width_px

        # Draw end of hand dialog
        if time.time() < self.end_dialog_start_time + self.END_DIALOG_SHOW_TIME_SECS:
            self._draw_end_dialog(canvas)

        # Draw 'Esc' menu -- MUST BE CALLED LAST
        if self.is_esc_menu_open:
            self._draw_esc_menu(canvas)

    def _draw_enemy_hands(self, surface):
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2
        y = centre_y + self.tile_height * 8

        for player in self.table.players:
            if player.seat == 0:
                continue  # Don't draw self

            rotation = [0, -90, -180, 90][player.seat]
            tile_rotation = rotation
            if player.seat in [Position.SHIMOCHA, Position.KAMICHA]:
                tile_rotation += 180

            tiles = player.get_only_hand_tiles()
            total_width = self.tile_width * len(tiles)

            # Determine position and rotate into place
            x = centre_x - total_width / 2
            for tile in tiles:
                coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                self._draw_tile(surface, tile, coordinates, small=True, rotation=tile_rotation)
                x += self.tile_width

            # Draw tsumohai
            if player.tsumohai is not None:
                x += self.tile_width / 2
                coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                self._draw_tile(surface, player.tsumohai, coordinates, small=True, rotation=tile_rotation)

    def _draw_hand(self, canvas):  # TODO: This is an unreadable mess
        center_pos = (canvas.get_width() / 2, 7 * canvas.get_height() / 8)
        player = self.table.get_main_player()

        tiles = player.tiles
        skipped_tsumohai = not (player.tsumohai is not None)

        discard_time = self._get_discard_time()
        discard_timer_text = None
        if discard_time is not None:
            time_string = "{0:.2f}".format(discard_time)
            discard_timer_text = self.discard_timer_font.render(time_string, 1, (255, 255, 255))
        centre_x, centre_y = center_pos

        num_tiles = len(tiles)
        if player.tsumohai is not None:
            num_tiles -= 1
        total_width = self.hand_tile_width * num_tiles
        x = centre_x - (total_width / 2)
        y = canvas.get_height() - self.hand_tile_height - 30
        for tile in tiles:
            if not skipped_tsumohai and player.tsumohai == tile:
                # Don't draw the tsumohai here
                skipped_tsumohai = True
                continue
            self._draw_tile(canvas, tile, (x, y))
            x += self.hand_tile_width
        if player.tsumohai is not None:
            x += 0.5 * self.hand_tile_width
            self._draw_tile(canvas, player.tsumohai, (x, y))
            if discard_timer_text is not None:
                canvas.blit(discard_timer_text,
                            (x - discard_timer_text.get_width() / 2 + self.hand_tile_width / 2, y - 13))

    def _draw_tile(self, surface: pygame.Surface, tile, coordinates: (int, int), small: bool = False,
                   rotation: int = 0, highlight_id=None, sideways: bool = False):
        """
        Blit a tile to a surface.
        :param surface: the surface
        :param tile: the Tile or tile_sprite_id
        :param coordinates: where to blit the tile, as a tuple (x, y)
        :param small: whether the tile is small
        :param rotation: the rotation of the tile, in degrees
        :param highlight_id: the highlight id (if the tile is to be highlighted)
        :param sideways: whether the tile is to be rendered on its side (i.e. rotated 90 degrees)
        :return: None
        """
        if tile >= len(self.tiles_38px):
            tile = Tile(tile)
        if type(tile) == Tile:
            if tile.is_five() and self.has_red_fives:
                # 4 = 5s, 13 = 5p, 22 = 5m
                # Draw red five, the last 4 tile sprite ids are 5sd, 5pd, 5md, back_face
                tile_real = tile / 4
                if tile_real == 4:
                    tile_id = -2
                elif tile_real == 13:
                    tile_id = -3
                elif tile_real == 22:
                    tile_id = -4
                else:
                    tile_id = tile.normalised()
            else:
                tile_id = tile.normalised()
        elif tile is None or tile < 0:
            tile_id = self._get_tile_back(small)
        else:
            tile_id = tile

        x, y = coordinates
        tile_image = self._get_tile_image(tile_id, small)

        if sideways:
            rotation += 90
        if rotation is not 0:
            tile_image = pygame.transform.rotate(tile_image, rotation)
        surface.blit(tile_image, (x, y))
        rect = pygame.Rect(x, y, tile_image.get_width(), tile_image.get_height())
        self.tile_rects.append(rect)
        if highlight_id is not None:
            self._draw_highlight(surface, rect, highlight_id)

    def _draw_calls(self, surface: pygame.Surface) -> None:
        """
        Draw player meld calls to a Surface.
        :param surface: the surface to draw to
        :return: None
        """
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2

        for player in self.table.players:
            position = player.seat
            rotation = [0, -90, -180, -270][position]
            tile_rotation = rotation
            x = centre_x + self.tile_width * 10
            y = centre_y + self.tile_height * 7.5

            # Positioning hack
            if position in [Position.KAMICHA, Position.TOIMEN]:
                y += self.tile_height
            if position in [Position.SHIMOCHA, Position.TOIMEN]:
                x += self.tile_width
            if position in [Position.SHIMOCHA, Position.KAMICHA]:
                tile_rotation += 180

            for meld in player.melds:
                # Determine how many tiles to display
                num_tiles = len(meld.tiles)
                if meld.type == Meld.NUKI:
                    num_tiles = 1

                # Draw tiles
                for n in range(num_tiles):
                    is_call_tile = (meld.type is not Meld.NUKI and False)  # TODO
                    if is_call_tile:
                        # More positioning hacks
                        if position in [Position.SHIMOCHA, Position.TOIMEN]:
                            x += self.tile_height - self.tile_width
                        if position in [Position.TOIMEN, Position.KAMICHA]:
                            y -= self.tile_height - self.tile_width

                        # Adjust for rotation
                        x -= self.tile_height - self.tile_width
                        y += self.tile_height - self.tile_width
                        if meld.kan_type == CallType.SHOUMINKAN:
                            y -= self.tile_width
                            coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                            self._draw_tile(surface, meld.tiles[n], coordinates, True, tile_rotation, sideways=True)
                            y += self.tile_width
                            if n is not num_tiles - 1:
                                n += 1
                    coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                    self._draw_tile(surface, meld.tiles[n], coordinates, True, tile_rotation, sideways=is_call_tile)
                    if meld.kan_type == Meld.NUKI:
                        txt = "{}x".format(len(meld.tiles))
                        nuke_text = self.discard_timer_font.render(txt, 1, (0, 0, 0))
                        tx = x + self.tile_width / 2 - nuke_text.get_width() / 2
                        ty = y - nuke_text.get_height()

                        # Even more positioning hacks holy shit I've got to fix these
                        if position in [Position.SHIMOCHA, Position.TOIMEN]:
                            tx -= self.tile_width / 2 + nuke_text.get_width() / 2
                        if position in [Position.TOIMEN, Position.KAMICHA]:
                            ty -= nuke_text.get_height() * 2

                        nuke_text = pygame.transform.rotate(nuke_text, tile_rotation)
                        coordinates = rotate((centre_x, centre_y), (tx, ty), rotation)
                        surface.blit(nuke_text, coordinates)
                    x -= self.tile_width
                    if is_call_tile:
                        y -= self.tile_height - self.tile_width
                        # Undo positioning hacks
                        if position in [Position.SHIMOCHA, Position.TOIMEN]:
                            x -= self.tile_height - self.tile_width
                        if position in [Position.TOIMEN, Position.KAMICHA]:
                            y += self.tile_height - self.tile_width

    def _draw_discards(self, surface: pygame.Surface):
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2
        discard_offset = self.tile_height * 3.25

        for player in self.table.players:
            position = player.seat
            tiles = player.discards
            rotation = [0, -90, -180, -270][position]
            tile_rotation = rotation
            if position in [Position.SHIMOCHA, Position.KAMICHA]:
                tile_rotation += 180

            x_count = 0
            y_count = 0
            riichi_count = 0

            for tile in tiles:
                called = tile in player.called_discards
                if called:
                    continue  # Don't render called tiles
                riichi = tile in player.riichi_discards
                tsumogiri = False  # TODO: Determine which discards were tsumogiri

                x = centre_x + (x_count - 3) * self.tile_width
                y = centre_y + discard_offset + y_count * self.tile_height

                # Account for riichi tiles
                x += (self.tile_height - self.tile_width) * riichi_count
                if riichi:
                    riichi_count += 1  # Must appear AFTER the positioning adjustment above

                # Positioning hacks
                if position in [Position.SHIMOCHA, Position.TOIMEN]:
                    x += self.tile_width
                    if riichi:
                        x += self.tile_height - self.tile_width
                if position in [Position.TOIMEN, Position.KAMICHA]:
                    y += self.tile_height
                    if riichi:
                        y -= self.tile_height - self.tile_width

                # Rotate into place
                pos = rotate((centre_x, centre_y), (x, y), rotation)

                # Highlight tsumogiri
                hl = 3 if tsumogiri else None

                self._draw_tile(surface, tile, pos, True, tile_rotation, highlight_id=hl, sideways=riichi)
                x_count += 1
                if x_count == 6 and y_count < 2:
                    x_count = 0
                    y_count += 1
                    riichi_count = 0

    def _draw_corner_info(self, surface):
        y_offset = 20
        x = y = 2 * y_offset

        # Remaining tiles
        text = self.corner_font.render("残り牌数：" + str(self.table.count_of_remaining_tiles), 1, (0, 0, 0))
        surface.blit(text, (x, y))
        y += y_offset

        # Dora indicators
        text = self.corner_font.render("ドラ表示：", 1, (0, 0, 0))
        surface.blit(text, (x, y))
        dora_width = 16
        dora_height = 20
        dora_x_offset = 5
        dora_x = x + text.get_width()
        dora_y = y
        for dora in self.table.dora_indicators:
            tile_id = Tile(dora).normalised()
            img = self._get_tile_image(tile_id, small=True)
            img = pygame.transform.scale(img, (dora_width, dora_height))
            surface.blit(img, (dora_x, dora_y))
            dora_x += dora_x_offset + dora_width
        y += y_offset

        # Riichi stick count
        text = self.corner_font.render("立直棒数：" + str(self.table.count_of_riichi_sticks), 1, (0, 0, 0))
        surface.blit(text, (x, y))
        y += y_offset

    def _draw_corner_text(self, surface):
        """
        Render lines of text in the top right of the screen.
        :param surface: the surface to render to
        :return: None
        """
        time_delta_secs = 0
        if self.start_time_secs >= 0:
            time_delta_secs = int(time.time() - self.start_time_secs)  # Truncate milliseconds
        time_string = seconds_to_time_string(time_delta_secs)
        round_string = self._get_round_name() + self._get_bonus_name()
        lines = [time_string, self.game_mode_display_name, round_string]
        if self.table.count_of_riichi_sticks > 0:
            lines.append("立直棒{}本".format(self.table.count_of_riichi_sticks))
        if self.table.is_oorasu:
            lines.append("オーラス")

        canvas_width = surface.get_width()
        y_offset = 20
        x_offset = y = 2 * y_offset
        for line in lines:
            text = self.corner_font.render(line, 1, (0, 0, 0))
            x = canvas_width - text.get_width() - x_offset
            surface.blit(text, (x, y))
            y += y_offset

    def _draw_centre_console(self, surface: pygame.Surface):
        """
        Render the centre console, including player names, seat winds, round information, scores, and riichi sticks.
        :param surface: the surface to render to
        :return: None
        """
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2
        wind_offset = self.tile_height * 1.20
        score_offset = self.tile_height * 2.15
        name_offset = score_offset + 20
        riichi_offset = self.tile_height * 3.00

        # Calculate score deltas first
        scores = [p.score for p in self.table.players]
        score_deltas = calculate_score_deltas(scores)

        for player in self.table.players:
            position = player.seat
            if self.centre_hover:
                score_text = self.score_font.render(str(score_deltas[position]), 1, (0, 0, 0))
            else:
                score_text = self.score_font.render(str(scores[position]), 1, (0, 0, 0))
            name_text = self.name_font.render("{0}・{1}".format(player.name, player.rank), 1, (0, 0, 0))
            wind_sprite = self.wind_sprites[player.dealer_seat]
            riichi_sprite = self.riichi_stick_sprite
            wind_x = wind_y = score_x = score_y = riichi_x = riichi_y = name_x = name_y = 0

            if position == Position.JIBUN:
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y + wind_offset - wind_sprite.get_height() / 2
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y + score_offset - score_text.get_height() / 2
                name_x = centre_x - name_text.get_width() / 2
                name_y = centre_y + name_offset - name_text.get_height() / 2
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y + riichi_offset - riichi_sprite.get_height() / 2
            elif position == Position.SHIMOCHA:
                wind_sprite = pygame.transform.rotate(wind_sprite, 90)
                wind_x = centre_x + wind_offset - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, 90)
                score_x = centre_x + score_offset - score_text.get_width() / 2
                score_y = centre_y - score_text.get_height() / 2
                name_text = pygame.transform.rotate(name_text, 90)
                name_x = centre_x + name_offset - name_text.get_width() / 2
                name_y = centre_y - name_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, 90)
                riichi_x = centre_x + riichi_offset - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_sprite.get_height() / 2
            elif position == Position.TOIMEN:
                wind_sprite = pygame.transform.rotate(wind_sprite, 180)
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_offset - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, 180)
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y - score_offset - score_text.get_height() / 2
                name_text = pygame.transform.rotate(name_text, 180)
                name_x = centre_x - name_text.get_width() / 2
                name_y = centre_y - name_offset - name_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, 180)
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_offset - riichi_sprite.get_height() / 2
            elif position == Position.KAMICHA:
                wind_sprite = pygame.transform.rotate(wind_sprite, -90)
                wind_x = centre_x - wind_offset - wind_sprite.get_width() / 2
                wind_y = centre_y - wind_sprite.get_height() / 2
                score_text = pygame.transform.rotate(score_text, -90)
                score_x = centre_x - score_offset - score_text.get_width() / 2
                score_y = centre_y - score_text.get_height() / 2
                name_text = pygame.transform.rotate(name_text, -90)
                name_x = centre_x - name_offset - name_text.get_width() / 2
                name_y = centre_y - name_text.get_height() / 2
                riichi_sprite = pygame.transform.rotate(riichi_sprite, -90)
                riichi_x = centre_x - riichi_offset - riichi_sprite.get_width() / 2
                riichi_y = centre_y - riichi_sprite.get_height() / 2

            surface.blit(wind_sprite, (wind_x, wind_y))
            surface.blit(score_text, (score_x, score_y))
            surface.blit(name_text, (name_x, name_y))
            if player.is_riichi:
                surface.blit(riichi_sprite, (riichi_x, riichi_y))

            centre_text_line0 = self.centre_font.render(self._get_round_name(), 1, (0, 0, 0))
            surface.blit(centre_text_line0,
                         (centre_x - centre_text_line0.get_width() / 2, centre_y - centre_text_line0.get_height()))
            centre_text_line1 = self.centre_font.render(self._get_bonus_name(), 1, (0, 0, 0))
            surface.blit(centre_text_line1, (centre_x - centre_text_line1.get_width() / 2, centre_y))

    def _draw_highlight(self, surface: pygame.Surface, rect: pygame.Rect, highlight_id: int):
        """
        Highlight a rectangle with the specified highlight id
        :param surface: the surface
        :param rect: the rectangle
        :param highlight_id: the highlight id
        :return: None
        """
        hl = pygame.transform.scale(self.tile_highlights[highlight_id], (rect.width, rect.height))
        surface.blit(hl, (rect.x, rect.y))

    def _draw_esc_menu(self, surface: pygame.Surface):
        # Fade everything else
        self._draw_highlight(surface, pygame.Rect(0, 0, surface.get_width(), surface.get_height()), 4)
        self.esc_menu.draw_to_canvas(surface)

    def _set_end_dialog(self, title=None, yaku_list=None, fu=None, han=None, points=None, yakuman_string=None):
        if yaku_list is None:
            yaku_list = []
        points_tuple = None if None in (fu, han, points) else (fu, han, points)
        self.end_dialog_data = {'title': title, 'yaku': yaku_list, 'points': points_tuple, 'yakuman': yakuman_string}
        if title is not None:
            self.end_dialog_start_time = time.time()

    def _draw_end_dialog(self, canvas):
        yaku_list = self.end_dialog_data['yaku']

        dialog_width = 500
        dialog_height = (len(yaku_list)) * 20
        if self.end_dialog_data['title'] is not None:
            dialog_height += 70
        if len(yaku_list) > 0:
            dialog_height += 40
        if self.end_dialog_data['points'] is not None:
            dialog_height += 20
        if self.end_dialog_data['yakuman'] is not None:
            dialog_height += 30

        centre_x = canvas.get_width() / 2
        centre_y = canvas.get_height() / 2
        x = centre_x - dialog_width / 2
        y = centre_y - dialog_height / 2
        self._draw_highlight(canvas, pygame.Rect(x, y, dialog_width, dialog_height), 3)
        self._draw_highlight(canvas, pygame.Rect(x, y, dialog_width, dialog_height),
                             3)  # Drawn twice for extra darkness
        # Title
        text = self.end_dialog_title_font.render(self.end_dialog_data['title'], 1, (255, 255, 255))
        x = centre_x - text.get_width() / 2
        y += 10
        canvas.blit(text, (x, y))
        y += 40
        # Yaku
        if len(yaku_list) > 0:
            for yaku in yaku_list:
                y += 20
                text = self.end_dialog_yaku_font.render(yaku, 1, (255, 255, 255))
                x = centre_x - text.get_width() / 2
                canvas.blit(text, (x, y))
        # Points
        if self.end_dialog_data['points'] is not None:
            fu, han, points = self.end_dialog_data['points']
            text = self.end_dialog_yaku_font.render("{}符 {}翻".format(fu, han), 1, (255, 255, 255))
            x = centre_x - text.get_width() - 10
            y += 40
            canvas.blit(text, (x, y))
            text = self.end_dialog_yaku_font.render("{}点".format(points), 1, (255, 255, 255))
            x = centre_x + 10
            canvas.blit(text, (x, y))
        # Yakuman string
        elif self.end_dialog_data['yakuman'] is not None:
            y += 15
            text = self.end_dialog_yaku_font.render(self.end_dialog_data['yakuman'], 1, (255, 255, 255))
            x = centre_x - text.get_width() / 2
            canvas.blit(text, (x, y))

    def _draw_call_text(self, canvas):
        centre_x = canvas.get_width() / 2
        centre_y = canvas.get_height() / 2
        for n in range(len(self.call_data)):
            if self.call_data[n] is None:
                continue
            start_time, string = self.call_data[n]
            if time.time() < start_time + self.CALL_SHOW_TIME_SECS:
                text = self.call_font.render(string, 1, (255, 255, 255))
                x = centre_x - text.get_width() / 2
                y = centre_y * 2 * 7 / 8
                coordinates = rotate((centre_x, centre_y), (x, y), [0, -90, 180, 90][n])
                text = pygame.transform.rotate(text, [0, 90, 180, -90][n])
                canvas.blit(text, coordinates)
            else:
                self.call_data[n] = None  # Erase expired call

    def _add_call(self, who, string):
        self.call_data[who] = (time.time(), string)
