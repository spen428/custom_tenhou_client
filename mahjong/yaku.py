class Yaku(object):
    han = {'open': None, 'closed': None}
    is_yakuman = False

    def __init__(self, open_value, closed_value, is_yakuman=False):
        self.han = {'open': open_value, 'closed': closed_value}
        self.is_yakuman = is_yakuman

    # for calls in array
    def __repr__(self):
        return self.__str__()


# Yaku situations
tsumo = Yaku(None, 1)
riichi = Yaku(None, 1)
ippatsu = Yaku(None, 1)
daburu_riichi = Yaku(None, 2)
haitei = Yaku(1, 1)
houtei = Yaku(1, 1)
rinshan = Yaku(1, 1)
chankan = Yaku(1, 1)
nagashi_mangan = Yaku(5, 5)
renhou = Yaku(None, 5)

# Yaku 1 Hands
pinfu = Yaku(None, 1)
tanyao = Yaku(1, 1)
iipeiko = Yaku(None, 1)
jikaze_ton = Yaku(1, 1)
jikaze_nan = Yaku(1, 1)
jikaze_shaa = Yaku(1, 1)
jikaze_pei = Yaku(1, 1)
bakaze_ton = Yaku(1, 1)
bakaze_nan = Yaku(1, 1)
bakaze_shaa = Yaku(1, 1)
bakaze_pei = Yaku(1, 1)
yakuhai_haku = Yaku(1, 1)
yakuhai_hatsu = Yaku(1, 1)
yakuhai_chun = Yaku(1, 1)

# Yaku 2 Hands
sanshoku_doujun = Yaku(1, 2)
ittsu = Yaku(1, 2)
chanta = Yaku(1, 2)
honroto = Yaku(2, 2)
toitoi = Yaku(2, 2)
sanankou = Yaku(2, 2)
sankantsu = Yaku(2, 2)
sanshoku_doukoo = Yaku(2, 2)
chiitoitsu = Yaku(None, 2)
shosangen = Yaku(2, 2)

# Yaku 3 Hands
honitsu = Yaku(2, 3)
junchan = Yaku(2, 3)
ryanpeiko = Yaku(None, 3)

# Yaku 6 Hands
chinitsu = Yaku(5, 6)

# Yakuman list
kokushi = Yaku(None, 13, True)
chuuren_poutou = Yaku(None, 13, True)
suuankou = Yaku(None, 13, True)
daisangen = Yaku(13, 13, True)
shosuushi = Yaku(13, 13, True)
ryuisou = Yaku(13, 13, True)
suukantsu = Yaku(13, 13, True)
tsuisou = Yaku(13, 13, True)
chinroto = Yaku(13, 13, True)

# Double yakuman
daisuushi = Yaku(26, 26, True)
daburu_kokushi = Yaku(None, 26, True)
suuankou_tanki = Yaku(None, 26, True)
junsei_chuuren_poutou = Yaku(None, 26, True)

# Yakuman situations
tenhou = Yaku(None, 13, True)
chiihou = Yaku(None, 13, True)

# Other
dora = Yaku(1, 1)
ura_dora = Yaku(1, 1)
aka_dora = Yaku(1, 1)

LIMIT_STRINGS = ['', '満貫', '跳満', '倍満', '三倍満', '役満']

YAKU_STRINGS = [  # In the order they are indexed on Tenhou.net
    '門前清自摸和', '立直', '一発', '槍槓', '嶺上開花', '海底摸月', '河底撈魚', '平和', '断幺九', '一盃口', '自風 東', '自風 南', '自風 西', '自風 北', '場風 東',
    '場風 南', '場風 西', '場風 北', '役牌 白', '役牌 發', '役牌 中', '両立直', '七対子', '混全帯幺九', '一気通貫', '三色同順', '三色同刻', '三槓子', '対々和', '三暗刻',
    '小三元', '混老頭', '二盃口', '純全帯幺九', '混一色', '清一色', '人和', '天和', '地和', '大三元', '四暗刻', '四暗刻単騎', '字一色', '緑一色', '清老頭', '九蓮宝燈',
    '純正九蓮宝燈', '国士無双', '国士無双１３面', '大四喜', '小四喜', '四槓子', 'ドラ', '裏ドラ', '赤ドラ']

YAKU_LIST = [  # In the order they are indexed on Tenhou.net
    tsumo, riichi, ippatsu, chankan, rinshan, haitei, houtei, pinfu, tanyao, iipeiko, jikaze_ton, jikaze_nan,
    jikaze_shaa, jikaze_pei, bakaze_ton, bakaze_nan, bakaze_shaa, bakaze_pei, yakuhai_haku, yakuhai_hatsu, yakuhai_chun,
    daburu_riichi, chiitoitsu, chanta, ittsu, ittsu,  # Yes, ittsu appears twice
    sanshoku_doujun, sanshoku_doukoo, sankantsu, toitoi, sanankou, shosangen, honroto, ryanpeiko, junchan, honitsu,
    chinitsu, renhou, tenhou, chiihou, daisangen, suuankou, suuankou_tanki, tsuisou, ryuisou, chinroto, chuuren_poutou,
    junsei_chuuren_poutou, kokushi, daburu_kokushi, shosuushi, daisuushi, suukantsu, dora, ura_dora, aka_dora]
