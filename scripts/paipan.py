#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paipan.py —— 六爻排盘命令行入口。

用法
----
  python3 paipan.py --date "2026-08-12 20:13" --yao 8,6,6,7,9,9 \
      --gender 女 --question "问工作" --out ./out/gua

  # 铜钱法（三枚，记背数或字背串），爻序默认自初爻至上爻
  python3 paipan.py --date "2026-08-12 20:13" --coins "字背背,背背背,..."

  # 摇卦记录是自上而下，可加 --order top
  python3 paipan.py --date "..." --yao 9,9,7,6,6,8 --order top

爻值：6 老阴（动）、7 少阳（静）、8 少阴（静）、9 老阳（动）。
"""
import argparse
import datetime
import json
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gua          # noqa: E402
import lifa         # noqa: E402
import render       # noqa: E402
import shensha      # noqa: E402

YAO_NAME = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}


def _split(text):
    for ch in ("，", "、", " ", ";", "；"):
        text = text.replace(ch, ",")
    return [t.strip() for t in text.split(",") if t.strip()]


def parse_yao(text, order="bottom"):
    vals = []
    for tok in _split(text):
        if tok not in ("6", "7", "8", "9"):
            raise SystemExit("爻值只能用 6/7/8/9（老阴/少阳/少阴/老阳）：%s" % tok)
        vals.append(int(tok))
    if len(vals) != 6:
        raise SystemExit("须给满六爻，现得 %d 个：%s" % (len(vals), text))
    return list(reversed(vals)) if order == "top" else vals


def parse_coins(text, order="bottom"):
    """三枚铜钱：每爻记背数（0–3）或字背串（背/字，或 正/反）。"""
    vals = []
    for tok in _split(text):
        tok = tok.strip()
        if tok in ("0", "1", "2", "3"):
            n = int(tok)
        else:
            if len(tok) != 3:
                raise SystemExit("每爻须三枚铜钱，如「背字字」或背数 2：%s" % tok)
            n = 0
            for c in tok:
                if c in ("背", "反", "阴"):
                    n += 1
                elif c not in ("字", "正", "阳"):
                    raise SystemExit("铜钱面只认「背/字」（或 反/正）：%s" % tok)
        vals.append({0: 6, 1: 7, 2: 8, 3: 9}[n])
    if len(vals) != 6:
        raise SystemExit("须给满六爻，现得 %d 个" % len(vals))
    return list(reversed(vals)) if order == "top" else vals


# 三枚钱一爻：背数 → 爻值。反（背）为阳，正是《周易六爻概率学解密》的口径：
# 三背老阳 9、二背少阴 8、一背少阳 7、无背老阴 6
YAO_BY_BEI = {0: 6, 1: 7, 2: 8, 3: 9}


def random_yao():
    """模拟三枚铜钱：每爻掷三枚，背数 0–3 按 YAO_BY_BEI 取爻。
    故 6/7/8/9 概率为 1/8、3/8、3/8、1/8——是摇卦本身的分布，不是四选一的均匀随机。"""
    return [YAO_BY_BEI[secrets.randbelow(2) + secrets.randbelow(2) + secrets.randbelow(2)]
            for _ in range(6)]


def paipan(dt, yao_values, gender="", question="", late_zi=True, method="数字",
           name="", mode="manual", cal="solar", leap=False, ymd=None, live=False):
    p = lifa.four_pillars(dt, late_zi=late_zi)
    bits = [1 if v in (7, 9) else 0 for v in yao_values]
    mov = [v in (6, 9) for v in yao_values]

    pri = gua.build(bits, mov, p["day"][0])
    gua.add_fushen(pri)
    gua.kong_flags(pri, p["kong"])
    ch = gua.bian(pri)
    if ch:
        gua.kong_flags(ch, p["kong"])

    return {
        "input": {
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "solar_text": lifa.solar_text(dt),
            "name": name,
            "gender": gender,
            "question": question,
            "mode": mode,
            "cal": cal,
            "leap": bool(leap),
            "ymd": list(ymd or [dt.year, dt.month, dt.day]),
            "hour": dt.hour,
            "minute": dt.minute,
            "yao_values": yao_values,
            "yao_names": [YAO_NAME[v] for v in yao_values],
            "method": method,
            "late_zi": late_zi,
            "live": bool(live),
        },
        "pillars": p,
        "shensha": shensha.compute(p["day"][0], p["day"][1], p["month_zhi"]),
        "primary": pri,
        "changed": ch,
    }


def write_out(data, out=None, html_path=None, md_path=None, json_path=None):
    written = []
    if out:
        html_path = html_path or out + ".html"
        md_path = md_path or out + ".md"
    if html_path:
        os.makedirs(os.path.dirname(os.path.abspath(html_path)), exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render.render_html(data))
        written.append(html_path)
    if md_path:
        os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render.render_md(data))
        written.append(md_path)
    if json_path:
        os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        written.append(json_path)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="六爻排盘")
    ap.add_argument("--date", help="公历时间，如 2026-08-12 20:13")
    ap.add_argument("--now", action="store_true", help="以当前时刻起卦")
    ap.add_argument("--yao", help="六爻爻值，自初爻至上爻，如 8,6,6,7,9,9")
    ap.add_argument("--coins", help="三枚铜钱记录，自初爻至上爻，如 字背背,背背背,…")
    ap.add_argument("--random", action="store_true", help="随机起卦（非人手摇，仅备无处摇时）")
    ap.add_argument("--order", choices=("bottom", "top"), default="bottom",
                    help="爻序：bottom 自初爻起（默认）；top 为摇卦记录的自上而下")
    ap.add_argument("--name", default="", help="姓名")
    ap.add_argument("--mode", choices=("manual", "auto"), default="manual",
                    help="排盘方式：manual 手工指定（默认）／auto 自动起卦")
    ap.add_argument("--cal", choices=("solar", "lunar"), default="solar",
                    help="日期类型：solar 公历（默认）／lunar 农历")
    ap.add_argument("--leap", action="store_true", help="农历闰月")
    ap.add_argument("--gender", default="男", help="乾造/坤造，或 男/女（默认 男）")
    ap.add_argument("--question", default="", help="所问之事")
    ap.add_argument("--no-late-zi", action="store_true", help="23 时后不换日柱")
    ap.add_argument("--live", action="store_true",
                    help="页面打开时取当前时刻（--date／--now 皆未给时自动启用）")
    ap.add_argument("--out", help="输出前缀，生成 前缀.html 与 前缀.md")
    ap.add_argument("--html")
    ap.add_argument("--md")
    ap.add_argument("--json", dest="json_path")
    ap.add_argument("--print-md", action="store_true", help="把 MD 文本打到标准输出")
    a = ap.parse_args(argv)

    # 默认态：未指定时间即取此刻（页面打开时按真实当前时间重排），未指定爻即乾为天
    live = (a.date is None and not a.now) or a.live
    dt = datetime.datetime.now() if (a.now or a.date is None) else lifa.parse_dt(a.date)

    if a.coins:
        yao, method = parse_coins(a.coins, a.order), "铜钱"
    elif a.yao:
        yao, method = parse_yao(a.yao, a.order), "数字爻值"
    elif a.random:
        yao, method = random_yao(), "随机（非人手摇）"
    else:
        yao, method = [7, 7, 7, 7, 7, 7], "默认（乾为天）"

    ymd = None
    if a.cal == "lunar":
        ly, lm, ld = dt.year, dt.month, dt.day
        sy, sm, sd = lifa.lunar_to_solar(ly, lm, ld, a.leap)
        dt = dt.replace(year=sy, month=sm, day=sd)
        ymd = (ly, lm, ld)
    data = paipan(dt, yao, a.gender.strip(), a.question.strip(),
                  late_zi=not a.no_late_zi, method=method,
                  name=a.name.strip(), mode=a.mode, cal=a.cal, leap=a.leap, ymd=ymd,
                  live=live)
    written = write_out(data, a.out, a.html, a.md, a.json_path)

    pri, ch = data["primary"], data["changed"]
    head = "%s宫：%s" % (pri["gong"], pri["name"])
    if ch:
        head += " 之 %s宫：%s" % (ch["gong"], ch["name"])
    print("%s　%s　%s" % (data["input"]["solar_text"],
                          " ".join([data["pillars"][k] for k in ("year", "month", "day", "hour")]),
                          head))
    if written:
        print("已写出：" + "　".join(written))
    if a.print_md:
        print()
        print(render.render_md(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
