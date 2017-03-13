# coding: utf-8
import math
import os
import time
from random import randint

import pygame

import tenhou.gui.main
from tenhou.gui.screens import AbstractScreen, MenuButton
from tenhou.gui.screens.esc_menu import EscMenuScreen
from tenhou.jong.classes import Call, CallType, Position, Player
from tenhou.utils import calculate_score_deltas, seconds_to_time_string

DEBUG = True


def rotate(origin, point, degrees):
    angle = math.radians(degrees)
    ox, oy = origin
    px, py = point
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def _load_64px_tile_sprites():
    tiles = []
    resource_dir = tenhou.gui.main.get_resource_dir()
    # suited tiles
    for suit in ["bamboo", "man", "pin"]:
        for number in range(1, 10):
            name = "{}{}.png".format(suit, number)
            img = pygame.image.load(os.path.join(resource_dir, "tiles_64", name))
            tiles.append(img)
        # dora fives
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "red-dora-" + suit + "5.png"))
        tiles.append(img)

    # honour tiles
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "wind-" + wind + ".png"))
        tiles.append(img)
    for dragon in ["chun", "haku", "hatsu"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "dragon-" + dragon + ".png"))
        tiles.append(img)

    # back of tile
    img = pygame.image.load(os.path.join(resource_dir, "tiles_64", "face-down.png"))
    tiles.append(img)
    return tiles


def _load_38px_tile_sprites():
    tiles = []
    resource_dir = tenhou.gui.main.get_resource_dir()
    # suited tiles
    for suit in "SMP":
        for number in range(1, 10):
            name = "{}{}.gif".format(suit, number)
            img = pygame.image.load(os.path.join(resource_dir, "tiles_38", name))
            tiles.append(img)
        # dora fives
        img = pygame.image.load(os.path.join(resource_dir, "tiles_38", suit + "5d.gif"))
        tiles.append(img)

    # honour tiles
    for tile in ["E", "S", "W", "N", "D1", "D2", "D3"]:
        img = pygame.image.load(os.path.join(resource_dir, "tiles_38", tile + ".gif"))
        tiles.append(img)

    # back of tile
    img = pygame.image.load(os.path.join(resource_dir, "tiles_38", "back.gif"))
    tiles.append(img)
    return tiles


def _load_wind_sprites():
    winds = []
    resource_dir = tenhou.gui.main.get_resource_dir()
    for wind in ["east", "south", "west", "north"]:
        img = pygame.image.load(os.path.join(resource_dir, wind + ".png"))
        winds.append(img)
    return winds


