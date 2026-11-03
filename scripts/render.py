#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render.py —— 渲染层：单文件 HTML（纯白、零外部依赖、可交互、响应式）与同名 MD 底本。

三条硬约束
1. **可复制**：爻线用真字符（U+2581），盘面用真 `<table>`，神煞用真空格分隔。
   不得以 CSS 色块画爻、不得以 grid 排表、不得只靠 CSS gap 造间距——Word 认不出这些。
2. **列宽写明**：`<colgroup>` 给百分比列宽，间隙计入列宽而非 padding，
   粘进 Word 才不会挤成折行。
3. **与 JS 同源**：页面内的浏览器端引擎（engine_js.py）生成同样结构，parity_check 逐字比对。
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

import gua          # noqa: E402
import shensha      # noqa: E402

try:
    import tables_js   # noqa: E402
    _DATA = ("JIE", "LUNAR", "DAY0", "GUA", "SHEN")
except ImportError:
    _DATA = ()

from engine_js import ENGINE_JS, UI_JS   # noqa: E402

SITE = "https://www.kuijuntang.com"
SITE_TEXT = "www.kuijuntang.com"      # 页脚链接的显示文字（照参考图，不带协议头）
SITE_LABEL = "魁君堂官网："
SIGN = "膠東魁君堂　復城道長　制作"
GUARD1 = "微信公众号：魁君堂"
GUARD2 = "复城道长微信：18550386868"
GUARD = GUARD1 + "　" + GUARD2        # MD 底本用连续文本；HTML 页脚以「｜」分隔（指令 36）
LOGO_FILE = os.path.join(ASSETS, "logo-kuijuntang.png")
LOGO_W, LOGO_H = 560, 126          # assets/logo-kuijuntang.png 的像素尺寸，供 <img> 定比例
_LOGO_URI = None

BAR_YANG = "───"
BAR_YIN = "─　─"
BAR_WIDTH = 3
# 卦名后括注的类别：八纯不括（道长令，2026-11-01），八纯卦本身必为六冲，故仍见（六冲）
GUATAGS = ("六合", "六冲", "游魂", "归魂")

