#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_gua.py —— 独立排盘校对器（指令 85）。

**刻意不复用** 项目 gua.py／render.py 的任何逻辑，另起一套推演：
  · 卦体：京房八宫「爻变生成法」（本宫→一世…五世→游魂→归魂）
  · 卦名：上卦×下卦六十四名表（独立抄录）
  · 纳甲：八卦纳甲口诀（乾甲壬、坤乙癸、震庚、巽辛、坎戊、离己、艮丙、兑丁）
  · 六亲：以卦宫五行为我，按生克定父母／兄弟／子孙／妻财／官鬼
  · 六神：按日干起青龙等六神，自初爻上行
  · 世应：八宫卦序世位（本宫六、一世一…五世五、游魂四、归魂三），应＝世+3（mod 6）
  · 伏神：本卦缺某六亲时，取**本宫首卦（八纯）**同位之纳甲补出
再与 paipan.paipan() 的产出逐项比对（卦名、宫、世应、纳甲、六亲、六神、伏神、动爻、变卦）。
历法另由 audit_cal() 用儒略日公式＋五虎遁＋五鼠遁＋旬空规则独立核算。

用法：
  python3 audit_gua.py            # 全量：64 静卦 + 随机/定向 86 例 + 历法 475 例
  python3 audit_gua.py --quick    # 只跑 64 静卦