class InGameScreen(AbstractScreen):
    def __init__(self, client):
        self.table_name = None
        self.round_name = None
        self.client = client
        # TILES 64
        self.tiles_64px = _load_64px_tile_sprites()
        # TILES 38
        self.tiles_38px = _load_38px_tile_sprites()
        # WINDS
        self.wind_sprites = _load_wind_sprites()
        self.riichi_stick_sprite = pygame.image.load(
            os.path.join(tenhou.gui.main.get_resource_dir(), "riichi_stick.png"))
        # Call buttons
        self.call_buttons = [MenuButton("ロン", self._call_ron), MenuButton("ツモ", self._call_tsumo),
                             MenuButton("九種九牌", self._call_kyuushukyuuhai), MenuButton("抜く", self._call_nuku),
                             MenuButton("チー", self._call_chii), MenuButton("ポン", self._call_pon),
                             MenuButton("カン", self._call_kan), MenuButton("パス", self._call_pasu)]
        for btn in self.call_buttons:
            setattr(btn, "available", False)
        self._call_button_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 14)
        self._call_button_width_px = 120
        self._call_button_height_px = 40
        self._call_button_color_normal = (255, 255, 255)  # White
        self._call_button_color_hover = (255, 255, 100)  # Pale yellow
        # Other
        self.tile_rects = []
        self.step = 0
        self.centre_hover = False
        self.centre_square = None
        self.hover_tile = None
        self.tile_hover_colour = (255, 0, 0)
        self.corner_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 15)
        self.score_font = pygame.font.SysFont("Arial", 16)
        self.discard_timer_font = pygame.font.SysFont("Arial", 10)
        self.name_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 12)
        self.centre_font = pygame.font.Font(os.path.join(tenhou.gui.main.get_resource_dir(), "meiryo.ttc"), 12)
        self.start_time_secs = time.time()
        self.discard_start_secs = time.time()
        self.tile_highlights = [
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-green.png")),
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-red.png")),
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-yellow.png")),
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "highlight-grey.png")),
            pygame.image.load(os.path.join(tenhou.gui.main.get_resource_dir(), "70perc-black.png"))]
        self.is_esc_menu_open = False
        self.esc_menu = EscMenuScreen(self.client)
        self.players = []

        self._test()

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

    def _test(self):
        names = ["Dave", "てつやち", "藤田プロ", "Mark"]
        ranks = ["四段", "初段", "八段", "２級"]
        scores = [72300, 8200, 11500, 23200]
        seats = [0, 1, 2, 3]

        self.players = [None for _ in range(4)]
        for n in range(4):
            player = self.players[n] = Player(names[n], ranks[n])
            # Discards
            for _ in range(21):
                tile_id = tile_sprite_id = randint(0, len(self.tiles_38px) - 2)
                riichi = not bool(randint(0, 10))
                tsumogiri = not bool(randint(0, 5))
                player.discards.append((tile_id, tile_sprite_id, riichi, tsumogiri))
            # Calls / Nuku
            call = Call([len(self.tiles_38px) - 5 for _ in range(3)], 0, CallType.NUKE)
            player.calls.append(call)
            r = [randint(0, len(self.tiles_38px) - 2) for _ in range(3)]
            r.append(randint(0, len(self.tiles_38px) - 6))
            player_calls = [Call([r[0] for _ in range(4)], randint(0, 3), CallType.SHOUMINKAN),
                            Call([r[1] for _ in range(4)], randint(0, 3), CallType.DAIMINKAN),
                            Call([r[2] for _ in range(3)], randint(0, 2), CallType.PON),
                            Call([r[3] + n for n in range(3)], randint(0, 2), CallType.CHII)]
            player.calls.extend(player_calls)
            # Hand
            player.hand_tiles = [-1 for _ in range(13)]
            # Etc
            player.score = scores[n]
            player.seat = seats[n]
            player.is_riichi = bool(randint(0, 1))
        self.players[0].hand_tiles = [2, 2, 2, 3, 3, 3, 4, 4, 4, 6, 6, 8, 8]  # Player 1's hand

        self.table_name = "東風戦喰速赤"
        self.round_name = "東四局二本"

        for btn in self.call_buttons:
            btn.available = bool(randint(0, 1))

    def _get_tile_image(self, tile_id, small=False):
        if small:
            return self.tiles_38px[tile_id]
        return self.tiles_64px[tile_id]

    def _toggle_esc_menu(self):
        self.hover_tile = None
        self.centre_hover = False
        self.is_esc_menu_open = not self.is_esc_menu_open

    # Superclass methods #

    def on_key_down(self, event):
        pass

    def on_key_up(self, event):
        if event.key == pygame.K_ESCAPE:
            self._toggle_esc_menu()
        if DEBUG and event.key == pygame.K_F5:
            self._test()

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

    def draw_to_canvas(self, canvas):
        canvas_width = canvas.get_width()
        canvas_height = canvas.get_height()
        centre_x = canvas_width / 2
        centre_y = canvas_height / 2

        tile_img = self._get_tile_image(0, True)
        tile_width = tile_img.get_width()
        # tile_height = tile_img.get_height()

        # Clear storage
        self.tile_rects = []
        if self._get_discard_time() <= 0:
            self.discard_start_secs = time.time()

        # initialise centre square shape
        if self.centre_square is None:
            width = tile_width * 6
            x = centre_x - width / 2
            y = centre_y - width / 2
            self.centre_square = pygame.Rect(x, y, width, width)

        # draw footer text
        footer_font = pygame.font.SysFont("Arial", 13)
        footer_text = footer_font.render("Custom client for Tenhou.net by lykat 2017", 1, (0, 0, 0))
        canvas.blit(footer_text, (canvas.get_width() / 2 - footer_text.get_width() / 2, canvas.get_height() - 25))

        for n in range(4):
            player = self.players[n]
            self._draw_discards(canvas, player.discards, n)
            self._draw_calls(canvas, player.calls, n)
        self._draw_hand(canvas, (canvas.get_width() / 2, 7 * canvas.get_height() / 8), self.players[0].hand_tiles, 22)
        self._draw_centre_console(canvas, self.players)

        if self.hover_tile is not None:
            self._draw_highlight(canvas, self.hover_tile, 0)

        time_delta_secs = int(time.time() - self.start_time_secs)  # Truncate milliseconds
        time_string = seconds_to_time_string(time_delta_secs)

        oorasu_string = "オーラス" if self._is_oorasu() else ""
        lines = [time_string, self.table_name, self.round_name, oorasu_string]
        self._draw_corner_text(canvas, lines)

        # Draw call buttons
        x = canvas_width - self._call_button_width_px - 20
        y = centre_y + tile_width * 6
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

        # Draw 'Esc' menu -- MUST BE CALLED LAST
        if self.is_esc_menu_open:
            self._draw_esc_menu(canvas)

    # Game information methods #

    def _get_discard_time(self):
        now = time.time()
        discard_time_secs = 4.0  # TODO
        return self.discard_start_secs + discard_time_secs - now

    def _is_oorasu(self):
        return True  # TODO

    # Drawing methods #

    def _draw_hand(self, canvas, center_pos, tiles, tsumohai=None):
        discard_time = self._get_discard_time()
        discard_timer_text = None
        if discard_time is not None:
            time_string = "{0:.2f}".format(discard_time)
            discard_timer_text = self.discard_timer_font.render(time_string, 1, (255, 255, 255))
        centre_x, centre_y = center_pos
        tile_width = self._get_tile_image(0).get_width()
        tile_height = self._get_tile_image(0).get_height()
        total_width = tile_width * len(tiles)
        x = centre_x - (total_width / 2)
        y = canvas.get_height() - tile_height - 30
        for tile in tiles:
            self._draw_tile(canvas, tile, (x, y))
            x += tile_width
        if tsumohai is not None:
            x += 0.5 * tile_width
            self._draw_tile(canvas, tsumohai, (x, y))
            if discard_timer_text is not None:
                canvas.blit(discard_timer_text, (x - discard_timer_text.get_width() / 2 + tile_width / 2, y - 13))

    def _draw_tile(self, canvas, tile_id, pos, small=False, rotation=0, highlight_id=None, sideways=False):
        x, y = pos
        tile_image = self._get_tile_image(tile_id, small)
        if sideways:
            rotation += 90
        if rotation is not 0:
            tile_image = pygame.transform.rotate(tile_image, rotation)
        canvas.blit(tile_image, (x, y))
        rect = pygame.Rect(x, y, tile_image.get_width(), tile_image.get_height())
        self.tile_rects.append(rect)
        if highlight_id is not None:
            self._draw_highlight(canvas, rect, highlight_id)

    def _draw_calls(self, surface: pygame.Surface, calls: [Call], position: int) -> None:
        """
        Draw player meld calls to a Surface.
        :param surface: the surface to draw to
        :param calls: the list of calls
        :param position: the player position at which to draw the calls
        :return: None
        """
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        tile_diff = tile_height - tile_width
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2

        rotation = [0, -90, -180, -270][position]
        tile_rotation = rotation
        x = centre_x + tile_width * 10
        y = centre_y + tile_height * 7.5

        # Positioning hack
        if position in [Position.KAMICHA, Position.TOIMEN]:
            y += tile_height
        if position in [Position.SHIMOCHA, Position.TOIMEN]:
            x += tile_width
        if position in [Position.SHIMOCHA, Position.KAMICHA]:
            tile_rotation += 180

        for call in calls:
            # Determine how many tiles to display
            num_tiles = 3
            if CallType.is_kantsu(call.call_type):
                num_tiles = 4
            elif call.call_type == CallType.NUKE:
                num_tiles = 1

            # Draw tiles
            for n in range(num_tiles):
                is_call_tile = (call.call_type is not CallType.NUKE and n is call.call_tile)
                if is_call_tile:
                    # More positioning hacks
                    if position in [Position.SHIMOCHA, Position.TOIMEN]:
                        x += tile_diff
                    if position in [Position.TOIMEN, Position.KAMICHA]:
                        y -= tile_diff

                    # Adjust for rotation
                    x -= tile_diff
                    y += tile_diff
                    if call.call_type == CallType.SHOUMINKAN:
                        y -= tile_width
                        coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                        self._draw_tile(surface, call.tile_ids[n], coordinates, True, tile_rotation, sideways=True)
                        y += tile_width
                        if n is not num_tiles - 1:
                            n += 1
                coordinates = rotate((centre_x, centre_y), (x, y), rotation)
                self._draw_tile(surface, call.tile_ids[n], coordinates, True, tile_rotation, sideways=is_call_tile)
                if call.call_type == CallType.NUKE:
                    txt = "{}x".format(len(call.tile_ids))
                    nuke_text = self.discard_timer_font.render(txt, 1, (0, 0, 0))
                    tx = x + tile_width / 2 - nuke_text.get_width() / 2
                    ty = y - nuke_text.get_height()

                    # Even more positioning hacks holy shit I've got to fix these
                    if position in [Position.SHIMOCHA, Position.TOIMEN]:
                        tx -= tile_width / 2 + nuke_text.get_width() / 2
                    if position in [Position.TOIMEN, Position.KAMICHA]:
                        ty -= nuke_text.get_height() * 2

                    nuke_text = pygame.transform.rotate(nuke_text, tile_rotation)
                    coordinates = rotate((centre_x, centre_y), (tx, ty), rotation)
                    surface.blit(nuke_text, coordinates)
                x -= tile_width
                if is_call_tile:
                    y -= (tile_height - tile_width)
                    # Undo positioning hacks
                    if position in [Position.SHIMOCHA, Position.TOIMEN]:
                        x -= tile_diff
                    if position in [Position.TOIMEN, Position.KAMICHA]:
                        y += tile_diff

    def _draw_discards(self, surface: pygame.Surface, tiles, position: int):
        a_tile = self._get_tile_image(0, True)
        tile_width = a_tile.get_width()
        tile_height = a_tile.get_height()
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2

        discard_offset = tile_height * 3.25
        rotation = [0, -90, -180, -270][position]
        tile_rotation = rotation
        if position in [Position.SHIMOCHA, Position.KAMICHA]:
            tile_rotation += 180

        x_count = 0
        y_count = 0
        riichi_count = 0

        for tile in tiles:
            tile_id, tile_sprite_id, riichi, tsumogiri = tile
            x = centre_x + (x_count - 3) * tile_width
            y = centre_y + discard_offset + y_count * tile_height

            # Account for riichi tiles
            x += (tile_height - tile_width) * riichi_count
            if riichi:
                riichi_count += 1  # Must appear AFTER the positioning adjustment above

            # Positioning hacks
            if position in [Position.SHIMOCHA, Position.TOIMEN]:
                x += tile_width
                if riichi:
                    x += (tile_height - tile_width)
            if position in [Position.TOIMEN, Position.KAMICHA]:
                y += tile_height
                if riichi:
                    y -= (tile_height - tile_width)

            # Rotate into place
            pos = rotate((centre_x, centre_y), (x, y), rotation)

            # Highlight tsumogiri
            hl = 3 if tsumogiri else None

            self._draw_tile(surface, tile_sprite_id, pos, True, tile_rotation, highlight_id=hl, sideways=riichi)
            x_count += 1
            if x_count == 6 and y_count < 2:
                x_count = 0
                y_count += 1
                riichi_count = 0

    def _draw_corner_text(self, surface, lines):
        """
        Render lines of text in the top right of the screen.
        :param surface: the surface to render to
        :param lines: the lines of text as a string list
        :return: None
        """
        canvas_width = surface.get_width()
        y_offset = 20
        x_offset = y = 2 * y_offset
        for line in lines:
            text = self.corner_font.render(line, 1, (0, 0, 0))
            x = canvas_width - text.get_width() - x_offset
            surface.blit(text, (x, y))
            y += y_offset

    def _draw_centre_console(self, surface, players):
        """
        Render the centre console, including player names, seat winds, round information, scores, and riichi sticks.
        :param surface: the surface to render to
        :param players: the list of players
        :return: None
        """
        centre_x = surface.get_width() / 2
        centre_y = surface.get_height() / 2
        tile_img = self._get_tile_image(0, True)
        # tile_width = tile_img.get_width()
        tile_height = tile_img.get_height()
        wind_offset = tile_height * 1.20
        score_offset = tile_height * 2.15
        name_offset = score_offset + 20
        riichi_offset = tile_height * 3.00

        # Calculate score deltas first
        score_deltas = calculate_score_deltas(players)

        for idx in range(4):
            player = players[idx]
            if player is None:
                continue  # For two and three player, some players will be `None`
            if self.centre_hover:
                score_text = self.score_font.render(str(score_deltas[idx]), 1, (0, 0, 0))
            else:
                score_text = self.score_font.render(str(player.score), 1, (0, 0, 0))
            name_text = self.name_font.render("{0}・{1}".format(player.name, player.rank), 1, (0, 0, 0))
            wind_sprite = self.wind_sprites[player.seat]
            riichi_sprite = self.riichi_stick_sprite
            if idx == Position.JIBUN:
                wind_x = centre_x - wind_sprite.get_width() / 2
                wind_y = centre_y + wind_offset - wind_sprite.get_height() / 2
                score_x = centre_x - score_text.get_width() / 2
                score_y = centre_y + score_offset - score_text.get_height() / 2
                name_x = centre_x - name_text.get_width() / 2
                name_y = centre_y + name_offset - name_text.get_height() / 2
                riichi_x = centre_x - riichi_sprite.get_width() / 2
                riichi_y = centre_y + riichi_offset - riichi_sprite.get_height() / 2
            elif idx == Position.SHIMOCHA:
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
            elif idx == Position.TOIMEN:
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
            elif idx == Position.KAMICHA:
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
            centre_text_line0 = self.centre_font.render("東四局", 1, (0, 0, 0))
            centre_text_line1 = self.centre_font.render("二本場", 1, (0, 0, 0))
            surface.blit(centre_text_line0,
                         (centre_x - centre_text_line0.get_width() / 2, centre_y - centre_text_line0.get_height()))
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
