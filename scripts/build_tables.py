#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_tables.py —— 由 Python 引擎生成浏览器端所需数据表（单一数据源）。

产出 tables_js.py，内含数据常量，由 render.py 内联进单文件 HTML。
凡改卦理表（gua.py）或神煞表（shensha.py），重跑本脚本，勿手改 tables_js.py。

表内容
------
* JIE   ：1900–2100 每年十二「节」的交节时刻（距当年 1 月 1 日 0 时的分钟数，base36 定宽 4）
* LUNAR ：1900–2100 农历（春节偏移 + 闰月号 + 月大小掩码，每年 8 字符）
* GUA   ：六十四卦（按六爻阴阳位串索引）、八宫、纳甲、宫五行、六合六冲
* SHEN  ：十四神煞所需表
* DAY0  ：日柱六十甲子的儒略日基准
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gua       # noqa: E402
import shensha   # noqa: E402

YEAR_FROM, YEAR_TO = 1900, 2100
B36 = "0123456789abcdefghijklmnopqrstuvwxyz"

# 十二节：sxtwl 的 jqIndex 序为「冬至0 小寒1 大寒2 立春3 雨水4 惊蛰5 …」，
# 取 1,3,5…23 恰好是公历 1–12 月各一节，依次主 丑寅卯辰巳午未申酉戌亥子 月。
JIE_IDX = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def b36(n, width):
    s = ""
    while n:
        s = B36[n % 36] + s
        n //= 36
    return s.rjust(width, "0")


def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _day_of_year(y, m, d):
    days = sum(MONTH_DAYS[:int(m) - 1]) + int(d)
    if int(m) > 2 and _is_leap(y):
        days += 1
    return days


def _jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def build_jie():
    import sxtwl
    # 一次扫全区间，按（公历年, jqIndex）索引，避免年界处的节气落到别年
    pool = {}
    for yy in range(YEAR_FROM - 1, YEAR_TO + 2):
        for item in sxtwl.getJieQiByYear(yy):
            dd = sxtwl.JD2DD(item.jd)
            pool[(dd.Y, item.jqIndex)] = (dd.M, dd.D, dd.h, dd.m, dd.s)
    out = []
    for y in range(YEAR_FROM, YEAR_TO + 1):
        for idx in JIE_IDX:
            key = (y, idx)
            if key not in pool:
                raise SystemExit("%d 年节气缺 jqIndex=%d" % (y, idx))
            M, D, h, mi, _sec = pool[key]
            minute = (_day_of_year(y, M, D) - 1) * 1440 + int(h) * 60 + int(mi)
            if not (0 <= minute < 36 ** 4):
                raise SystemExit("%d 年节气偏移越界：%d" % (y, minute))
            out.append(b36(minute, 4))
    return "".join(out)


def _lunar_first_jdn(y, m, leap):
    import sxtwl
    d = sxtwl.fromLunar(y, m, 1, leap)
    return _jdn(d.getSolarYear(), d.getSolarMonth(), d.getSolarDay())


def build_lunar():
    import sxtwl
    base = _jdn(1900, 1, 31)                 # 1900 年正月初一
    out = []
    for y in range(YEAR_FROM, YEAR_TO + 1):
        off = _lunar_first_jdn(y, 1, False) - base
        leap = sxtwl.getRunMonth(y)
        starts = []
        for m in range(1, 13):
            starts.append(_lunar_first_jdn(y, m, False))
            if leap == m:
                starts.append(_lunar_first_jdn(y, m, True))
        starts.append(_lunar_first_jdn(y + 1, 1, False))
        lens = [starts[i + 1] - starts[i] for i in range(len(starts) - 1)]
        if any(n not in (29, 30) for n in lens):
            raise SystemExit("%d 年农历月长异常：%s" % (y, lens))
        mask = 0
        for i, n in enumerate(lens):
            if n == 30:
                mask |= 1 << i
        out.append(b36(off, 4) + b36(leap, 1) + b36(mask, 3))
    return "".join(out)


def build_gua():
    gua64 = {}
    for (up, lo), name in gua.NAME_TO_GUA.items():
        bits = list(gua.GUA_BITS[lo]) + list(gua.GUA_BITS[up])
        gua64["".join(str(b) for b in bits)] = name
    data = {
        "gua64": gua64,
        "gong": {g: v for g, v in gua.GONG.items()},
        "najia": {g: [[a, b] for a, b in v] for g, v in gua.NAJIA.items()},
        "gongWx": gua.GONG_WX,
        "shi": gua._SHI_BY_INDEX,
        "liuhe": sorted(gua.LIUHE_GUA),
        "liuchong": sorted(gua.LIUCHONG_GUA),
        "liuqinOrder": gua.LIUQIN_ORDER,
        "liushen": gua.LIUSHEN,
        "zhiWx": gua.ZHI_WX,
        "ganWx": gua.GAN_WX,
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def build_shen():
    data = {
        "sanhe": {k: list(v) for k, v in shensha._SANHE.items()},
        "lu": shensha._LU,
        "ren": shensha._REN,
        "wenchang": shensha._WENCHANG,
        "guiren": {k: list(v) for k, v in shensha._GUIREN.items()},
        "ride": shensha._RI_DE,
        "tianma": shensha._TIANMA,
        "order": shensha.ORDER,
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def build_day0():
    """日柱基准：儒略日 → 六十甲子序的平移量，用 lifa 校准（同一口径）。"""
    import datetime
    import lifa
    p = lifa.four_pillars(datetime.datetime(2000, 1, 1, 12, 0))
    return (p["day_index"] - _jdn(2000, 1, 1)) % 60


def main():
    jie = build_jie()
    lunar = build_lunar()
    day0 = build_day0()
    js = (
        '"""tables_js.py —— 由 build_tables.py 生成，勿手改。"""\n\n'
        "YEAR_FROM = %d\nYEAR_TO = %d\n\n" % (YEAR_FROM, YEAR_TO)
        + "JIE_JS = \"%s\"\n\n" % jie
        + "LUNAR_JS = \"%s\"\n\n" % lunar
        + "DAY0_JS = %d\n\n" % day0
        + "GUA_JS = r'''%s'''\n\n" % build_gua()
        + "SHEN_JS = r'''%s'''\n" % build_shen()
    )
    with open(os.path.join(HERE, "tables_js.py"), "w", encoding="utf-8") as f:
        f.write(js)
    print("tables_js.py 已生成：节气 %d 字符，农历 %d 字符，DAY0=%d"
          % (len(jie), len(lunar), day0))


if __name__ == "__main__":
    main()
