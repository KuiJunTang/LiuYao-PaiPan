#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lifa.py —— 历法层：四柱、旬空、月建、农历互转。

口径
----
* 时区：北京时间（UTC+8），不做夏令时还原。
* 年柱：立春换年。
* 月柱：十二「节」换月（立春→寅、惊蛰→卯……小寒→丑），非中气。
* 日柱：连续六十甲子；默认晚子时（23:00 起）归次日，可用 late_zi=False 关闭。
* 时柱：五鼠遁（日干起时干），子时 23:00–00:59。
* 旬空：以日柱所在旬取旬首后二支。
* 农历：以「春节偏移＋闰月号＋月大小掩码」表推，不依赖任何天文库。

数据来源（无外部依赖）
----------------------
本模块只读 `tables_js.py` 三张表：
  · JIE   —— 1900–2100 每年十二节交节时刻（距当年 1 月 1 日 0 时的分钟数，base36 定宽 4）
  · LUNAR —— 1900–2100 农历（春节偏移＋闰月号＋月大小掩码，每年 8 字符）
  · DAY0  —— 儒略日 → 六十甲子序的平移量
表由 `build_tables.py` 用寿星天文历（sxtwl）一次生成，随包分发，运行期**不再需要 sxtwl**。
表值本身由开发期 `check_tables.py`（重算出表、逐字比对）把关；干支组合、换年换月、旬空、
农历换算等**逻辑**，由 `audit_gua.py` 另起一套公式复核。二者分工：表归天文库校，逻辑归独立公式校。
"""
import datetime

import tables_js

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
          "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

# 六十甲子（索引即 0–59）
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]

# 十二节（与 build_tables.py 同序，仅为可读保留）
JIE_IDX = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23)
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# 可排年份：与随包历法表（tables_js.YEAR_FROM..YEAR_TO）及页面年份下拉同此一界，
# 三处不得各自为政。
YEAR_MIN, YEAR_MAX = tables_js.YEAR_FROM, tables_js.YEAR_TO

LUNA_DAY = ("初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
            "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
            "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十")
LUNA_MON = ("正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊")

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def _b36(s):
    n = 0
    for c in s:
        n = n * 36 + B36.index(c)
    return n


def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _doy(y, m, d):
    n = sum(MONTH_DAYS[:m - 1]) + d
    if m > 2 and _is_leap(y):
        n += 1
    return n


def jdn(y, m, d):
    """公历 → 儒略日数（整数）。"""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def _from_jdn(n):
    """儒略日数 → 公历 (y, m, d)。"""
    a = n + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    dd = (4 * c + 3) // 1461
    e = c - 1461 * dd // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    mon = m + 3 - 12 * (m // 10)
    yr = 100 * b + dd - 4800 + m // 10
    return yr, mon, day


def _check_year(y, kind="公历"):
    if not (YEAR_MIN <= y <= YEAR_MAX):
        raise SystemExit("可排年份为 %d–%d 年（历法表与页面年份下拉同此范围）；"
                         "所给%s %d 年超界。" % (YEAR_MIN, YEAR_MAX, kind, y))


# ------------------------------------------------------------------ 节气
def jie_minute(y, i):
    """(公历年, 节序 0–11) → 该节距当年 1 月 1 日 0 时的分钟数。

    节序：0 小寒、1 立春、2 惊蛰、3 清明、4 立夏、5 芒种、
          6 小暑、7 立秋、8 白露、9 寒露、10 立冬、11 大雪（公历 1–12 月各一节）。
    """
    _check_year(y)
    p = ((y - YEAR_MIN) * 12 + i) * 4
    return _b36(tables_js.JIE_JS[p:p + 4])


# ------------------------------------------------------------------ 农历表
def _lunar_rec(y):
    _check_year(y, "农历")
    p = (y - YEAR_MIN) * 8
    return tables_js.LUNAR_JS[p:p + 8]


def _cny_offset(y):
    """该农历年正月初一距 1900-01-31 的天数。"""
    return _b36(_lunar_rec(y)[:4])


def lunar_leap_month(y):
    """该农历年的闰月号（1–12），无闰月为 0。"""
    return _b36(_lunar_rec(y)[4])


def _lunar_seq(y):
    """[(月, 是否闰), ...]，闰月插在本月之后——与前端 lunarSeq() 同序。"""
    leap = lunar_leap_month(y)
    seq = []
    for m in range(1, 13):
        seq.append((m, False))
        if leap == m:
            seq.append((m, True))
    return seq


def lunar_month_len(y, m, leap=False):
    """该农历年该月（含闰月）实有天数：29 或 30。"""
    seq = _lunar_seq(y)
    if (m, bool(leap)) not in seq:
        run = lunar_leap_month(y)
        raise SystemExit("农历 %d 年没有闰%s月（%s）。"
                         % (y, LUNA_MON[m - 1],
                            ("该年闰%s月" % LUNA_MON[run - 1]) if run else "该年无闰月"))
    mask = _b36(_lunar_rec(y)[5:8])
    i = seq.index((m, bool(leap)))
    return 30 if (mask >> i) & 1 else 29


def lunar_to_solar(y, m, d, leap=False):
    """农历 → 公历 (y, m, d)。

    不存在的日期一律报错，绝不静默改写：旧版直接问天文库，遇「小月三十」「该年无此闰月」
    会被顺延到下月／次年，等于替用户改了他没选的日子（BUG-49）。
    """
    _check_year(y, "农历")
    if not (1 <= m <= 12):
        raise SystemExit("农历月份须在 1–12：%d" % m)
    run = lunar_leap_month(y)
    if leap and run != m:
        raise SystemExit("农历 %d 年没有闰%s月（%s）。"
                         % (y, LUNA_MON[m - 1],
                            ("该年闰%s月" % LUNA_MON[run - 1]) if run else "该年无闰月"))
    n = lunar_month_len(y, m, leap)
    if not (1 <= d <= n):
        raise SystemExit("农历 %d 年%s%s月只有%d天，没有%s。"
                         % (y, "闰" if leap else "", LUNA_MON[m - 1], n, LUNA_DAY[d - 1]))
    seq = _lunar_seq(y)
    mask = _b36(_lunar_rec(y)[5:8])
    days = _cny_offset(y)
    for i, item in enumerate(seq):
        if item == (m, bool(leap)):
            break
        days += 30 if (mask >> i) & 1 else 29
    days += d - 1
    return _from_jdn(jdn(1900, 1, 31) + days)


def solar_to_lunar(dt):
    """公历 → 农历 (y, m, d, is_leap)。"""
    _check_year(dt.year)
    days = jdn(dt.year, dt.month, dt.day) - jdn(1900, 1, 31)
    y = YEAR_MIN
    while y < YEAR_MAX and _cny_offset(y + 1) <= days:
        y += 1
    seq = _lunar_seq(y)
    mask = _b36(_lunar_rec(y)[5:8])
    rest = days - _cny_offset(y)
    i = 0
    while i < len(seq) and rest >= (30 if (mask >> i) & 1 else 29):
        rest -= 30 if (mask >> i) & 1 else 29
        i += 1
    if i >= len(seq):
        i = len(seq) - 1
    return y, seq[i][0], rest + 1, seq[i][1]


# ------------------------------------------------------------------ 干支
def jiazi_index(gan, zhi):
    """干支 → 六十甲子序号 0–59。"""
    for i in range(60):
        if GAN[i % 10] == gan and ZHI[i % 12] == zhi:
            return i
    raise ValueError("非法干支：%s%s" % (gan, zhi))


def xun_kong(day_index):
    """日柱序号 → 旬空二支（旬首后二支）。"""
    head = day_index - day_index % 10
    return [ZHI[(head + 10) % 12], ZHI[(head + 11) % 12]]


def xun_name(day_index):
    """日柱所属旬名，如「甲寅」。"""
    head = day_index - day_index % 10
    return GAN[0] + ZHI[head % 12]


def shi_chen(hour):
    """小时 → 时支（23:00 起子时）。"""
    return ZHI[((hour + 1) // 2) % 12]


def day_index(dt):
    """公历日 → 日柱六十甲子序。"""
    return (jdn(dt.year, dt.month, dt.day) + tables_js.DAY0_JS) % 60


def four_pillars(dt, late_zi=True):
    """公历 datetime → 四柱。

    返回 dict：year/month/day/hour（干支字符串）、day_index、kong（二支）、
    month_zhi（月建支）、hour_zhi、late_zi_applied、xun（旬名）。
    """
    _check_year(dt.year)

    idx = day_index(dt)
    late = False
    if late_zi and dt.hour >= 23:
        idx = (idx + 1) % 60
        late = True
    day_s = JIAZI[idx]

    # 年柱、月柱按「交节时刻」判定，不看整日：交节当日时刻未到便不得提前换年换月
    now = (_doy(dt.year, dt.month, dt.day) - 1) * 1440 + dt.hour * 60 + dt.minute
    yb = dt.year
    if now < jie_minute(dt.year, 1):        # 未过立春，属上一年
        yb -= 1
    yi = (yb - 4) % 60
    year = GAN[yi % 10] + ZHI[yi % 12]
    ji = 11                                  # 早于小寒者，承上年大雪，子月
    if now >= jie_minute(dt.year, 0):
        for k in range(11, -1, -1):
            if now >= jie_minute(dt.year, k):
                ji = k
                break
    mz = (ji + 1) % 12
    yin_gan = ((yi % 10) % 5) * 2 + 2         # 五虎遁：甲己丙作首
    m_gan = (yin_gan + (mz - 2 + 12) % 12) % 10
    month = GAN[m_gan] + ZHI[mz]

    # 时柱：五鼠遁（甲己起甲子、乙庚起丙子、丙辛起戊子、丁壬起庚子、戊癸起壬子）
    hz = ((dt.hour + 1) // 2) % 12
    hg = (GAN.index(day_s[0]) * 2 + hz) % 10
    hour = GAN[hg] + ZHI[hz]

    return {
        "year": year, "month": month, "day": day_s, "hour": hour,
        "day_index": idx,
        "kong": xun_kong(idx),
        "xun": xun_name(idx),
        "month_zhi": month[1],
        "hour_zhi": hour[1],
        "late_zi_applied": late,
    }


def parse_dt(text):
    """解析 "YYYY-MM-DD HH:MM" / "YYYY/MM/DD HH:MM" / "YYYY-MM-DDTHH:MM"。"""
    t = text.strip().replace("/", "-").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(t, fmt)
        except ValueError:
            continue
    raise SystemExit("时间格式无法识别：%s（应为 2026-08-12 20:13）" % text)


def solar_text(dt):
    """公历中文显示：2026年8月12日 20时13分。"""
    return "%d年%d月%d日 %d时%d分" % (dt.year, dt.month, dt.day, dt.hour, dt.minute)


def jieqi_of_month(month_zhi):
    """月建支 → 当令节名。"""
    table = {"寅": "立春", "卯": "惊蛰", "辰": "清明", "巳": "立夏", "午": "芒种",
             "未": "小暑", "申": "立秋", "酉": "白露", "戌": "寒露", "亥": "立冬",
             "子": "大雪", "丑": "小寒"}
    return table[month_zhi]