_CSS = """
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#ffffff;color:#1a1a1a;
  font-family:"Source Han Sans SC","Source Han Sans CN","Noto Sans CJK SC","Noto Sans SC",
    "思源黑体","PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,-apple-system,sans-serif;
  font-size:15px;line-height:1.5}
.pan{max-width:660px;margin:0 auto;padding:26px 24px 22px}

/* —— 页顶：魁君堂 logo ＋ 题名 —— */
/* logo 与「题名＋副标题」整块上下居中；logo 高取等于该块总高，上下才齐平 */
.top{--logoh:clamp(32px,7vw,44px);display:flex;align-items:center;gap:14px;
  padding:0 0 13px;margin:0 0 16px;border-bottom:1px solid #ededed}
.top .tlogo{flex:0 0 auto;display:block;line-height:0;text-decoration:none;border:0}
.top .tlogo img{display:block;height:var(--logoh);width:auto;border:0}
.top .tlogo:hover{opacity:.82}
.top .tseal{display:inline-flex;align-items:center;justify-content:center;
  border:1.5px solid #9c3a2e;color:#9c3a2e;border-radius:2px;padding:.2em .45em;
  font-size:.82em;letter-spacing:.1em;writing-mode:vertical-rl}
.top .tsep{flex:0 0 auto;width:1px;align-self:stretch;margin:2px 0;background:#e6e6e6}
.top .ttext{min-width:0}
.top h1{margin:0;font-size:1.3em;font-weight:600;letter-spacing:.16em;
  line-height:1.24;color:#1a1a1a;white-space:nowrap}
.top .tsub{margin:.3em 0 0;font-size:.76em;color:#8c8c8c;letter-spacing:.09em;
  line-height:1.3;white-space:nowrap}

/* —— 起卦面板：卡片分块，四组各一行 —— */
.panel{margin:0 0 1.5em;padding:16px 18px 15px;background:#f7f6f2; /* 照道长参考图取色 */
  border:1px solid #f0efea;border-radius:12px}
/* 四组等距：每组行高恒为 30px，组间距恒为 12px，视觉上段距一律相等 */
.pgroup{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:12px;
  align-items:center;min-height:30px}
.pgroup+.pgroup{margin-top:12px}
.pg-lab{display:inline-flex;align-items:center;gap:8px;color:#1f1f1f;font-size:1.02em;
  font-weight:600;letter-spacing:.08em;white-space:nowrap;line-height:1}
.pg-lab::before{content:"";flex:0 0 auto;width:3px;height:1em;border-radius:2px;background:#9c3a2e}
.pg-body{display:flex;flex-wrap:wrap;align-items:center;gap:9px 14px;min-width:0;min-height:30px}
.fld{display:inline-flex;align-items:center;gap:7px;white-space:nowrap;min-width:0}
/* 方式组恒一行（指令 49）：自动/手工·公历/农历任何宽度不折行 */
.pg-mode{flex-wrap:nowrap;gap:8px 12px}
/* 所问一项用 basis 0 撑余宽：若按 auto，input 的固有宽（默认 20 字符）会把整行顶断 */
.fld-wide{flex:1 1 0;min-width:0}
.fld>span{color:#4a4a4a;font-size:.92em}
.ptext,.psel,.pbtn{height:30px;font:inherit;font-size:.95em;color:#1a1a1a;background:#fff;
  border:1px solid #e4e4e4;border-radius:7px;padding:0 9px;line-height:1}
.ptext{width:6.4em}
/* 所问弹性填满余宽，窄屏也不掉行 */
.ptext.wide{width:auto;flex:1 1 0;min-width:3.4em}
.psel{padding-right:18px}                     /* 右侧留给原生下拉箭头，免得箭头压字 */
.psel-s{min-width:3.8em}
.ptext:hover,.psel:hover{border-color:#d6d6d6}
.ptext:focus,.psel:focus{outline:none;border-color:#c8a29b;box-shadow:0 0 0 3px rgba(156,58,46,.08)}
.ptext::placeholder{color:#b6b6b6}
.pbtn{cursor:pointer;padding:0 12px;background:#fff}
.pbtn:hover{background:#f6f6f6;border-color:#d6d6d6}
.pr{display:inline-flex;align-items:center;gap:6px;color:#333;font-size:.94em;white-space:nowrap}
.pr input{accent-color:#9c3a2e;width:14px;height:14px;margin:0}
.vsep{width:1px;height:15px;background:#e8e8e8}
/* 时间组：恒为一行，任何分辨率都不折行（单位并入下拉文本，不再另占字位）
   箭头自绘：原生箭头在内容框内另占约 16px，五个下拉就是 80px，窄屏正是被它挤爆的
   弹性填满（指令 65）：五个日期下拉自身伸长填满整行——没有中段空白，
   现时按钮自然贴到全局右缘，间隙保持小而均匀 */
.time-grid{display:flex;flex-wrap:nowrap;align-items:center;gap:6px;width:100%}
.time-grid .date{display:flex;flex-wrap:nowrap;align-items:center;gap:5px;
  flex:1 1 auto;min-width:0}
.time-grid .date .dsel{flex:1 1 auto;min-width:0}
.dsel{position:relative;display:inline-flex;flex:0 1 auto;min-width:0}
.dsel .psel{width:auto}                    /* 其余组：宽度随最长选项，不硬拉满，免裁字 */
.time-grid .date .psel{flex:1 1 auto}   /* 时间组例外（指令 65）：flex 逐级填满（width:100% 在 inline-flex 内解析不到拉伸值），箭头才贴框 */
.dsel::after{content:"";position:absolute;right:7px;top:50%;width:0;height:0;
  border:3.5px solid transparent;border-top-color:#8c8c8c;
  transform:translateY(-25%);pointer-events:none}
.dsel .psel{appearance:none;-webkit-appearance:none;min-width:0;
  padding-left:5px;padding-right:15px}    /* 右内距给箭头留位，免贴字 */
.time-grid .pbtn{flex:0 0 auto;padding:0 9px}
/* 六爻：恒为三列两行——初二三（内卦）／四五上（外卦），任何宽度都不变 */
.yao-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 10px;width:100%}
.yao-cell{display:flex;align-items:center;gap:4px;min-width:0}
.yao-cell>span{flex:0 0 2.2em;color:#4a4a4a;font-size:.92em;white-space:nowrap;
  height:30px;line-height:30px;display:inline-flex;align-items:center}
.yao-cell .dsel{flex:1 1 auto;min-width:0}
.yao-cell .psel{flex:1 1 auto;min-width:0;width:100%}
/* 折叠钮在页头右上角（指令 39），随页头各元素垂直居中 */
.top .fold{margin-left:auto;flex:0 0 auto}
.fold{height:26px;font-size:.84em;color:#7a7a7a;background:#fff;
  border:1px solid #ececec;border-radius:6px;padding:0 10px;cursor:pointer}
.fold:hover{background:#f7f7f7;color:#555}
.panel[hidden]{display:none}
.ask{margin:0;font-size:1em;font-weight:500;letter-spacing:.02em;line-height:1.9}
.meta{margin:0;font-size:1em;line-height:1.9}
/* 起卦信息区用「无边框表格」承载（指令 76/79/81）：Word 粘贴时表格逐行紧贴、不套段落「段后距」；
   段落版（<p>＋<br>、甚至 inline margin）在 Word 里仍被撑开且「改行距无效」，表格版与盘面同理最稳 */
.headtbl{width:100%;border-collapse:collapse;border:0;table-layout:fixed;margin:0}
.headtbl td{padding:0;border:0;vertical-align:top;line-height:1.9;font-size:1em;white-space:normal}
.headtbl .ask{word-spacing:.4em}
.headtbl .shen{font-size:.88em;color:#4a4a4a;word-spacing:.4em}  /* 项间用半角空格＋word-spacing：全角空格行尾不裁、窄屏会撑出 13px 溢出（BUG-45） */
.headtbl .shen .lab{color:#1a1a1a}
.headtbl .shen span{white-space:nowrap}
/* 复制卦例钮（指令 83）：与页头「收起排卦」同款 .fold，只去掉箭头；
   置于 #pan-head 之外（.headwrap 内）——引擎重绘只换 head/board 的 innerHTML，不会覆盖它，
   手工选中复制时它也不在选区内；user-select:none 再兜一层，确保永不进入 Word */
.headwrap{position:relative}
.copybtn{position:absolute;right:0;top:0;background:#fff;white-space:nowrap;
  user-select:none;-webkit-user-select:none}
.copybtn.done{color:#a02b2b;border-color:#e8d8d8}
.headtbl tr:first-child td{padding-right:80px}   /* 首行右侧给按钮让位，免长问句顶到钮上 */
/* 打印／另存 PDF 时不印操作钮（指令 84）：钮是交互件，不属于卦例内容；
   钮既隐藏，首行为它让出的右内距也一并归零，免纸上留一段空白 */
@media print{.copybtn,.top .fold{display:none}.headtbl tr:first-child td{padding-right:0}}
/* 旬空与正文同字号同色（指令 43），靠继承实现，不另设样式 */

/* —— 盘面：真表格，列宽写明 —— */
.board{width:100%;max-width:550px;margin:0 auto;border-collapse:collapse;table-layout:fixed;border:0}
/* 盘面字体与表宽强耦合（指令 41）：9 列表 550px↔15px 字（1/36.667）、静卦 318px↔15px（1/21.2），
   列宽用百分比、字宽随表等比，墨迹比例恒定，卦名居中才「时刻」成立。
   耦合基准用**容器**宽（cqw）而非视口：预览面板、iframe、分屏等「容器≠视口」场景同样成立（BUG-40） */
.pan{container-type:inline-size}
/* 字号随宽度收窄（指令 61 根治）：双保险——先写 vw 版（不认 cqw 的内核照常按视口
   收缩，比例与列宽耦合一致：.pan 左右内距恒 13px，容器宽=100vw−26px，两版数值相等），
   支持 cqw 的内核再用 @supports 覆盖为容器版（保住 BUG-40 的容器≠视口修复）。
   此前单靠 cqw，失效内核退回继承字号（比例错误），盘面五字干支装不下列宽，
   <wbr> 处折成两行——卦象分两行、行距过大、线压字、卦名截断皆此一因（指令 59） */
.top,.panel,.brand{font-size:min(15px,max(9px,calc((100vw - 26px)/32)))}
#pan-head,#pan-board,.headwrap{font-size:min(15px,calc((100vw - 26px)/36.667))}
#pan-board{margin-top:1.1em}   /* 恢复合并前神煞 margin-bottom 带来的盘前间距（指令 79） */
.sixpage #pan-head,.sixpage #pan-board,.sixpage .headwrap{font-size:min(15px,calc((100vw - 26px)/21.2))}
@supports (width:1cqw){
  .top,.panel,.brand{font-size:min(15px,max(9px,calc(100cqw/32)))}
  #pan-head,#pan-board,.headwrap{font-size:min(15px,calc(100cqw/36.667))}
  .sixpage #pan-head,.sixpage #pan-board,.sixpage .headwrap{font-size:min(15px,calc(100cqw/21.2))}
}
/* 列宽比例（指令 41、42）：本卦与变卦的卦名一律以「六亲纳甲｜爻｜世应」三列的
   墨迹中心为居中基准，六神、伏神、动爻不计（道长明示）。
   本卦六列之上，卦体墨迹中心在 th 几何中心右侧，以 .gmain 内距定向；
   变卦三列列宽本身满足 c7−c9=3.75ch 恒等式，无需定向。 */
.board col.c1{width:5.818%}
.board col.c2{width:14.091%}
.board col.c3{width:14.364%}
.board col.c4{width:9.091%}
.board col.c5{width:5.455%}
.board col.c6{width:12.318%}
.board col.c7{width:17.773%}
.board col.c8{width:12.727%}
.board col.c9{width:8.364%}
/* 卦名居中基准（指令 74）：只随卦象（六亲纳甲｜爻线），不考虑世应——
   本卦 gmain 左距 2.41%、静卦 9.89%、变卦 gsub 右距 6.51%（表宽百分比，跨宽度恒定） */
.board .gmain{padding-left:2.41%}
.board .gsub{padding-right:6.51%}
/* 静卦只有六列：表宽收为 318px（15px 字的六列之和，比例 1/21.2），卦名定向同上 */
.board.six{width:318px;max-width:100%}
.board.six col.c1{width:10.063%}
.board.six col.c2{width:24.371%}
.board.six col.c3{width:24.843%}
.board.six col.c4{width:15.723%}
.board.six col.c5{width:12.579%}
.board.six col.c6{width:12.421%}
.board.six .gmain{padding-left:9.89%}
.board th,.board td{padding:.3em 0;font-weight:400;white-space:nowrap;vertical-align:middle;line-height:1.4}
.board .gname{font-size:1em;font-weight:600;text-align:center;padding-bottom:.7em;letter-spacing:.02em}
.board .gname .tag{font-weight:400}   /* 括注与卦名同大（指令 38），只以字重区分 */
.board .liushen{text-align:right;color:#666}
/* 格内一律单行（指令 59 绝对兜底）：任何格永不折成两行 */
.board th,.board td{white-space:nowrap}
.board .fush{text-align:right;color:#6b6b6b}
.board .qin{text-align:right}
/* 爻线（指令 55 重合 bug 的根治）：▁ 字符保留在 DOM 里（复制进 Word 仍是
   阴阳爻字符），但墨迹设为透明——手机端 ▁ 字体回退后墨迹顶满字身框、上移后
   横穿前后文字，字符方案跨端不可控；可见线改由 CSS 绘制：宽恒 3em（与字符
   等宽）、垂直居中于行（指令 37）、两端必留格内余白，任何设备均不会与
   六亲／世应接触。断线两段各 0.7em、中缝 0.6em，与「▁　▁」同构 */
.board .yao{text-align:center;letter-spacing:0;position:relative;color:transparent}
.board .yao::before,.board .yao::after{content:"";position:absolute;top:50%;
  height:.075em;transform:translateY(-50%);background:#1a1a1a;border-radius:1px}
/* 线长 2em（两端各内缩 0.5em），与六亲／世应留出明确间隙（指令 57）；断线两段各 0.7em、中缝 0.6em */
/* 宽幅爻线 2.8em（指令 71「放大时爻位要加长」）：爻列实测 3.333em，两侧各余 0.267em */
.board .yao.y1::before{left:calc(50% - 1.4em);width:2.8em}
.board .yao.y0::before{left:calc(50% - 1.4em);width:.95em}
.board .yao.y0::after{right:calc(50% - 1.4em);width:.95em}
.board .sy{text-align:left;font-weight:600;padding-left:.55em}
/* 动爻标记贴右（指令 70）：九列时本卦与变卦之间的中段空白被压到最小；
   动爻列不参与卦名居中基准（居中只算六亲纳甲｜爻｜世应），此改动不扰居中。
   静卦六列仍左对齐（标记紧随世应） */
.board:not(.six) .dong{text-align:right;padding-left:0;padding-right:.25em}
.board .dong{text-align:left;color:#9c3a2e;padding-left:.25em}
.note{margin:.9em 0 0;color:#6b6b6b;font-size:.92em}

/* 页脚：居中三行——logo／署名／公众号·微信·官网（指令 36，照道长参考图） */
.brand{margin-top:2.4em;padding-top:1.1em;border-top:1px solid #e8e8e8;
  display:flex;flex-direction:column;align-items:center;gap:.55em;
  color:#6b6b6b;font-size:.76em;line-height:1.62;text-align:center}
.brand .logo{flex:0 0 auto;display:block;line-height:0;text-decoration:none;border:0}
.brand .logo img{display:block;height:clamp(21px,4vw,28px);width:auto;border:0}
.brand .logo:hover{opacity:.82}
.brand .seal{flex:0 0 auto;display:inline-block;border:1.5px solid #9c3a2e;color:#9c3a2e;
  border-radius:2px;font-size:.94em;line-height:1.12;text-decoration:none;letter-spacing:.04em;
  writing-mode:vertical-rl;text-align:center;padding:.22em .16em}
.brand p{margin:0}
.brand .sign{color:#333;letter-spacing:.06em}
.brand .fmeta{display:flex;flex-wrap:wrap;justify-content:center;align-items:baseline;max-width:100%}
/* 桌面端页脚信息行「单行居中」（指令 82）：不换行约需 624px、栏宽 612px，故略缩字号 .95em 收纳；
   窄屏（容器 <600px）仍允许换行，否则字会小到不可读 */
@container (min-width:600px){.brand .fmeta{flex-wrap:nowrap;font-size:.95em}}
.brand .sep{padding:0 .6em;color:#c4c4c4}
.brand a{color:#6b6b6b;text-decoration:none;border-bottom:1px solid #d8d8d8}
.brand .logo{border-bottom:0}
.brand a:hover{color:#9c3a2e;border-color:#9c3a2e}

@media (max-width:620px){
  /* 窄屏兜底（版面规则已容器化，见 @container）：仅剩基准字与面板留白 */
  body{font-size:clamp(9px,calc((100vw - 26px)/32),15px)}
  .pan{padding:20px 13px 18px}
}
@container (max-width:640px){
  /* 窄屏不折行：整表按可用宽度等比缩字，列宽比例同步收窄 */
  .board{width:100%}
  /* 窄屏列宽比例不变：盘面字体已与表宽耦合（1/36.667、静卦 1/21.2），居中恒成立 */
  .board th,.board td{padding:.3em 0}
  .top{--logoh:32px;gap:10px;padding-bottom:10px;margin-bottom:14px}
  .top h1{font-size:1.16em;letter-spacing:.1em}
  .top .tsub{font-size:.7em;letter-spacing:.03em}
  .panel{padding:14px 15px 13px}
  .pgroup+.pgroup{margin-top:13px}
  .pg-lab{line-height:1.2;font-size:1.02em;letter-spacing:.06em}
  .pg-body{gap:8px 12px;min-height:0}
  .ptext{width:4.6em}
  .ptext.wide{width:auto;flex:1 1 0;min-width:3em}
  .fld-wide{flex:1 1 0;min-width:0}
  /* 窄幅爻线维持 2em（间隙优先，指令 57） */
  .board .yao.y1::before{left:calc(50% - 1em);width:2em}
  .board .yao.y0::before{left:calc(50% - 1em);width:.7em}
  .board .yao.y0::after{right:calc(50% - 1em);width:.7em}
  .time-grid{gap:2px;font-size:.94em}   /* 组名同行后更紧：时间组整体微缩 */
  .time-grid .date{gap:1px}
  .time-grid .pbtn{padding:0 5px}
  .dsel .psel{padding-left:3px;padding-right:12px}
  .dsel::after{right:6px;border-width:3px}
  .time-grid .pbtn{padding:0 7px}
  .yao-grid{gap:8px 8px}
  .yao-cell{gap:4px}
  .yao-cell>span{flex:0 0 2.2em;font-size:.88em;white-space:nowrap}
  .yao-cell .dsel .psel{padding-left:4px;padding-right:14px}
  .brand{gap:.45em}
  .top .fold,.copybtn{padding:0 8px;font-size:.78em}   /* 复制卦例钮与页头钮同步收窄（指令 83） */
}

@container (max-width:345px){
  /* 345 以下：组名同行（指令 48）后更紧——组名列收窄、面板内距收窄、时间组再降字 */
  .panel{padding:12px 6px 11px}
  .pgroup{grid-template-columns:auto minmax(0,1fr);column-gap:8px}
  .dsel .psel{padding-left:2px;padding-right:8px;font-size:.72em}
  .dsel::after{right:3px;border-width:2.5px}
  .time-grid{gap:1px}
  .time-grid .date{gap:1px}
  .time-grid .pbtn{padding:0 3px;font-size:.72em}
}
@container (max-width:400px){
  /* 400 以下：六爻仍须三列两行，故再收标签宽与下拉内距 */
  .yao-grid{gap:8px 4px}
  .yao-cell{gap:2px}
  .yao-cell>span{flex:0 0 1.9em;font-size:.78em}
  .yao-cell .dsel .psel{padding-left:3px;padding-right:11px;font-size:.82em}
  .yao-cell .dsel::after{right:4px;border-width:2.5px}
}

  /* 400 以下：六爻仍须三列两行，故再收标签宽与下拉内距 */
  .yao-grid{gap:8px 4px}
  .yao-cell{gap:2px}
  .yao-cell>span{flex:0 0 1.9em;font-size:.78em}
  .yao-cell .dsel .psel{padding-left:3px;padding-right:11px;font-size:.82em}
  .yao-cell .dsel::after{right:4px;border-width:2.5px}
}
@container (max-width:360px){
  /* 320 级极窄屏：时间组仍须一行，故再收字号与箭头位 */
  .dsel .psel{padding-left:4px;padding-right:14px;font-size:.9em}
  .dsel::after{right:5px;border-width:2.5px}
  .time-grid .pbtn{padding:0 5px;font-size:.9em}
}

  /* 320 级极窄屏：时间组仍须一行，故再收字号与箭头位 */
  .dsel .psel{padding-left:4px;padding-right:14px;font-size:.9em}
  .dsel::after{right:5px;border-width:2.5px}
  .time-grid .pbtn{padding:0 5px;font-size:.9em}
}
"""