"""
import datetime
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paipan     # 仅作被测对象取数据
import shensha    # 仅作被测对象取数据
import tables_js  # 节气数据（表值本身由 check_tables.py 校）

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WX_GAN = dict(zip(GAN, "木木火火土土金金水水"))
WX_ZHI = dict(zip(ZHI, "水土木木土火火土金金土水"))
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 八卦三爻（自下而上，1=阳）
TRIG = {"乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
        "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0)}
TRI_OF_BITS = {v: k for k, v in TRIG.items()}
WX_TRI = {"乾": "金", "兑": "金", "离": "火", "震": "木",
          "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

# 六十四卦名（上卦, 下卦）
NAME64 = {
    ("乾", "乾"): "乾为天", ("乾", "兑"): "天泽履", ("乾", "离"): "天火同人", ("乾", "震"): "天雷无妄",
    ("乾", "巽"): "天风姤", ("乾", "坎"): "天水讼", ("乾", "艮"): "天山遁", ("乾", "坤"): "天地否",
    ("兑", "乾"): "泽天夬", ("兑", "兑"): "兑为泽", ("兑", "离"): "泽火革", ("兑", "震"): "泽雷随",
    ("兑", "巽"): "泽风大过", ("兑", "坎"): "泽水困", ("兑", "艮"): "泽山咸", ("兑", "坤"): "泽地萃",
    ("离", "乾"): "火天大有", ("离", "兑"): "火泽睽", ("离", "离"): "离为火", ("离", "震"): "火雷噬嗑",
    ("离", "巽"): "火风鼎", ("离", "坎"): "火水未济", ("离", "艮"): "火山旅", ("离", "坤"): "火地晋",
    ("震", "乾"): "雷天大壮", ("震", "兑"): "雷泽归妹", ("震", "离"): "雷火丰", ("震", "震"): "震为雷",
    ("震", "巽"): "雷风恒", ("震", "坎"): "雷水解", ("震", "艮"): "雷山小过", ("震", "坤"): "雷地豫",
    ("巽", "乾"): "风天小畜", ("巽", "兑"): "风泽中孚", ("巽", "离"): "风火家人", ("巽", "震"): "风雷益",
    ("巽", "巽"): "巽为风", ("巽", "坎"): "风水涣", ("巽", "艮"): "风山渐", ("巽", "坤"): "风地观",
    ("坎", "乾"): "水天需", ("坎", "兑"): "水泽节", ("坎", "离"): "水火既济", ("坎", "震"): "水雷屯",
    ("坎", "巽"): "水风井", ("坎", "坎"): "坎为水", ("坎", "艮"): "水山蹇", ("坎", "坤"): "水地比",
    ("艮", "乾"): "山天大畜", ("艮", "兑"): "山泽损", ("艮", "离"): "山火贲", ("艮", "震"): "山雷颐",
    ("艮", "巽"): "山风蛊", ("艮", "坎"): "山水蒙", ("艮", "艮"): "艮为山", ("艮", "坤"): "山地剥",
    ("坤", "乾"): "地天泰", ("坤", "兑"): "地泽临", ("坤", "离"): "地火明夷", ("坤", "震"): "地雷复",
    ("坤", "巽"): "地风升", ("坤", "坎"): "地水师", ("坤", "艮"): "地山谦", ("坤", "坤"): "坤为地",
}

# 纳甲：(内卦三爻, 外卦三爻)，每爻 (干, 支)
NAJIA = {
    "乾": (("甲", "子"), ("甲", "寅"), ("甲", "辰"), ("壬", "午"), ("壬", "申"), ("壬", "戌")),
    "坎": (("戊", "寅"), ("戊", "辰"), ("戊", "午"), ("戊", "申"), ("戊", "戌"), ("戊", "子")),
    "艮": (("丙", "辰"), ("丙", "午"), ("丙", "申"), ("丙", "戌"), ("丙", "子"), ("丙", "寅")),
    "震": (("庚", "子"), ("庚", "寅"), ("庚", "辰"), ("庚", "午"), ("庚", "申"), ("庚", "戌")),
    "巽": (("辛", "丑"), ("辛", "亥"), ("辛", "酉"), ("辛", "未"), ("辛", "巳"), ("辛", "卯")),
    "离": (("己", "卯"), ("己", "丑"), ("己", "亥"), ("己", "酉"), ("己", "未"), ("己", "巳")),
    "坤": (("乙", "未"), ("乙", "巳"), ("乙", "卯"), ("癸", "丑"), ("癸", "亥"), ("癸", "酉")),
    "兑": (("丁", "巳"), ("丁", "卯"), ("丁", "丑"), ("丁", "亥"), ("丁", "酉"), ("丁", "未")),
}

SHI_ORDER = [6, 1, 2, 3, 4, 5, 4, 3]   # 本宫／一世…五世／游魂／归魂
LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
LS_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}


def gua_of(bits):
    """bits: 六爻自下而上 → (上卦, 下卦)"""
    return TRI_OF_BITS[tuple(bits[3:6])], TRI_OF_BITS[tuple(bits[0:3])]


def build_bagong():
    """京房八宫：本宫→一世…五世→游魂→归魂，爻变生成。返回 bits→(宫, 世位)"""
    out = {}
    for head_tri in ("乾", "坎", "艮", "震", "巽", "离", "坤", "兑"):
        base = list(TRIG[head_tri] * 2)      # 八纯卦：上下同
        seq = [base]
        for k in range(1, 6):                # 一世…五世
            b = list(base)
            for i in range(k):
                b[i] ^= 1
            seq.append(b)
        you = list(base)                     # 游魂：一至三爻变、四爻不变、五爻变
        for i in (0, 1, 2, 4):
            you[i] ^= 1
        seq.append(you)
        gui = list(base)                     # 归魂：仅五爻变
        gui[4] ^= 1
        seq.append(gui)
        for idx, b in enumerate(seq):
            key = tuple(b)
            assert key not in out, "八宫重复：%s" % (gua_of(b),)
            out[key] = (head_tri, SHI_ORDER[idx])
    assert len(out) == 64, "八宫应得 64 卦，实得 %d" % len(out)
    return out


BAGONG = build_bagong()


def liuqin(gong_wx, zhi):
    w = WX_ZHI[zhi]
    if w == gong_wx:
        return "兄弟"
    if SHENG[gong_wx] == w:
        return "子孙"
    if SHENG[w] == gong_wx:
        return "父母"
    if KE[gong_wx] == w:
        return "妻财"
    return "官鬼"


def expect_gua(bits):
    """独立算出某卦（静卦）应得的全部字段"""
    up, lo = gua_of(bits)
    name = NAME64[(up, lo)]
    gong, shi = BAGONG[tuple(bits)]
    gong_wx = WX_TRI[gong]
    ying = (shi + 2) % 6 + 1
    lines = []
    for i in range(6):
        tri = lo if i < 3 else up
        gan, zhi = NAJIA[tri][i]
        lines.append({"pos": i + 1, "yin": bits[i] == 0, "gan": gan, "zhi": zhi,
                      "wx": WX_ZHI[zhi], "gan_wx": WX_GAN[gan],
                      "liuqin": liuqin(gong_wx, zhi),
                      "shi": shi == i + 1, "ying": ying == i + 1})
    return {"name": name, "upper": up, "lower": lo, "gong": gong, "gong_wx": gong_wx,
            "shi": shi, "ying": ying, "lines": lines}


def expect_fushen(bits):
    """缺六亲则从**本宫首卦（八纯卦）**同位取伏神：返回 {pos: (六亲, 干, 支, 五行)}"""
    up, lo = gua_of(bits)
    gong, _ = BAGONG[tuple(bits)]
    gong_wx = WX_TRI[gong]
    have = {liuqin(gong_wx, NAJIA[lo if i < 3 else up][i][1]) for i in range(6)}
    need = [q for q in ("父母", "兄弟", "子孙", "妻财", "官鬼") if q not in have]
    if not need:
        return {}
    out = {}
    for i in range(6):
        gan, zhi = NAJIA[gong][i]          # 首卦上下同卦，六爻纳甲皆取本宫
        q = liuqin(gong_wx, zhi)
        if q in need:
            out[i + 1] = (q, gan, zhi, WX_ZHI[zhi])
    return out


def check_case(dt, yao, label=""):
    d = paipan.paipan(dt, list(yao), gender="男", question="", name="")
    fails = []

    bits = [0 if v in (6, 8) else 1 for v in yao]
    exp = expect_gua(bits)
    pr = d["primary"]
    for k in ("name", "upper", "lower", "gong", "gong_wx", "shi", "ying"):
        if pr[k] != exp[k]:
            fails.append("%s 本卦.%s 项目=%r 独立=%r" % (label, k, pr[k], exp[k]))
    for i in range(6):
        a, b = pr["lines"][i], exp["lines"][i]
        for k in ("yin", "gan", "zhi", "wx", "liuqin"):
            if a[k] != b[k]:
                fails.append("%s 本卦第%d爻.%s 项目=%r 独立=%r" % (label, i + 1, k, a[k], b[k]))
        if a["shi"] != b["shi"] or a["ying"] != b["ying"]:
            fails.append("%s 本卦第%d爻 世应 项目=%s/%s 独立=%s/%s"
                         % (label, i + 1, a["shi"], a["ying"], b["shi"], b["ying"]))

    # 六神（依赖日干）
    day_gan = d["pillars"]["day"][0]
    start = LS_START[day_gan]
    for i in range(6):
        want = LIUSHEN[(start + i) % 6]
        if pr["lines"][i]["liushen"] != want:
            fails.append("%s 本卦第%d爻 六神 项目=%s 独立=%s(日干%s)"
                         % (label, i + 1, pr["lines"][i]["liushen"], want, day_gan))

    # 伏神
    expfs = expect_fushen(bits)
    gotfs = {}
    for ln in pr["lines"]:
        f = ln.get("fushen")
        if f:
            gotfs[ln["pos"]] = (f["liuqin"], f["gan"], f["zhi"], f["wx"])
    if gotfs != expfs:
        fails.append("%s 伏神 项目=%r 独立=%r" % (label, gotfs, expfs))

    # 变卦
    moving = [i for i, v in enumerate(yao) if v in (6, 9)]
    if moving:
        cbits = list(bits)
        for i in moving:
            cbits[i] ^= 1
        cexp = expect_gua(cbits)
        ch = d["changed"]
        for k in ("name", "upper", "lower", "gong", "shi", "ying"):
            if ch[k] != cexp[k]:
                fails.append("%s 变卦.%s 项目=%r 独立=%r" % (label, k, ch[k], cexp[k]))
        # 变卦六亲以本卦宫为准
        for i in range(6):
            a, b = ch["lines"][i], cexp["lines"][i]
            want_q = liuqin(exp["gong_wx"], b["zhi"])
            if a["liuqin"] != want_q:
                fails.append("%s 变卦第%d爻 六亲 项目=%s 独立=%s"
                             % (label, i + 1, a["liuqin"], want_q))
            if a["gan"] != b["gan"] or a["zhi"] != b["zhi"]:
                fails.append("%s 变卦第%d爻 纳甲 项目=%s%s 独立=%s%s"
                             % (label, i + 1, a["gan"], a["zhi"], b["gan"], b["zhi"]))
        if ch.get("gong_wx") != exp["gong_wx"]:
            pass   # 变卦 gong_wx 是其自身宫，不校验

    return fails




# ---------------------------------------------------------------- 历法独立核算
CAL_GAN = GAN
CAL_ZHI = ZHI


def _jdn(y, m, d):
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045


def audit_cal(n_random=300, seed=11):
    """日柱用儒略日公式（锚点 1900-01-01＝甲戌）；年柱以立春为界、月柱以节为界
    （节气时刻取随包历法表，干支组合由五虎遁／五鼠遁独立推）；旬空按旬首推。

    注：节气「数据」与被测模块同源（同为天文库生成的表），故此项只校**逻辑**——
    换年换月公式、时柱起例、旬空。表值本身对不对，由 `check_tables.py` 重算比对把关。
    """
    def jie_dt(y, i):
        """第 y 年第 i 个节（0 小寒…11 大雪）的时刻。"""
        p = ((y - 1900) * 12 + i) * 4
        n = 0
        for c in tables_js.JIE_JS[p:p + 4]:
            n = n * 36 + "0123456789abcdefghijklmnopqrstuvwxyz".index(c)
        return datetime.datetime(y, 1, 1) + datetime.timedelta(minutes=n)

    def day_idx(dt):
        d = dt.date()
        if dt.hour >= 23:                       # 晚子时进位次日（late_zi）
            d += datetime.timedelta(days=1)
        return (_jdn(d.year, d.month, d.day) + 49) % 60

    def hour_gz(di, hour):
        zi = ((hour + 1) // 2) % 12
        start = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}[di % 10]
        return GAN[(start + zi) % 10] + ZHI[zi]

    def kong(di):
        x = di - (di % 10)
        return [ZHI[(x % 12 + 10) % 12], ZHI[(x % 12 + 11) % 12]]

    # 十二节 → 月建支（小寒起丑，逐月进一位）
    JIE = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]

    def year_idx(dt):
        lc = jie_dt(dt.year, 1)                 # 立春
        return ((dt.year if dt >= lc else dt.year - 1) - 4) % 60

    def month_gz(dt):
        yi = year_idx(dt)
        cands = []
        for yy in (dt.year - 1, dt.year, dt.year + 1):
            for i in range(12):
                cands.append((jie_dt(yy, i), JIE[i]))
        cands.sort()
        mb = None
        for t, m0 in cands:
            if t <= dt:
                mb = m0
            else:
                break
        k = "寅卯辰巳午未申酉戌亥子丑".index(mb)
        sg = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}[yi % 10]
        return GAN[(sg + k) % 10] + mb

    cases = []
    rnd = random.Random(seed)
    for _ in range(n_random):
        cases.append(datetime.datetime(rnd.randint(1901, 2099), rnd.randint(1, 12),
                                       rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59)))
    for y in (1901, 1950, 1999, 2026, 2099):
        for d in range(1, 8):
            cases.append(datetime.datetime(y, 2, d, 12, 0))
    for hh in range(24):
        cases.append(datetime.datetime(2026, 11, 2, hh, 30))
    bad = 0
    for dt in cases:
        p = paipan.paipan(dt, [7] * 6)["pillars"]
        di = day_idx(dt)
        want = {"year": GAN[year_idx(dt) % 10] + ZHI[year_idx(dt) % 12],
                "month": month_gz(dt), "day": GAN[di % 10] + ZHI[di % 12],
                "hour": hour_gz(di, dt.hour)}
        if any(p[k] != v for k, v in want.items()) or p["kong"] != kong(di):
            bad += 1
    return len(cases), bad


# ---------------------------------------------------------------- 神煞独立核算
# 十四神煞此前无任何独立校验（只查了「十四项齐不齐」）。此处按三合局十二长生
# 与十干口诀另抄一遍推演，与 shensha.compute() 逐项比对，专抓表里的错字错位。
JU_WX = {"申": "水", "子": "水", "辰": "水", "寅": "火", "午": "火", "戌": "火",
         "亥": "木", "卯": "木", "未": "木", "巳": "金", "酉": "金", "丑": "金"}
CS = {"水": "申", "火": "寅", "木": "亥", "金": "巳"}          # 各局长生之位
LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
      "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}      # 甲禄到寅宫
WC = {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
      "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}      # 甲乙巳午报君知
GUI = {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
       "丙": "亥酉", "丁": "亥酉", "辛": "午寅", "壬": "卯巳", "癸": "卯巳"}  # 甲戊庚牛羊
RIDE = {"甲": "寅", "己": "寅", "乙": "申", "庚": "申", "丙": "巳", "辛": "巳",
        "丁": "亥", "壬": "亥", "戊": "巳", "癸": "巳"}               # 日德
YANG_MONTH = "寅卯辰巳午未申酉戌亥子丑"


def _plus(z, k):
    return ZHI[(ZHI.index(z) + k) % 12]


def expect_shensha(dg, dz, mz):
    """三合局：长生→驿马冲长生、桃花居沐浴、将星居中神、华盖居墓、劫煞居绝、
    灾煞冲将星、谋星冲华盖；天马自正月午起逐月进二支；天医月建退一位。"""
    cs = CS[JU_WX[dz]]
    ren = _plus(LU[dg], 1 if GAN.index(dg) % 2 == 0 else -1)      # 阳干进、阴干退
    return {
        "驿马": [_plus(cs, 6)], "桃花": [_plus(cs, 1)], "日禄": [LU[dg]],
        "贵人": list(GUI[dg]), "文昌": [WC[dg]], "羊刃": [ren],
        "将星": [_plus(cs, 4)], "谋星": [_plus(cs, 14)],
        "劫煞": [_plus(cs, 9)], "灾煞": [_plus(cs, 10)], "华盖": [_plus(cs, 8)],
        "日德": [RIDE[dg]],
        "天马": [_plus("午", 2 * YANG_MONTH.index(mz))],
        "天医": [_plus(mz, -1)],
    }


def audit_shensha():
    n = bad = 0
    for dg in GAN:
        for dz in ZHI:
            for mz in ZHI:
                n += 1
                got = dict(shensha.compute(dg, dz, mz))
                want = expect_shensha(dg, dz, mz)
                if sorted(got) != sorted(want) or [x[0] for x in shensha.compute(dg, dz, mz)] != shensha.ORDER:
                    bad += 1
                    continue
                for k, v in want.items():
                    if got[k] != v:
                        bad += 1
                        if bad <= 5:
                            print("  神煞差 %s日 %s支 %s月 %s：得 %s 应 %s"
                                  % (dg, dz, mz, k, got[k], v))
                        break
    return n, bad


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    quick = "--quick" in argv
    fails = 0
    n = 0
    dt0 = datetime.datetime(2026, 11, 2, 15, 30)
    # 一、六十四卦全量（静卦）
    for bits in BAGONG:
        n += 1
        fails += len(check_case(dt0, [7 if b else 8 for b in bits], "静卦"))
    # 二、随机＋定向（含动爻）
    if not quick:
        rnd = random.Random(20261102)
        cases = []
        for _ in range(80):
            cases.append((datetime.datetime(rnd.randint(1902, 2099), rnd.randint(1, 12),
                                            rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59)),
                          [rnd.choice((6, 7, 8, 9)) for _ in range(6)]))
        for yao in ([9] * 6, [6] * 6, [6, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 9],
                    [8, 9, 8, 9, 8, 9], [7, 6, 9, 6, 7, 9]):
            cases.append((datetime.datetime(2026, 11, 2, 21, 30), yao))
        for dt, yao in cases:
            n += 1
            fails += len(check_case(dt, yao, str(yao)))
    # 三、历法
    cal_n, cal_bad = (0, 0) if quick else audit_cal()
    # 四、神煞（十干 × 十二支 × 十二月）
    ss_n, ss_bad = (0, 0) if quick else audit_shensha()
    if quick:
        print("独立校对：卦例 %d 例，失败 %d 项" % (n, fails))
    else:
        print("独立校对：卦例 %d 例，失败 %d 项；历法 %d 例，失败 %d 项；神煞 %d 例，失败 %d 项"
              % (n, fails, cal_n, cal_bad, ss_n, ss_bad))
    return 1 if (fails or cal_bad or ss_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
