#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfcheck.py —— 全量自检：金标对图、六十四卦不变量、历法连续性、神煞完备、渲染合规。

金标杆：用户提供的 2026-08-12 20:13 截图（女测·问工作 · 天地否之雷风恒）。
凡此文件中的断言，均为可复算的硬条件；不靠目测。
"""
import datetime
import itertools
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_js  # noqa: E402
import gua      # noqa: E402
import lifa     # noqa: E402
import paipan   # noqa: E402
import render   # noqa: E402
import shensha  # noqa: E402

N_OK = 0
FAILS = []


def chk(name, cond, detail=""):
    global N_OK
    if cond:
        N_OK += 1
    else:
        FAILS.append("%s%s" % (name, ("：" + detail) if detail else ""))


# ---------------------------------------------------------------- 金标杆
GOLD_PILLARS = ("丙午", "丙申", "戊午", "壬戌")
GOLD_KONG = ["子", "丑"]
GOLD_PRIMARY = ("乾", "天地否", 3, 6)
GOLD_CHANGED = ("震", "雷风恒", 3, 6)
GOLD_LINES = [   # 初 → 上：(六亲, 干, 支, 阴?, 动?)
    ("父母", "乙", "未", True, False),
    ("官鬼", "乙", "巳", True, True),
    ("妻财", "乙", "卯", True, True),
    ("官鬼", "壬", "午", False, False),
    ("兄弟", "壬", "申", False, True),
    ("父母", "壬", "戌", False, True),
]
GOLD_BIAN = [    # 初 → 上
    ("父母", "辛", "丑", True),
    ("子孙", "辛", "亥", False),
    ("兄弟", "辛", "酉", False),
    ("官鬼", "庚", "午", False),
    ("兄弟", "庚", "申", True),
    ("父母", "庚", "戌", True),
]
GOLD_SHEN = [("驿马", ["申"]), ("桃花", ["卯"]), ("日禄", ["巳"]), ("贵人", ["丑", "未"]),
             ("文昌", ["申"]), ("羊刃", ["午"]), ("将星", ["午"]), ("谋星", ["辰"]),
             ("劫煞", ["亥"]), ("灾煞", ["子"]), ("华盖", ["戌"]), ("日德", ["巳"]),
             ("天马", ["午"]), ("天医", ["未"])]
GOLD_LIUSHEN = ["勾陈", "螣蛇", "白虎", "玄武", "青龙", "朱雀"]


def _paipan(dt, yao, gender="女", live=False):
    import paipan
    return paipan.paipan(dt, yao, gender, "问工作" if gender else "", live=live)


def test_golden():
    d = _paipan(lifa.parse_dt("2026-08-12 20:13"), [8, 6, 6, 7, 9, 9])
    p = d["pillars"]
    chk("金标·四柱", (p["year"], p["month"], p["day"], p["hour"]) == GOLD_PILLARS,
        "%s%s%s%s" % (p["year"], p["month"], p["day"], p["hour"]))
    chk("金标·旬空", p["kong"] == GOLD_KONG, str(p["kong"]))
    pri, ch = d["primary"], d["changed"]
    chk("金标·本卦", (pri["gong"], pri["name"], pri["shi"], pri["ying"]) == GOLD_PRIMARY,
        "%s宫%s 世%d应%d" % (pri["gong"], pri["name"], pri["shi"], pri["ying"]))
    chk("金标·六合", "六合" in pri["tags"], str(pri["tags"]))
    chk("金标·变卦", (ch["gong"], ch["name"], ch["shi"], ch["ying"]) == GOLD_CHANGED,
        "%s宫%s 世%d应%d" % (ch["gong"], ch["name"], ch["shi"], ch["ying"]))
    for i, (q, g, z, yin, mov) in enumerate(GOLD_LINES):
        l = pri["lines"][i]
        ok = (l["liuqin"], l["gan"], l["zhi"], l["yin"], l["moving"]) == (q, g, z, yin, mov)
        chk("金标·本卦第%d爻" % (i + 1), ok,
            "%s%s%s 阴%s 动%s" % (l["liuqin"], l["gan"], l["zhi"], l["yin"], l["moving"]))
        chk("金标·六神第%d爻" % (i + 1), l["liushen"] == GOLD_LIUSHEN[i], l["liushen"])
    for i, (q, g, z, yin) in enumerate(GOLD_BIAN):
        l = ch["lines"][i]
        chk("金标·变卦第%d爻" % (i + 1), (l["liuqin"], l["gan"], l["zhi"], l["yin"]) == (q, g, z, yin),
            "%s%s%s 阴%s" % (l["liuqin"], l["gan"], l["zhi"], l["yin"]))
    f = pri["lines"][0].get("fushen")
    chk("金标·伏神", f and (f["liuqin"], f["gan"], f["zhi"]) == ("子孙", "甲", "子"),
        str(f))
    chk("金标·神煞十四项", [(n, list(v)) for n, v in d["shensha"]] == [(n, list(v)) for n, v in GOLD_SHEN],
        str(d["shensha"]))


# ---------------------------------------------------------------- 六十四卦
def test_64():
    names = list(gua.GONG_OF)
    chk("六十四卦·总数", len(gua.NAME_TO_GUA) == 64 and len(set(gua.NAME_TO_GUA.values())) == 64,
        "组合 %d，卦名 %d" % (len(gua.NAME_TO_GUA), len(set(gua.NAME_TO_GUA.values()))))
    chk("六十四卦·八宫覆盖", len(names) == 64 and len(set(names)) == 64, "归宫 %d" % len(names))

    count = {"八纯": 0, "六合": 0, "六冲": 0, "游魂": 0, "归魂": 0}
    for bits in itertools.product((0, 1), repeat=6):
        h = gua.build(list(bits), None, "甲")
        for t in h["tags"]:
            count[t] = count.get(t, 0) + 1

    chk("卦象·八纯八", count["八纯"] == 8, str(count["八纯"]))
    chk("卦象·六冲十", count["六冲"] == 10, str(count["六冲"]))
    chk("卦象·六合八", count["六合"] == 8, str(count["六合"]))
    chk("卦象·游魂八", count["游魂"] == 8, str(count["游魂"]))
    chk("卦象·归魂八", count["归魂"] == 8, str(count["归魂"]))

    # 纳甲：爻之天干须属该经卦所纳
    najia_gan = {"乾": {"甲", "壬"}, "坤": {"乙", "癸"}, "震": {"庚"}, "巽": {"辛"},
                 "坎": {"戊"}, "离": {"己"}, "艮": {"丙"}, "兑": {"丁"}}
    bad_na, bad_shi, bad_liuqin, bad_fu = [], [], [], []
    for bits in itertools.product((0, 1), repeat=6):
        h = gua.build(list(bits), None, "甲")
        lower, upper = h["lower"], h["upper"]
        for i, l in enumerate(h["lines"]):
            g = lower if i < 3 else upper
            if l["gan"] not in najia_gan[g]:
                bad_na.append((h["name"], i + 1))
        if not (1 <= h["shi"] <= 6) or abs(h["shi"] - h["ying"]) != 3:
            bad_shi.append(h["name"])
        gua.add_fushen(h)
        have = {l["liuqin"] for l in h["lines"]}
        have |= {v["liuqin"] for v in
                 [l.get("fushen") for l in h["lines"] if l.get("fushen")]}
        if set(have) != set(gua.LIUQIN_ORDER):
            bad_fu.append((h["name"], sorted(have)))
        gwx = h["gong_wx"]
        for l in h["lines"]:
            if l["liuqin"] != gua.liuqin(gwx, l["wx"]):
                bad_liuqin.append(h["name"])
    chk("纳甲·干支归属", not bad_na, str(bad_na[:3]))
    chk("世应·对宫相隔三位", not bad_shi, str(bad_shi[:3]))
    chk("六亲·伏神补足五类", not bad_fu, str(bad_fu[:3]))
    chk("六亲·以本宫五行为我", not bad_liuqin, str(bad_liuqin[:3]))

    # 动爻变卦：翻转正确，且六亲仍依本卦宫
    bad_flip, bad_gong = [], []
    for bits in itertools.product((0, 1), repeat=6):
        for mov in itertools.product((False, True), repeat=6):
            h = gua.build(list(bits), list(mov), "甲")
            c = gua.bian(h)
            if c is None:
                if any(mov):
                    bad_flip.append(h["name"])
                continue
            for i in range(6):
                want = (1 - bits[i]) if mov[i] else bits[i]
                if c["bits"][i] != want:
                    bad_flip.append((h["name"], i + 1))
            for l in c["lines"]:
                if l["liuqin"] != gua.liuqin(h["gong_wx"], l["wx"]):
                    bad_gong.append(h["name"])
    chk("变卦·动爻翻转", not bad_flip, str(bad_flip[:3]))
    chk("变卦·六亲依本卦宫", not bad_gong, str(bad_gong[:3]))


# ---------------------------------------------------------------- 历法
def test_lifa():
    d = datetime.date(2020, 1, 1)
    prev = None
    bad = 0
    for _ in range(730):
        p = lifa.four_pillars(datetime.datetime(d.year, d.month, d.day, 12, 0))
        if prev is not None and p["day_index"] != (prev + 1) % 60:
            bad += 1
        prev = p["day_index"]
        d += datetime.timedelta(days=1)
    chk("历法·日柱六十日连续", bad == 0, "断点 %d 处" % bad)

    # 五鼠遁：时干 = (日干序*2 + 时支序) % 10
    base = datetime.datetime(2026, 8, 12, 0, 0)
    bad_h = 0
    for hh in range(24):
        p = lifa.four_pillars(base.replace(hour=hh))
        want = (lifa.GAN.index(p["day"][0]) * 2 + lifa.ZHI.index(p["hour"][1])) % 10
        if lifa.GAN.index(p["hour"][0]) != want:
            bad_h += 1
    chk("历法·时柱五鼠遁", bad_h == 0, "错 %d 处" % bad_h)

    # 旬空：每旬二支，且不落旬内十支
    bad_k = 0
    for i in range(60):
        kong = lifa.xun_kong(i)
        head = i - i % 10
        xun_zhi = {lifa.ZHI[(head + k) % 12] for k in range(10)}
        if len(set(kong)) != 2 or set(kong) & xun_zhi:
            bad_k += 1
    chk("历法·旬空不落旬内", bad_k == 0, "错 %d 处" % bad_k)

    y1 = lifa.four_pillars(datetime.datetime(2026, 2, 3, 12, 0))["year"]
    y2 = lifa.four_pillars(datetime.datetime(2026, 2, 5, 12, 0))["year"]
    chk("历法·立春换年", (y1, y2) == ("乙巳", "丙午"), "%s→%s" % (y1, y2))

    # 交节时刻：当日时刻未到不得提前换年／换月（sxtwl 的 getYearGZ／getMonthGZ 按整日换，故自算）
    m1 = lifa.four_pillars(datetime.datetime(2025, 3, 5, 9, 27))["month"]
    m2 = lifa.four_pillars(datetime.datetime(2025, 3, 5, 16, 30))["month"]
    chk("历法·交节时刻换月", (m1, m2) == ("戊寅", "己卯"), "%s→%s（惊蛰 16:07）" % (m1, m2))
    y1 = lifa.four_pillars(datetime.datetime(2026, 2, 4, 4, 0))["year"]
    y2 = lifa.four_pillars(datetime.datetime(2026, 2, 4, 4, 30))["year"]
    chk("历法·交节时刻换年", (y1, y2) == ("乙巳", "丙午"), "%s→%s（立春 04:01）" % (y1, y2))
    b1 = lifa.four_pillars(datetime.datetime(2025, 3, 5, 9, 27))
    chk("历法·年月月互洽", b1["month"][1] == "寅" and b1["year"] == lifa.four_pillars(
        datetime.datetime(2025, 2, 10, 12, 0))["year"], str(b1["month"]))

    a = lifa.four_pillars(datetime.datetime(2026, 8, 12, 22, 59))
    b = lifa.four_pillars(datetime.datetime(2026, 8, 12, 23, 1))
    chk("历法·晚子时换日", lifa.jiazi_index(*b["day"]) == (lifa.jiazi_index(*a["day"]) + 1) % 60,
        "%s→%s" % (a["day"], b["day"]))

    # 越界年份须明确报错：不许抛裸 KeyError，也不许算出页面端根本复现不了的干支
    # （历法表只到 1900–2100，见 lifa.YEAR_MIN／YEAR_MAX）
    bad = 0
    for y in (1899, 2101):
        try:
            lifa.four_pillars(datetime.datetime(y, 6, 1, 12, 0))
        except SystemExit as e:
            bad += 0 if "可排年份" in str(e) else 1
        except Exception:
            bad += 1
        else:
            bad += 1
    chk("历法·越界年份明确报错", bad == 0, "异常 %d 处" % bad)

    # 农历不存在的日期须报错，不得静默跨月／跨年（sxtwl 自己会滚到下月）
    bad = 0
    for (y, m, d, lp) in ((2025, 6, 30, True), (2025, 8, 1, True), (2026, 2, 30, False)):
        try:
            lifa.lunar_to_solar(y, m, d, lp)
        except SystemExit:
            pass
        else:
            bad += 1
    chk("历法·农历不存在日期明确报错", bad == 0, "静默改写 %d 处" % bad)
    chk("历法·农历大月三十仍可排", lifa.lunar_to_solar(2025, 6, 30, False) == (2025, 7, 24),
        str(lifa.lunar_to_solar(2025, 6, 30, False)))

    # 运行期不得依赖 sxtwl（C++ 扩展，Windows 上要编 UCRT 头文件，别人装不动）。
    # 历法一律取自随包表 tables_js；表本身由开发期 check_tables.py 重算比对（指令 91）。
    src = ""
    for fn in ("lifa.py", "audit_gua.py"):
        with open(os.path.join(HERE, fn), encoding="utf-8") as f:
            src += f.read()
    chk("历法·运行期不依赖 sxtwl", "import sxtwl" not in src,
        "仍有 sxtwl 导入：装不上该扩展的机器将无法排盘")


# ---------------------------------------------------------------- 神煞
def test_shensha():
    bad = 0
    for gi in range(10):
        for zi in range(12):
            for mi in range(12):
                pairs = shensha.compute(lifa.GAN[gi], lifa.ZHI[zi], lifa.ZHI[mi])
                if len(pairs) != 14 or [n for n, _ in pairs] != shensha.ORDER:
                    bad += 1
                    continue
                for _, vals in pairs:
                    if not vals or any(v not in lifa.ZHI for v in vals):
                        bad += 1
    chk("神煞·十四项完备", bad == 0, "异常 %d 组" % bad)

    bad_ty = 0
    for mi in range(12):
        res = dict(shensha.compute("甲", "子", lifa.ZHI[mi]))
        if res["天医"][0] != lifa.ZHI[(mi - 1) % 12]:
            bad_ty += 1
    chk("神煞·天医月建退一位", bad_ty == 0, "错 %d 处" % bad_ty)

    # 三合局按十二长生推：驿马冲长生、桃花居沐浴、将星居中神、华盖居墓、
    # 劫煞居绝、灾煞冲将星、谋星冲华盖。由局自身推，不查 _SANHE 表。
    JU = {"申": "水", "子": "水", "辰": "水", "寅": "火", "午": "火", "戌": "火",
          "亥": "木", "卯": "木", "未": "木", "巳": "金", "酉": "金", "丑": "金"}
    CS = {"水": "申", "火": "寅", "木": "亥", "金": "巳"}
    bad = 0
    for dz, wx in JU.items():
        cs = lifa.ZHI.index(CS[wx])
        res = dict(shensha.compute("甲", dz, "寅"))
        for k, step in (("驿马", 6), ("桃花", 1), ("将星", 4), ("华盖", 8),
                        ("劫煞", 9), ("灾煞", 10), ("谋星", 14)):
            if res[k][0] != lifa.ZHI[(cs + step) % 12]:
                bad += 1
    chk("神煞·三合局七神煞合长生之序", bad == 0, "错 %d 处" % bad)

    bad = 0
    for i, g in enumerate(lifa.GAN):
        lu = lifa.ZHI.index(shensha._LU[g])
        ren = lifa.ZHI.index(shensha._REN[g])
        if ren != (lu + (1 if i % 2 == 0 else -1)) % 12:
            bad += 1
    chk("神煞·羊刃随禄进退休一位", bad == 0, "错 %d 处" % bad)


# ---------------------------------------------------------------- 渲染
def test_render():
    d = _paipan(lifa.parse_dt("2026-08-12 20:13"), [8, 6, 6, 7, 9, 9])
    h = render.render_html(d)
    m = render.render_md(d)
    chk("渲染·无外链资源", "src=\"http" not in h and "<link" not in h and "@import" not in h
        and "url(http" not in h, "含外链资源")
    chk("品牌·logo 内联", 'class="logo"' in h and "data:image/png;base64," in h
        and h.count("<img") == 2, "logo 未内联，或页头页脚未各一枚")
    chk("页头·题名与 logo", '<header class="top">' in h and "<h1>六爻排盘</h1>" in h
        and 'class="tlogo"' in h and h.index('class="top"') < h.index('id="panel"'),
        "页头缺 logo／题名，或不在面板之前")
    chk("页头·整块居中", 'class="ttext"' in h and 'class="tsep"' in h
        and h.index('class="tlogo"') < h.index('class="tsep"') < h.index('class="ttext"')
        and "align-items:center" in h, "页头未按「logo ｜ 题名＋副标题」整块居中")
    chk("页头·标签恒定", "<title>魁君堂·六爻排盘</title>" in h
        and "六爻排盘 · " not in h.split("<body>")[0], "页面标签未固定为「魁君堂·六爻排盘」")
    # 字号随宽度收窄的双保险（指令 61）：vw 回退版必须存在且在 @supports cqw 覆盖版之前
    vw = "calc((100vw - 26px)/36.667)"
    chk("字体·vw 回退在前", vw in h and "@supports (width:1cqw)" in h
        and "calc((100vw - 26px)/21.2)" in h
        and h.index(vw) < h.index("@supports (width:1cqw)"),
        "字号缺 vw 回退或回退未置于 cqw 版之前——不认 cqw 的内核会退回错误比例字号")
    # 格内一律单行（指令 59「卦象分两行以后不要出现」的绝对兜底）
    chk("盘面·格内禁折行", ".board th,.board td{white-space:nowrap}" in h,
        "盘面格未设 nowrap——字号失配时将再次折成两行")
    # 方式组右对齐（指令 59）
    chk("方式·紧凑自然", "justify-content:space-between" not in h.split(".pg-mode{")[1].split("}")[0],
        "方式组被拉开大间隙（巨丑），应为紧凑自然排布")
    chk("时间·下拉填满右对齐", ".time-grid .date{display:flex" in h
        and ".time-grid .date .dsel{flex:1 1 auto" in h
        and ".time-grid .date .psel{flex:1 1 auto}" in h,
        "时间组日期下拉未弹性填满整行（会留中段空白）")
    chk("字体·JS 实测自适应", "function fitFont()" in h and 'addEventListener("resize",fitFont)' in h,
        "缺 fitFont——不支持 cqw/vw 的内核字号将不随宽度收窄")
    chk("页头·logo 高度随块", "--logoh:" in h and "height:var(--logoh)" in h,
        "logo 高度未与文字块等高")
    chk("字体·思源黑体优先", h.index('"Source Han Sans SC"') < h.index('"PingFang SC"'),
        "字体栈未把思源黑体排在苹方之前")
    # 页脚：居中三行——logo／署名／公众号｜微信｜官网（指令 36）
    fb = h.split('<footer class="brand">')[1].split("</footer>")[0]
    chk("品牌·logo 链官网", ('<a class="logo" href="%s"' % render.SITE) in fb
        and 'alt="魁君堂"' in fb, "logo 未链官网或缺 alt")
    chk("品牌·页脚三行次序", fb.index('class="logo"') < fb.index('class="sign"')
        < fb.index('class="fmeta"'), "页脚三行次序不对")
    chk("品牌·页脚居中样式", "flex-direction:column;align-items:center" in h
        and "text-align:center" in h.split(".brand{margin-top")[1].split("}")[0], "页脚未居中")
    chk("品牌·署名行无链接", "<a " not in fb.split('class="sign">')[1].split("</p>")[0],
        "署名行夹带了链接")
    chk("品牌·信息行齐备", render.GUARD1 in fb and render.GUARD2 in fb
        and "魁君堂官网：" in fb
        and fb.split('class="fmeta">')[1].count("<a ") == 1, "页脚信息行缺项或链接数不对")
    chk("品牌·信息行以｜分隔", fb.count('class="sep"') == 2, "信息行未用两道竖分隔")
    chk("品牌·官网只一次", h.count("kuijuntang.com</a>") == 1, "官网链接不止一处")
    chk("渲染·纯白背景", "body{\n  margin:0;background:#ffffff" in h or "background:#ffffff" in h)
    chk("品牌·署名制作", render.SIGN in h and "制作" in render.SIGN and "整理" not in render.SIGN,
        render.SIGN)
    chk("品牌·官网可点", 'href="%s"' % render.SITE in h and "魁君堂官网：" in h)
    chk("品牌·防盗文字", render.GUARD1 in h and render.GUARD2 in h, render.GUARD)
    chk("落款·无干支年季", "年秋" not in h and "年春" not in h and "年冬" not in h and "年夏" not in h)
    chk("渲染·MD 同源", all(k in m for k in ("天地否", "雷风恒", "丙午年", "戊午", "旬空：子丑")), "MD 缺关键项")
    chk("渲染·MD 段落留空行", "\n\n公历：" in m and "\n\n## " in m, "段落被并成一段")
    chk("渲染·MD 表九列", "| 六神 | 伏神 | 六亲纳甲 | 本卦爻 | 世应 | 动 |" in m)
    chk("渲染·MD 落款", render.SIGN in m and render.GUARD in m and render.SITE in m)

    # 可复制：爻线须为真字符，盘面须为真表格（粘贴进 Word 才不丢爻、不散列）
    chk("复制·爻线为字符", ('<td class="yao y1">%s</td>' % render.BAR_YANG) in h
        and ('<td class="yao y0">%s</td>' % render.BAR_YIN) in h, "爻线未以字符输出")
    chk("复制·阴阳等宽", len(render.BAR_YANG) == len(render.BAR_YIN) == render.BAR_WIDTH,
        "%r / %r" % (render.BAR_YANG, render.BAR_YIN))
    board = h.split('<table class="board')[1].split("</table>")[0]
    chk("复制·无图形爻线", "<i>" not in board and 'class="bar' not in board and "<img" not in board,
        "盘面内仍有图形爻线")
    hs = h.split("<script>")[0]
    chk("复制·真表格", '<table class="board"' in hs and "<tbody>" in hs and "<td" in hs)
    chk("复制·列宽写明", "<colgroup>" in hs and 'class="c1"' in hs and hs.count("<col ") == 9)
    chk("复制·表头跨列", 'colspan="6"' in hs and 'colspan="3"' in hs)
    # 神煞项须用半角空格分隔（防粘连 BUG-12；禁全角空格——其行尾不被裁、窄屏撑出约 13px 溢出 BUG-45）
    _i = hs.find('<span class="shen">')
    _shen = hs[_i: hs.find('</td>', _i)] if _i >= 0 else ""
    chk("复制·神煞用半角空格分隔（禁全角防溢出）",
        ('</span> <span>' in _shen) and ('\u3000' not in _shen),
        "神煞须半角空格分隔、禁全角空格")
    # 复制卦例钮（指令 83）：须复用页头 .fold 样式（UI 一致）；且**必须**位于 #pan-head 之外——
    # 若按钮落在 head 与 board 之间，会被 copyGua 的选区裹进去，贴到 Word 就多出一枚按钮
    chk("复制·有「复制卦例」钮且复用 .fold",
        'id="f-copy"' in hs and 'class="fold copybtn"' in hs and "复制卦例" in hs,
        "复制钮缺失或未复用 .fold 样式")
    _iBtn = hs.find('id="f-copy"')
    chk("复制·钮在 #pan-head 之外（不进复制选区）",
        0 <= _iBtn < hs.find('<div id="pan-head">'), "复制钮落在信息区内，会被一并复制进剪贴板")
    chk("复制·钮已绑定复制实现",
        "function copyGua()" in h and '$("f-copy")' in h, "缺少复制实现或事件未绑定")
    # 信息区须为无边框表格（指令 81）：段落版（<p>＋<br>、哪怕 inline margin:0）在 Word 里必被
    # 「段后距」撑开，且用户改行距无效——此题曾三轮返工（指令 76/79/81），故立硬断言，禁再退回段落
    chk("复制·信息区为表格（防 Word 段距复发）",
        '<table class="headtbl">' in hs and 'class="headinfo"' not in hs,
        "信息区退回段落了——Word 粘贴会再被段后距撑开、且改行距无效")
    # 打印时不印操作钮（指令 84）
    chk("打印·隐藏操作钮", "@media print{.copybtn,.top .fold{display:none}" in h,
        "缺打印规则：打印/存 PDF 会把「复制卦例」「收起排卦」印进成品")

    # 输入面板与浏览器端引擎
    chk("面板·姓名性别所问", all(k in hs for k in ("f-name", "f-gender", "f-q")))
    chk("面板·排盘方式两式", 'value="auto"' in hs and 'value="manual"' in hs)
    chk("面板·日期类型两式", 'value="solar"' in hs and 'value="lunar"' in hs)
    chk("面板·年月日时分", all(('id="f-%s"' % k) in hs for k in ("y", "m", "d", "h", "i")))
    chk("面板·六爻六个", all(('id="y%d"' % i) in hs for i in range(1, 7)))
    chk("引擎·内联数据表", "window.__JIE__" in h and "window.__LUNAR__" in h and "window.__GUA__" in h)
    chk("引擎·已装载", "window.__pani" in h)
    chk("引擎·无外链脚本", "src=\"http" not in h, "含外链资源")
    chk("面板·可折叠", 'id="f-fold"' in hs and 'aria-controls="panel"' in hs and 'id="panel"' in hs
        and "收起排卦" in hs, "折叠控件缺失")
    chk("面板·折叠钮在页头右上", hs.index('id="f-fold"') > hs.index('<header class="top">')
        and hs.index('id="f-fold"') < hs.index("</header>")
        and "margin-left:auto" in hs.split(".top .fold{")[1].split("}")[0], "折叠钮不在页头右上角")
    chk("面板·所问占位", 'placeholder="所问事情填写"' in hs, "所问占位未改")
    chk("面板·组名四组", hs.count('class="pg-lab"') == 4 and ".pg-lab::before" in h,
        "组名不是四组或不带朱条")
    chk("面板·组名为 信息/方式/时间/六爻",
        all(('>%s</span>' % t) in hs for t in ("信息", "方式", "时间", "六爻")), "组名文字不符")
    chk("面板·时间一行不折", "pg-body time-grid" in hs and "flex-wrap:nowrap" in h
        and ".dsel::after" in h, "时间组未锁单行或未用自绘箭头")
    chk("面板·时间单位入选项", "y+\"年\"" in h and "m+\"月\"" in h and 'i+"分"' in h,
        "时间选项未带单位")
    chk("面板·现时在末", hs.index('id="f-i"') < hs.index('id="f-now"'), "现时未排在分之后")
    chk("面板·默认男", '<option>男</option><option>女</option>' in hs, "性别默认非男")
    chk("复制·MD 爻线同为字符", render.BAR_YANG in m and render.BAR_YIN in m)

    # 无变卦（六爻安静）
    d2 = _paipan(lifa.parse_dt("2026-08-12 20:13"), [7, 7, 7, 7, 7, 7])
    chk("渲染·静卦不变", d2["changed"] is None)
    h2 = render.render_html(d2)
    h2s = h2.split("<script>")[0]        # 只看静态盘面，不数脚本源码里的模板串
    chk("渲染·静卦提示", "六爻安静" in h2)
    chk("渲染·静卦六列", h2s.count('colspan="6"') == 1 and 'colspan="3"' not in h2s)
    chk("渲染·静卦表满六列", '<table class="board six">' in h2s and h2s.count("<col ") == 6,
        "静卦列组不是六列")

    # 默认态：现在时刻、乾为天、男、所问占位
    d3 = _paipan(lifa.parse_dt("2026-10-31 23:59"), [7] * 6, gender="男", live=True)
    h3 = render.render_html(d3).split("<script>")[0]
    chk("默认·乾为天", "乾宫：乾为天" in h3 and "六爻安静" in render.render_html(d3))
    chk("默认·当前时刻", '"live": true' in render.render_html(d3), "未标记 live")

    # 初始态须完整承接起卦时的历法与晚子时口径（指令 89）：
    # 漏 leap 则农历闰月页一打开就错日；漏 lateZi 则 23 时后一动控件就换日柱
    d4 = paipan.paipan(lifa.parse_dt("2025-07-29 10:00"), [7, 8, 9, 6, 7, 8],
                       cal="lunar", leap=True, ymd=(2025, 6, 5))
    h4 = render.render_html(d4)
    chk("初始态·承接闰月", '"leap": true' in h4, "INIT 未带 leap，农历闰月页交互后即错日")
    d5 = paipan.paipan(lifa.parse_dt("2026-08-12 23:30"), [7] * 6, late_zi=False)
    h5 = render.render_html(d5)
    chk("初始态·承接晚子时口径", '"lateZi": false' in h5,
        "INIT 未带 lateZi，--no-late-zi 页一交互就换日柱")

    # 前端不得再用固定天数：公历须按大小月闰年、农历须按小月大月
    ui = engine_js.UI_JS
    chk("前端·公历日按实有天数", "function daysSolar(y,m)" in ui and "d<=31;" not in ui,
        "日下拉又写死 31 天，2 月 30 日会被静默滚到下月")
    chk("前端·农历日按实有天数", "lunarMonthLen" in ui and "for(var d=1;d<=30;d++" not in ui,
        "农历日下拉又写死 30 天，小月选三十会跨月")
    chk("前端·改年改月重填日期", "function syncDate()" in ui and "syncDate();" in ui,
        "换年换月未重填日/月下拉")
    chk("前端·越界年份报错", "超出可排范围" in engine_js.ENGINE_JS, "前端无年份护栏")


# ---------------------------------------------------------------- 卦名括注
def test_guatitle():
    """六合／六冲／游魂／归魂须在卦名后括注全显；八纯不括（道长令）。"""
    from render import _guatitle, GUATAGS
    strip = lambda x: re.sub(r"<[^>]+>", "", x)
    plain = strip(_guatitle({"gong": "乾", "name": "天地否", "tags": ["六合"]}))
    chk("括注·六合", plain == "乾宫：天地否（六合）", plain)
    pure = strip(_guatitle({"gong": "乾", "name": "乾为天", "tags": ["八纯", "六冲"]}))
    chk("括注·八纯不入括注", pure == "乾宫：乾为天（六冲）", pure)

    missed = []
    for name in gua.GONG_OF:
        h = gua.build(list(gua.GUA_BITS[gua.GUA_TO_NAME[name][1]])
                      + list(gua.GUA_BITS[gua.GUA_TO_NAME[name][0]]), None, "甲")
        want = [t for t in h["tags"] if t in GUATAGS]
        title = strip(_guatitle(h))
        for t in want:
            if "（" not in title or t not in title.split("（")[1]:
                missed.append((name, t, title))
    chk("括注·六十四卦类别全显", not missed, str(missed[:3]))

    cnt = {}
    for name in gua.GONG_OF:
        h = gua.build(list(gua.GUA_BITS[gua.GUA_TO_NAME[name][1]])
                      + list(gua.GUA_BITS[gua.GUA_TO_NAME[name][0]]), None, "甲")
        for t in h["tags"]:
            cnt[t] = cnt.get(t, 0) + 1
    chk("括注·类别计数", cnt == {"八纯": 8, "六冲": 10, "六合": 8, "游魂": 8, "归魂": 8}, str(cnt))

    # 八纯不括：乾为天只须见（六冲），不得出现「八纯」
    d = _paipan(lifa.parse_dt("2026-11-01 00:30"), [7] * 6)
    hs = render.render_html(d).split("<script>")[0]
    ms = render.render_md(d)
    chk("括注·八纯不显", "（六冲）" in hs and "八纯" not in hs and "八纯" not in ms,
        "乾为天仍标八纯")
    # 六合／六冲／游魂／归魂 四类仍须显（六十四卦全遍历）
    seen = set()
    for name in gua.GONG_OF:
        h = gua.build(list(gua.GUA_BITS[gua.GUA_TO_NAME[name][1]])
                      + list(gua.GUA_BITS[gua.GUA_TO_NAME[name][0]]), None, "甲")
        title = strip(_guatitle(h))
        for t in h["tags"]:
            if t in render.GUATAGS:
                seen.add(t)
                if t not in title:
                    chk("括注·%s 显于 %s" % (t, name), False, title)
    chk("括注·四类皆显", seen == set(render.GUATAGS), str(sorted(seen)))


def test_prob():
    """依《周易六爻概率学解密》（复城道长，2024-07-23）复核起卦概率。

    三枚钱一爻：6 老阴 1/8、7 少阳 3/8、8 少阴 3/8、9 老阳 1/8；
    故动爻 1/4、静爻 3/4，一次起卦的动爻个数分布如下（文中七档）。
    """
    from math import comb
    import paipan

    chk("概率·背数取爻", paipan.YAO_BY_BEI == {0: 6, 1: 7, 2: 8, 3: 9}, str(paipan.YAO_BY_BEI))
    # 八种等概组合：无背 1 种、一背 3 种、二背 3 种、三背 1 种
    tally = {6: 1, 7: 3, 8: 3, 9: 1}
    chk("概率·爻值权重", [tally[v] for v in (6, 7, 8, 9)] == [1, 3, 3, 1], str(tally))

    p, q = 0.25, 0.75
    got = [comb(6, k) * p ** k * q ** (6 - k) for k in range(7)]
    want = [17.80, 35.60, 29.66, 13.18, 3.30, 0.44, 0.024]      # 文中七档，百分比
    bad = [(k, round(g * 100, 3), w) for k, (g, w) in enumerate(zip(got, want))
           if abs(g * 100 - w) > 0.005]
    chk("概率·动爻七档合文", not bad, str(bad))
    chk("概率·合计为一", abs(sum(got) - 1) < 1e-12, "%.12f" % sum(got))
    chk("概率·静卦 17.80%", abs(got[0] * 100 - 17.80) < 0.005)
    chk("概率·一动 35.60%", abs(got[1] * 100 - 35.60) < 0.005)
    chk("概率·六动万分之二", abs(got[6] * 100 - 0.0244) < 0.001)


def test_toss():
    """随机起卦须模拟三枚钱：6/7/8/9 = 1/8、3/8、3/8、1/8，而非四选一均匀。"""
    import paipan
    cnt = {6: 0, 7: 0, 8: 0, 9: 0}
    rounds = 1200
    for _ in range(rounds):
        for v in paipan.random_yao():
            cnt[v] += 1
    total = sum(cnt.values())
    want = {6: 0.125, 7: 0.375, 8: 0.375, 9: 0.125}
    worst = max(abs(cnt[k] / total - want[k]) for k in want)
    chk("起卦·掷钱概率", worst < 0.02,
        "偏差 %.3f：%s" % (worst, {k: round(cnt[k] / total, 3) for k in sorted(cnt)}))
    moving = (cnt[6] + cnt[9]) / total
    chk("起卦·动爻两成半", abs(moving - 0.25) < 0.03, "动爻占 %.3f" % moving)
    chk("起卦·非均匀", abs(cnt[6] / total - 0.25) > 0.05, "老阴仍近四分之一，疑为均匀随机")

    # —— 结构守护（指令 86）：必须是「三枚钱一爻」逐枚掷——
    # 只测分布不足以防退化：若改成「按权重 1/8·3/8·3/8·1/8 直接抽爻值」，
    # 分布、动爻率、卡方全都照样通过，但已不是摇六次三钱，且无从核背数。
    import inspect
    src = inspect.getsource(paipan.random_yao)
    flat = "".join(src.split())
    chk("起卦·逐枚掷钱（Python 三次取背）",
        flat.count("randbelow(2)") == 3 and "YAO_BY_BEI[" in flat,
        "randbelow(2) 出现 %d 次" % flat.count("randbelow(2)"))
    chk("起卦·不得按权重直抽爻值（Python）",
        not any(t in flat for t in ("choice((6,7,8,9))", "choice([6,7,8,9])",
                                    "randbelow(4)", "randrange(4)")),
        "发现疑似四选一／加权抽取")

    import engine_js
    js = "".join((engine_js.ENGINE_JS + engine_js.UI_JS).split())
    chk("起卦·逐枚掷钱（浏览器 flip×3）",
        ("flip()+flip()+flip()" in js) and ("[6,7,8,9][" in js),
        "未找到三枚相加取爻的写法")
    chk("起卦·不得按权重直抽爻值（浏览器）",
        not any(t in js for t in ("[6,7,8,9][Math.floor", "Math.random()*4",
                                   "Math.floor(Math.random()*4)")),
        "发现疑似四选一抽取")


def main():
    test_golden()
    test_64()
    test_lifa()
    test_shensha()
    test_prob()
    test_toss()
    test_render()
    test_guatitle()
    print("自检：%d 项通过，%d 项失败" % (N_OK, len(FAILS)))
    for f in FAILS:
        print("  ✗ " + f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
