#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gua.py —— 卦理层：八宫、纳甲、六亲、六神、世应、伏神、变卦。

口径
----
* 八宫：京房八宫卦序。世位随宫序而定：八纯六世，一至五世顺次，游魂四世，归魂三世；
  应爻为世爻之对（相隔三位）。
* 纳甲：京房纳甲（乾甲壬、坤乙癸、震庚、巽辛、坎戊、离己、艮丙、兑丁）。
* 六亲：以本卦卦宫五行为「我」。变卦六亲仍以本卦卦宫为准
  （依参考图：雷风恒见「父母庚戌土」，非以震木论）。
* 六神：日干起——甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武，自初爻向上顺布。
* 伏神：本卦缺某六亲时，取本宫首卦（八纯卦）同位之爻，伏于本卦同位爻下。
* 六合／六冲：取通行卦表（京房），不以纳甲爻支偶合推定，理由见表注。
"""

ZHI = "子丑寅卯辰巳午未申酉戌亥"

BAGUA_BITS = {       # (初, 二, 三) → 卦名
    (1, 1, 1): "乾", (1, 1, 0): "兑", (1, 0, 1): "离", (1, 0, 0): "震",
    (0, 1, 1): "巽", (0, 1, 0): "坎", (0, 0, 1): "艮", (0, 0, 0): "坤",
}
GUA_BITS = {v: k for k, v in BAGUA_BITS.items()}

BAGUA_SYMBOL = {"乾": "☰", "兑": "☱", "离": "☲", "震": "☳",
                "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷"}

_LOWER_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

_UPPER_TABLE = {     # 上卦 → 下卦（乾兑离震巽坎艮坤）相应卦名
    "乾": ["乾为天", "天泽履", "天火同人", "天雷无妄", "天风姤", "天水讼", "天山遁", "天地否"],
    "兑": ["泽天夬", "兑为泽", "泽火革", "泽雷随", "泽风大过", "泽水困", "泽山咸", "泽地萃"],
    "离": ["火天大有", "火泽睽", "离为火", "火雷噬嗑", "火风鼎", "火水未济", "火山旅", "火地晋"],
    "震": ["雷天大壮", "雷泽归妹", "雷火丰", "震为雷", "雷风恒", "雷水解", "雷山小过", "雷地豫"],
    "巽": ["风天小畜", "风泽中孚", "风火家人", "风雷益", "巽为风", "风水涣", "风山渐", "风地观"],
    "坎": ["水天需", "水泽节", "水火既济", "水雷屯", "水风井", "坎为水", "水山蹇", "水地比"],
    "艮": ["山天大畜", "山泽损", "山火贲", "山雷颐", "山风蛊", "山水蒙", "艮为山", "山地剥"],
    "坤": ["地天泰", "地泽临", "地火明夷", "地雷复", "地风升", "地水师", "地山谦", "坤为地"],
}
NAME_TO_GUA = {(u, l): _UPPER_TABLE[u][i] for u in _LOWER_ORDER
               for i, l in enumerate(_LOWER_ORDER)}
GUA_TO_NAME = {v: k for k, v in NAME_TO_GUA.items()}

GONG = {             # 京房八宫卦序（首卦为八纯）
    "乾": ["乾为天", "天风姤", "天山遁", "天地否", "风地观", "山地剥", "火地晋", "火天大有"],
    "坎": ["坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师"],
    "艮": ["艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐"],
    "震": ["震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随"],
    "巽": ["巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊"],
    "离": ["离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人"],
    "坤": ["坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比"],
    "兑": ["兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹"],
}
GONG_WX = {"乾": "金", "兑": "金", "离": "火", "震": "木",
           "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
_SHI_BY_INDEX = [6, 1, 2, 3, 4, 5, 4, 3]      # 八纯、一至五世、游魂四世、归魂三世

GONG_OF, SHI_OF = {}, {}
for _g, _names in GONG.items():
    for _i, _n in enumerate(_names):
        GONG_OF[_n] = _g
        SHI_OF[_n] = _SHI_BY_INDEX[_i]

NAJIA = {            # 京房纳甲：卦 → 六爻（初→上）干支
    "乾": [("甲", "子"), ("甲", "寅"), ("甲", "辰"), ("壬", "午"), ("壬", "申"), ("壬", "戌")],
    "坤": [("乙", "未"), ("乙", "巳"), ("乙", "卯"), ("癸", "丑"), ("癸", "亥"), ("癸", "酉")],
    "震": [("庚", "子"), ("庚", "寅"), ("庚", "辰"), ("庚", "午"), ("庚", "申"), ("庚", "戌")],
    "巽": [("辛", "丑"), ("辛", "亥"), ("辛", "酉"), ("辛", "未"), ("辛", "巳"), ("辛", "卯")],
    "坎": [("戊", "寅"), ("戊", "辰"), ("戊", "午"), ("戊", "申"), ("戊", "戌"), ("戊", "子")],
    "离": [("己", "卯"), ("己", "丑"), ("己", "亥"), ("己", "酉"), ("己", "未"), ("己", "巳")],
    "艮": [("丙", "辰"), ("丙", "午"), ("丙", "申"), ("丙", "戌"), ("丙", "子"), ("丙", "寅")],
    "兑": [("丁", "巳"), ("丁", "卯"), ("丁", "丑"), ("丁", "亥"), ("丁", "酉"), ("丁", "未")],
}

ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
          "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}

_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
LIUQIN_ORDER = ["父母", "兄弟", "子孙", "妻财", "官鬼"]


def liuqin(gong_wx, yao_wx):
    """以卦宫五行为我定六亲。"""
    if gong_wx == yao_wx:
        return "兄弟"
    if _SHENG[yao_wx] == gong_wx:
        return "父母"
    if _SHENG[gong_wx] == yao_wx:
        return "子孙"
    if _KE[yao_wx] == gong_wx:
        return "官鬼"
    return "妻财"


def liushen_start(day_gan):
    """日干 → 初爻六神序号。"""
    return {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3,
            "庚": 4, "辛": 4, "壬": 5, "癸": 5}[day_gan]


def _najia_of(bits):
    """六位阴阳（初→上）→ 六爻 (干, 支)，逐爻按所隶经卦取纳甲。"""
    lower = BAGUA_BITS[tuple(bits[0:3])]
    upper = BAGUA_BITS[tuple(bits[3:6])]
    out = []
    for i in range(6):
        gua = lower if i < 3 else upper
        out.append(NAJIA[gua][i])      # 纳甲表 index i 即六爻位次（内卦 0–2、外卦 3–5）
    return out, upper, lower


def build(bits, moving_flags=None, day_gan="甲", liuqin_gong=None):
    """由六爻阴阳成卦。bits 自初爻起、长 6（1 阳 0 阴）。

    liuqin_gong：指定六亲所依卦宫五行（变卦须传本卦宫），None 则用自身卦宫。
    """
    moving_flags = moving_flags or [False] * 6
    najia, upper, lower = _najia_of(bits)
    name = NAME_TO_GUA[(upper, lower)]
    gong = GONG_OF[name]
    gong_wx = liuqin_gong or GONG_WX[gong]
    shi = SHI_OF[name]
    ying = shi + 3 if shi <= 3 else shi - 3
    liushen0 = liushen_start(day_gan)

    rows = []
    for i in range(6):
        gan, zhi = najia[i]
        wx = ZHI_WX[zhi]
        rows.append({
            "pos": i + 1,
            "yin": bits[i] == 0,
            "moving": bool(moving_flags[i]),
            "liuqin": liuqin(gong_wx, wx),
            "gan": gan, "zhi": zhi, "wx": wx,
            "gan_wx": GAN_WX[gan],
            "liushen": LIUSHEN[(liushen0 + i) % 6],
            "shi": (i + 1) == shi,
            "ying": (i + 1) == ying,
            "kong": False,
        })

    idx = GONG[gong].index(name)
    tags = []
    if idx == 0:
        tags.append("八纯")
    elif idx == 6:
        tags.append("游魂")
    elif idx == 7:
        tags.append("归魂")
    if name in LIUHE_GUA:
        tags.append("六合")
    if name in LIUCHONG_GUA:
        tags.append("六冲")

    return {
        "name": name, "upper": upper, "lower": lower,
        "symbol": BAGUA_SYMBOL[upper] + BAGUA_SYMBOL[lower],
        "gong": gong, "gong_wx": GONG_WX[gong],
        "liuqin_gong_wx": gong_wx,
        "shi": shi, "ying": ying,
        "tags": tags,
        "lines": rows,
        "bits": list(bits),
    }


# 六合／六冲取通行卦表（京房），不以纳甲爻支偶合推定：
#   爻支全合者另有「火山旅、山火贲」，卦义不属六合；卦与卦六合之「山泽损、泽山咸」，
#   其爻支亦不全合。两法互有出入，六爻家所用者为此表。
LIUHE_GUA = {"天地否", "地天泰", "山泽损", "泽山咸",
             "水泽节", "泽水困", "地雷复", "雷地豫"}
LIUCHONG_GUA = {"乾为天", "坤为地", "震为雷", "巽为风", "坎为水", "离为火", "艮为山", "兑为泽",
                "天雷无妄", "雷天大壮"}


def add_fushen(primary):
    """本卦缺六亲 → 取本宫首卦同位之爻伏于下。原地写入并返回 {爻位: 信息}。"""
    present = {r["liuqin"] for r in primary["lines"]}
    missing = [q for q in LIUQIN_ORDER if q not in present]
    out = {}
    if not missing:
        return out
    first = GONG[primary["gong"]][0]
    bits = [1 if b else 0 for b in GUA_BITS[GUA_TO_NAME[first][0]]]
    up_bits = GUA_BITS[GUA_TO_NAME[first][0]]
    lo_bits = GUA_BITS[GUA_TO_NAME[first][1]]
    full = list(lo_bits) + list(up_bits)
    najia, _, _ = _najia_of(full)
    gong_wx = GONG_WX[primary["gong"]]
    for i in range(6):
        gan, zhi = najia[i]
        q = liuqin(gong_wx, ZHI_WX[zhi])
        if q in missing and q not in out.values():
            out[i + 1] = {"liuqin": q, "gan": gan, "zhi": zhi, "wx": ZHI_WX[zhi]}
    for pos, info in out.items():
        primary["lines"][pos - 1]["fushen"] = info
    return out


def bian(primary):
    """动爻取反成变卦；无动爻返回 None。六亲仍以本卦卦宫为准。"""
    if not any(l["moving"] for l in primary["lines"]):
        return None
    bits = []
    for l in primary["lines"]:
        b = 0 if l["yin"] else 1
        if l["moving"]:
            b = 1 - b
        bits.append(b)
    ch = build(bits, None, "甲", liuqin_gong=primary["gong_wx"])
    for r in ch["lines"]:
        r["liushen"] = ""
    return ch


def kong_flags(hexagram, kong):
    """标注各爻旬空。"""
    for r in hexagram["lines"]:
        r["kong"] = r["zhi"] in kong
    return hexagram