_PANEL = """
<form class="panel" id="panel" autocomplete="off" onsubmit="return false">
  <div class="pgroup">
    <span class="pg-lab">信息</span>
    <div class="pg-body">
      <label class="fld"><span>姓名</span><input class="ptext" id="f-name" type="text" placeholder="可不填"></label>
      <label class="fld"><span>性别</span><select class="psel psel-s" id="f-gender"><option>男</option><option>女</option></select></label>
      <label class="fld fld-wide"><span>所问</span><input class="ptext wide" id="f-q" type="text" placeholder="所问事情填写"></label>
    </div>
  </div>

  <div class="pgroup">
    <span class="pg-lab">方式</span>
    <div class="pg-body pg-mode">
      <label class="pr"><input type="radio" name="mode" value="auto"><span>自动起卦</span></label>
      <label class="pr"><input type="radio" name="mode" value="manual" checked><span>手工指定</span></label>
      <button type="button" class="pbtn" id="f-recast" hidden title="模拟三枚铜钱，一爻一掷">点击起卦</button>
      <span class="vsep"></span>
      <label class="pr"><input type="radio" name="cal" value="solar" checked><span>公历</span></label>
      <label class="pr"><input type="radio" name="cal" value="lunar"><span>农历</span></label>
    </div>
  </div>

  <div class="pgroup">
    <span class="pg-lab">时间</span>
    <div class="pg-body time-grid">
      <span class="date">
        <span class="dsel"><select class="psel ysel-y" id="f-y"></select></span>
        <span class="dsel"><select class="psel ysel-n" id="f-m"></select></span>
        <span class="dsel"><select class="psel ysel-n" id="f-d"></select></span>
        <span class="dsel"><select class="psel ysel-y" id="f-h"></select></span>
        <span class="dsel"><select class="psel ysel-n" id="f-i"></select></span>
      </span>
      <button type="button" class="pbtn" id="f-now">现时</button>
    </div>
  </div>

  <div class="pgroup" id="row-yao">
    <span class="pg-lab">六爻</span>
    <div class="pg-body yao-grid">
      <label class="yao-cell"><span>初爻</span><span class="dsel"><select class="psel ysel" id="y1"></select></span></label>
      <label class="yao-cell"><span>二爻</span><span class="dsel"><select class="psel ysel" id="y2"></select></span></label>
      <label class="yao-cell"><span>三爻</span><span class="dsel"><select class="psel ysel" id="y3"></select></span></label>
      <label class="yao-cell"><span>四爻</span><span class="dsel"><select class="psel ysel" id="y4"></select></span></label>
      <label class="yao-cell"><span>五爻</span><span class="dsel"><select class="psel ysel" id="y5"></select></span></label>
      <label class="yao-cell"><span>上爻</span><span class="dsel"><select class="psel ysel" id="y6"></select></span></label>
    </div>
  </div>
</form>
"""


def _e(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def logo_uri():
    """页脚 logo 以 data URI 内联：仍是单文件、零外链，双击即开不依赖同目录资源。"""
    global _LOGO_URI
    if _LOGO_URI is None:
        try:
            with open(LOGO_FILE, "rb") as f:
                _LOGO_URI = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
        except OSError:
            _LOGO_URI = ""
    return _LOGO_URI


def top_html():
    """页顶：logo（链官网）与「题名＋副标题」整块上下居中，中间一道竖分隔。"""
    uri = logo_uri()
    if uri:
        mark = ('<a class="tlogo" href="%s" target="_blank" rel="noopener" title="魁君堂官网">'
                '<img src="%s" width="%d" height="%d" alt="魁君堂"></a>'
                % (SITE, uri, LOGO_W, LOGO_H))
    else:
        mark = '<span class="tlogo"><span class="tseal">魁君堂</span></span>'
    return ('<header class="top">%s<span class="tsep" aria-hidden="true"></span>'
            '<div class="ttext"><h1>六爻排盘</h1>'
            '<p class="tsub">京房八宫 · 纳甲六亲</p></div>'
            '<button type="button" class="fold" id="f-fold" aria-expanded="true" '
            'aria-controls="panel">收起排卦 ▲</button></header>' % mark)


def brand_html():
    """页脚：居中三行——logo／署名／公众号｜微信｜官网（指令 36，照道长参考图）。"""
    uri = logo_uri()
    if uri:
        mark = ('<a class="logo" href="%s" target="_blank" rel="noopener" title="魁君堂官网">'
                '<img src="%s" width="%d" height="%d" alt="魁君堂"></a>'
                % (SITE, uri, LOGO_W, LOGO_H))
    else:
        mark = ('<a class="seal" href="%s" target="_blank" rel="noopener">魁君堂</a>' % SITE)
    return (
        '<footer class="brand">%s'
        '<p class="sign">%s</p>'
        '<p class="fmeta"><span>%s</span><span class="sep">｜</span><span>%s</span>'
        '<span class="sep">｜</span><span>%s<a href="%s" target="_blank" rel="noopener">%s</a></span></p>'
        '</footer>'
        % (mark, _e(SIGN), _e(GUARD1), _e(GUARD2), _e(SITE_LABEL), SITE, SITE_TEXT)
    )


def _bar(line):
    return BAR_YIN if line["yin"] else BAR_YANG


def _guatitle(ch):
    tags = [t for t in ch["tags"] if t in GUATAGS]
    tag = '<span class="tag">（%s）</span>' % _e("、".join(tags)) if tags else ""
    return "%s宫：%s%s" % (_e(ch["gong"]), _e(ch["name"]), tag)


def _qin_cell(line):
    return '<td class="qin">%s%s%s%s</td>' % (
        _e(line["liuqin"]), _e(line["gan"]), _e(line["zhi"]), _e(line["wx"]))


def _row(line, bline=None):
    f = line.get("fushen")
    cells = [
        '<td class="liushen">%s</td>' % _e(line["liushen"]),
        _qin_cell(f).replace('<td class="qin">', '<td class="fush">') if f else '<td class="fush"></td>',
        _qin_cell(line),
        '<td class="yao %s">%s</td>' % ("y0" if line["yin"] else "y1", _bar(line)),
        '<td class="sy">%s</td>' % ("世" if line["shi"] else ("应" if line["ying"] else "")),
        '<td class="dong">%s</td>' % (("%s→" % ("○" if not line["yin"] else "×")) if line["moving"] else ""),
    ]
    if bline is not None:
        cells += [
            _qin_cell(bline),
            '<td class="yao %s">%s</td>' % ("y0" if bline["yin"] else "y1", _bar(bline)),
            '<td class="sy">%s</td>' % ("世" if bline["shi"] else ("应" if bline["ying"] else "")),
        ]
    return "<tr>%s</tr>" % "".join(cells)


def head_html(d):
    p, st = d["pillars"], d["input"]
    who = []
    if st.get("name"):
        who.append("姓名：" + _e(st["name"]))
    g = (_e(st["gender"]) + "测") if st.get("gender") else ""
    if g:
        who.append(g + ("：" + _e(st["question"]) if st.get("question") else ""))
    elif st.get("question"):
        who.append(_e(st["question"]))
    # 用「无边框表格」承载信息区：Word 粘贴时表格逐行紧贴、不套段落「段后距」（指令 76/79/81）
    # （段落版——哪怕 <p>＋<br>、inline margin:0——在 Word 里仍被撑开且「改行距无效」；表格与盘面同理最稳）
    rows = []
    if who:
        rows.append('<tr><td><span class="ask">%s</span></td></tr>' % " ".join(who))
    rows.append('<tr><td><span class="meta">公历：%s</span></td></tr>' % _e(st["solar_text"]))
    rows.append('<tr><td><span class="meta">干支：%s年 %s月 %s日 %s时'
                '<span class="kong">　（旬空：%s）</span></span></td></tr>'
                % (_e(p["year"]), _e(p["month"]), _e(p["day"]), _e(p["hour"]), _e("".join(p["kong"]))))
    items = " ".join('<span>%s-%s</span>' % (_e(n), _e("，".join(v))) for n, v in d["shensha"])
    rows.append('<tr><td class="shenrow"><span class="shen"><span class="lab">神煞：</span>%s</span></td></tr>' % items)
    return '<table class="headtbl"><tbody>%s</tbody></table>' % "".join(rows)


_COLS = ('<colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4">'
         '<col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"></colgroup>')
_COLS6 = ('<colgroup><col class="c1"><col class="c2"><col class="c3">'
          '<col class="c4"><col class="c5"><col class="c6"></colgroup>')


def board_html(pri, ch):
    rows = []
    for i in range(5, -1, -1):
        rows.append(_row(pri["lines"][i], ch["lines"][i] if ch else None))
    if ch:
        thead = ('<tr><th colspan="6" class="gname gmain">%s</th>'
                 '<th colspan="3" class="gname gsub">%s</th></tr>' % (_guatitle(pri), _guatitle(ch)))
        cls, cols = "board", _COLS
    else:
        thead = '<tr><th colspan="6" class="gname gmain">%s</th></tr>' % _guatitle(pri)
        cls, cols = "board six", _COLS6
    return ('<table class="%s">%s<thead>%s</thead><tbody>%s</tbody></table>'
            % (cls, cols, thead, "".join(rows)))


def _data_js():
    if not _DATA:
        return ""
    return ("<script>\n"
            "window.__JIE__=%s;\nwindow.__LUNAR__=%s;\nwindow.__DAY0__=%d;\n"
            "window.__GUA__=%s;\nwindow.__SHEN__=%s;\n"
            "</script>" % (json.dumps(tables_js.JIE_JS), json.dumps(tables_js.LUNAR_JS),
                           tables_js.DAY0_JS, tables_js.GUA_JS, tables_js.SHEN_JS))


def _init_js(d):
    st = d["input"]
    init = {
        "name": st.get("name", ""), "gender": st.get("gender") or "男",
        "question": st.get("question", ""),
        "cal": st.get("cal", "solar"),
        "y": st["ymd"][0], "m": st["ymd"][1], "d": st["ymd"][2],
        "h": st["hour"], "i": st["minute"], "leap": bool(st.get("leap")),
        "lateZi": bool(st.get("late_zi", True)),
        "yao": st["yao_values"], "mode": st.get("mode", "manual"),
        "live": bool(st.get("live")),
    }
    return "<script>window.__INIT__=%s;</script>" % json.dumps(init, ensure_ascii=False)


def render_html(d):
    pri, ch = d["primary"], d["changed"]
    title = "魁君堂·六爻排盘"   # 页面标签恒定，不随卦变（指令 46）
    board = board_html(pri, ch)
    note = "" if ch else '\n<p class="note">六爻安静，无变卦。</p>'
    brand = brand_html()
    scripts = _data_js() + _init_js(d) + "<script>" + ENGINE_JS + "</script>" + "<script>" + UI_JS + "</script>"
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>%s</title>
<style>%s</style>
</head>
<body>
<main class="pan%s">
%s
%s
<div class="headwrap"><button type="button" class="fold copybtn" id="f-copy" title="复制卦例（起卦信息＋卦象）到剪贴板">复制卦例</button><div id="pan-head">
%s
</div></div>
<div id="pan-board">
%s%s
</div>
%s
</main>
%s
</body>
</html>
""" % (_e(title), _CSS, " sixpage" if not ch else "", top_html(), _PANEL.strip(),
       head_html(d), board, note, brand, scripts)


def render_md(d):
    p, pri, ch = d["pillars"], d["primary"], d["changed"]
    L = []
    L.append("# 六爻排盘 · %s%s" % (pri["name"], ("之" + ch["name"]) if ch else ""))
    L.append("")
    st = d["input"]
    who = []
    if st.get("name"):
        who.append("姓名：" + st["name"])
    if st.get("gender"):
        who.append("%s测%s" % (st["gender"], ("：" + st["question"]) if st.get("question") else ""))
    elif st.get("question"):
        who.append(st["question"])
    if who:
        L.append("**%s**" % "　".join(who))
        L.append("")
    L.append("公历：%s" % st["solar_text"])
    L.append("")
    L.append("干支：%s年　%s月　%s日　%s时（旬空：%s）"
             % (p["year"], p["month"], p["day"], p["hour"], "".join(p["kong"])))
    L.append("")
    L.append("神煞：%s" % "　".join("%s-%s" % (n, "，".join(v)) for n, v in d["shensha"]))
    L.append("")
    tags = "、".join(t for t in pri["tags"] if t in GUATAGS)
    L.append("## %s宫：%s%s" % (pri["gong"], pri["name"], ("（%s）" % tags) if tags else ""))
    L.append("")
    if ch:
        ctags = "、".join(t for t in ch["tags"] if t in GUATAGS)
        L.append("变卦 · %s宫：%s%s" % (ch["gong"], ch["name"], ("（%s）" % ctags) if ctags else ""))
    else:
        L.append("六爻安静，无变卦。")
    L.append("")
    L.append("| 六神 | 伏神 | 六亲纳甲 | 本卦爻 | 世应 | 动 | 变卦六亲纳甲 | 变爻 | 变世应 |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    blines = list(reversed(ch["lines"])) if ch else [None] * 6
    for line, bl in zip(reversed(pri["lines"]), blines):
        f = line.get("fushen")
        fus = ("%s%s%s%s" % (f["liuqin"], f["gan"], f["zhi"], f["wx"])) if f else ""
        qin = "%s%s%s%s" % (line["liuqin"], line["gan"], line["zhi"], line["wx"])
        sy = "世" if line["shi"] else ("应" if line["ying"] else "")
        dong = ("○→" if not line["yin"] else "×→") if line["moving"] else ""
        if bl:
            bq = "%s%s%s%s" % (bl["liuqin"], bl["gan"], bl["zhi"], bl["wx"])
            bsy = "世" if bl["shi"] else ("应" if bl["ying"] else "")
            byao = _bar(bl)
        else:
            bq = bsy = byao = ""
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                 % (line["liushen"], fus, qin, _bar(line), sy, dong, bq, byao, bsy))
    L.append("")
    L.append("---")
    L.append("")
    L.append(SIGN)
    L.append("")
    L.append("%s%s" % (SITE_LABEL, SITE))
    L.append("")
    L.append(GUARD)
    return "\n".join(L).strip() + "\n"
