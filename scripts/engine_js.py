#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engine_js.py —— 浏览器端排盘引擎（内联进单文件 HTML）。

与 Python 引擎同口径、同输出：parity_check.py 会逐字比对两边生成的 head/board HTML。
数据表来自 tables_js.py（由 build_tables.py 从 gua.py／shensha.py／sxtwl 生成）。
"""

ENGINE_JS = r"""
(function(){
"use strict";
var GAN="甲乙丙丁戊己庚辛壬癸", ZHI="子丑寅卯辰巳午未申酉戌亥";
var Y0=1900;
var D=window.__GUA__, S=window.__SHEN__, JIE=window.__JIE__, LUNAR=window.__LUNAR__, DAY0=window.__DAY0__;
var BITS2={"111":"乾","110":"兑","101":"离","100":"震","011":"巽","010":"坎","001":"艮","000":"坤"};
var SHENG={"木":"火","火":"土","土":"金","金":"水","水":"木"};
var KE={"木":"土","土":"水","水":"火","火":"金","金":"木"};
var BAR_YANG="───", BAR_YIN="─　─", GUATAGS=["六合","六冲","游魂","归魂"];   // 八纯不括，与 render.py 同步

function b36(s){var n=0;for(var i=0;i<s.length;i++){n=n*36+parseInt(s.charAt(i),36);}return n;}
function isLeap(y){return y%4===0&&(y%100!==0||y%400===0);}
var MD=[31,28,31,30,31,30,31,31,30,31,30,31];
function jdn(y,m,d){var a=Math.floor((14-m)/12),yy=y+4800-a,mm=m+12*a-3;
  return d+Math.floor((153*mm+2)/5)+365*yy+Math.floor(yy/4)-Math.floor(yy/100)+Math.floor(yy/400)-32045;}
function fromJdn(n){var a=n+32044,b=Math.floor((4*a+3)/146097),c=a-Math.floor(146097*b/4),
  d=Math.floor((4*c+3)/1461),e=c-Math.floor(1461*d/4),m=Math.floor((5*e+2)/153);
  var day=e-Math.floor((153*m+2)/5)+1, mon=m+3-12*Math.floor(m/10), yr=100*b+d-4800+Math.floor(m/10);
  return [yr,mon,day];}
function doy(y,m,d){var n=d;for(var i=0;i<m-1;i++){n+=MD[i];}if(m>2&&isLeap(y)){n++;}return n;}
function jieMin(y,i){var p=((y-Y0)*12+i)*4;return b36(JIE.substr(p,4));}

/* ---------------- 历法 ---------------- */
function pillars(y,m,d,h,mi,lateZi){
  /* 历法表覆盖 1900–2100（与页面年份下拉、Python 端同期）；越界即报错，
     不许拿空表算出一组像真一样的干支（指令 89） */
  if(!(y>=Y0&&y<=Y0+200)){throw new Error("公元 "+y+" 年超出可排范围（1900–2100）");}
  var di=((jdn(y,m,d)+DAY0)%60+60)%60, day=GAN.charAt(di%10)+ZHI.charAt(di%12);
  if(lateZi&&h>=23){di=(di+1)%60;day=GAN.charAt(di%10)+ZHI.charAt(di%12);}
  var now=(doy(y,m,d)-1)*1440+h*60+mi;
  var yb=y;
  if(now<jieMin(y,1)){yb=y-1;}                      /* 未过立春，属上一年 */
  var yi=((yb-4)%60+60)%60, year=GAN.charAt(yi%10)+ZHI.charAt(yi%12);
  var i=11;                                          /* 早于小寒者，承上年大雪，子月 */
  if(now>=jieMin(y,0)){for(var k=11;k>=0;k--){if(now>=jieMin(y,k)){i=k;break;}}}
  var mz=(i+1)%12;
  var yinGan=((yi%10)%5)*2+2, kk=(mz-2+12)%12, mGan=(yinGan+kk)%10;
  var month=GAN.charAt(mGan)+ZHI.charAt(mz);
  var hz=Math.floor((h+1)/2)%12, hg=(GAN.indexOf(day.charAt(0))*2+hz)%10;
  var hour=GAN.charAt(hg)+ZHI.charAt(hz);
  var head=di-di%10;
  var kong=[ZHI.charAt((head+10)%12),ZHI.charAt((head+11)%12)];
  return {year:year,month:month,day:day,hour:hour,dayIndex:di,kong:kong,
          monthZhi:ZHI.charAt(mz),hourZhi:ZHI.charAt(hz)};
}

/* ---------------- 农历 ---------------- */
function lunarYearRec(ly){var p=(ly-Y0)*8;return LUNAR.substr(p,8);}
function cnyOffset(ly){return b36(lunarYearRec(ly).substr(0,4));}
function lunarSeq(leap){var a=[];for(var m=1;m<=12;m++){a.push({m:m,leap:false});if(leap===m){a.push({m:m,leap:true});}}return a;}
function monthLenAt(rec,i){var mask=b36(rec.substr(5,3));return ((mask>>i)&1)?30:29;}
function lunarLeapOf(ly){return b36(lunarYearRec(ly).substr(4,1));}
/* 该年该月（含闰）实有天数：小月 29、大月 30。指令 89：日下拉须按此收口，
   否则选「三十」会静默跨到下月初一 */
function lunarMonthLen(ly,lm,isLeap){
  var rec=lunarYearRec(ly), seq=lunarSeq(lunarLeapOf(ly)),  i;
  for(i=0;i<seq.length;i++){
    if(seq[i].m===lm&&seq[i].leap===!!isLeap){return monthLenAt(rec,i);}
  }
  return 29;
}
function lunarToSolar(ly,lm,ld,isLeap){
  var rec=lunarYearRec(ly), leap=lunarLeapOf(ly), mask=b36(rec.substr(5,3));
  var seq=lunarSeq(leap), days=cnyOffset(ly), i, hit=-1;
  var want=!!isLeap;
  /* 该年无此闰月时按本月算——不再把十二个月全累加、静默跨到次年 */
  if(want&&leap!==lm){want=false;}
  for(i=0;i<seq.length;i++){if(seq[i].m===lm&&seq[i].leap===want){hit=i;break;}}
  if(hit<0){hit=0;}
  for(i=0;i<hit;i++){days+=((mask>>i)&1)?30:29;}
  var len=((mask>>hit)&1)?30:29;
  /* 越界日一律落到本月底，绝不跨月（Python 端对不存在的日期直接报错） */
  days+=Math.max(0,Math.min(len,ld)-1);
  var j=jdn(1900,1,31)+days, t=fromJdn(j);
  return [t[0],t[1],t[2]];
}
function solarToLunar(y,m,d){
  var base=jdn(1900,1,31), days=jdn(y,m,d)-base, ly=Y0;
  var top=Y0+200;
  while(ly<top&&cnyOffset(ly+1)<=days){ly++;}
  var rec=lunarYearRec(ly), leap=b36(rec.substr(4,1)), seq=lunarSeq(leap);
  var rest=days-cnyOffset(ly), i=0;
  while(i<seq.length&&rest>=monthLenAt(rec,i)){rest-=monthLenAt(rec,i);i++;}
  if(i>=seq.length){i=seq.length-1;}
  return {y:ly,m:seq[i].m,d:rest+1,leap:seq[i].leap,months:seq};
}

/* ---------------- 卦理 ---------------- */
function liuqin(gwx,ywx){
  if(gwx===ywx){return "兄弟";}
  if(SHENG[ywx]===gwx){return "父母";}
  if(SHENG[gwx]===ywx){return "子孙";}
  if(KE[ywx]===gwx){return "官鬼";}
  return "妻财";
}
function liushen0(dayGan){return {"甲":0,"乙":0,"丙":1,"丁":1,"戊":2,"己":3,"庚":4,"辛":4,"壬":5,"癸":5}[dayGan];}
function najiaOf(bits){
  var lo=BITS2[bits.slice(0,3).join("")], up=BITS2[bits.slice(3).join("")], out=[];
  for(var i=0;i<6;i++){var g=(i<3)?lo:up;out.push(D.najia[g][i]);}
  return {najia:out,upper:up,lower:lo};
}
function build(bits,moving,dayGan,gwxOverride){
  var na=najiaOf(bits), name=D.gua64[bits.join("")];
  var gong=null, names;
  for(var g in D.gong){if(D.gong[g].indexOf(name)>=0){gong=g;break;}}
  var gwx=gwxOverride||D.gongWx[gong], idx=D.gong[gong].indexOf(name), shi=D.shi[idx];
  var ying=(shi<=3)?shi+3:shi-3, ls0=liushen0(dayGan), rows=[];
  for(var i=0;i<6;i++){
    var gan=na.najia[i][0], zhi=na.najia[i][1], wx=D.zhiWx[zhi];
    rows.push({pos:i+1,yin:bits[i]===0,moving:!!(moving&&moving[i]),
      liuqin:liuqin(gwx,wx),gan:gan,zhi:zhi,wx:wx,
      liushen:D.liushen[(ls0+i)%6],shi:(i+1)===shi,ying:(i+1)===ying,kong:false});
  }
  var tags=[];
  if(idx===0){tags.push("八纯");}else if(idx===6){tags.push("游魂");}else if(idx===7){tags.push("归魂");}
  if(D.liuhe.indexOf(name)>=0){tags.push("六合");}
  if(D.liuchong.indexOf(name)>=0){tags.push("六冲");}
  return {name:name,upper:na.upper,lower:na.lower,gong:gong,gongWx:D.gongWx[gong],
    shi:shi,ying:ying,tags:tags,lines:rows,bits:bits.slice()};
}
function addFushen(pri){
  var have={},miss=[],i;
  for(i=0;i<6;i++){have[pri.lines[i].liuqin]=1;}
  for(i=0;i<D.liuqinOrder.length;i++){if(!have[D.liuqinOrder[i]]){miss.push(D.liuqinOrder[i]);}}
  if(!miss.length){return;}
  var first=D.gong[pri.gong][0], key=null;
  for(var k in D.gua64){if(D.gua64[k]===first){key=k;break;}}
  var bits=key.split("").map(Number), na=najiaOf(bits), gwx=D.gongWx[pri.gong], used={};
  for(i=0;i<6;i++){
    var gan=na.najia[i][0], zhi=na.najia[i][1], q=liuqin(gwx,D.zhiWx[zhi]);
    if(miss.indexOf(q)>=0&&!used[q]){used[q]=1;
      pri.lines[i].fushen={liuqin:q,gan:gan,zhi:zhi,wx:D.zhiWx[zhi]};}
  }
}
function bian(pri){
  var any=false,i;
  for(i=0;i<6;i++){if(pri.lines[i].moving){any=true;}}
  if(!any){return null;}
  var bits=[];
  for(i=0;i<6;i++){var b=pri.lines[i].yin?0:1;if(pri.lines[i].moving){b=1-b;}bits.push(b);}
  var ch=build(bits,null,"甲",pri.gongWx);
  for(i=0;i<6;i++){ch.lines[i].liushen="";}
  return ch;
}
function markKong(h,kong){
  for(var i=0;i<6;i++){h.lines[i].kong=kong.indexOf(h.lines[i].zhi)>=0;}
}

/* ---------------- 神煞 ---------------- */
function shensha(dg,dz,mz){
  var s=S.sanhe[dz], o={
    "驿马":[s[0]],"桃花":[s[1]],"日禄":[S.lu[dg]],"贵人":S.guiren[dg].slice(),
    "文昌":[S.wenchang[dg]],"羊刃":[S.ren[dg]],"将星":[s[2]],"谋星":[s[3]],
    "劫煞":[s[4]],"灾煞":[s[5]],"华盖":[s[6]],"日德":[S.ride[dg]],
    "天马":[S.tianma[mz]],"天医":[ZHI.charAt((ZHI.indexOf(mz)-1+12)%12)]
  };
  return S.order.map(function(n){return [n,o[n]];});
}

/* ---------------- 渲染（与 Python 逐字一致） ---------------- */
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function bar(l){return l.yin?BAR_YIN:BAR_YANG;}
function guatitle(ch){
  var t=[];for(var i=0;i<ch.tags.length;i++){if(GUATAGS.indexOf(ch.tags[i])>=0){t.push(ch.tags[i]);}}
  return esc(ch.gong)+"宫："+esc(ch.name)+(t.length?'<span class="tag">（'+esc(t.join("、"))+'）</span>':"");
}
function qinCell(l){
  return '<td class="qin">'+esc(l.liuqin)+esc(l.gan)+esc(l.zhi)+esc(l.wx)+"</td>";
}
function rowHTML(l,b){
  var cells=[];
  cells.push('<td class="liushen">'+esc(l.liushen)+"</td>");
  cells.push(l.fushen?('<td class="fush">'+qinCell(l.fushen).replace('<td class="qin">',"").replace("</td>","")+"</td>"):'<td class="fush"></td>');
  cells.push(qinCell(l));
  cells.push('<td class="yao '+(l.yin?"y0":"y1")+'">'+bar(l)+"</td>");
  cells.push('<td class="sy">'+(l.shi?"世":(l.ying?"应":""))+"</td>");
  cells.push('<td class="dong">'+(l.moving?((l.yin?"×":"○")+"→"):"")+"</td>");
  if(b){
    cells.push(qinCell(b));
    cells.push('<td class="yao '+(b.yin?"y0":"y1")+'">'+bar(b)+"</td>");
    cells.push('<td class="sy">'+(b.shi?"世":(b.ying?"应":""))+"</td>");
  }
  return "<tr>"+cells.join("")+"</tr>";
}
function boardHTML(pri,ch){
  var rows=[],i,rev=[];
  for(i=5;i>=0;i--){rev.push(i);}
  var body="";
  for(i=0;i<6;i++){body+=rowHTML(pri.lines[rev[i]], ch?ch.lines[rev[i]]:null);}
  var thead;
  if(ch){
    thead='<tr><th colspan="6" class="gname gmain">'+guatitle(pri)+'</th><th colspan="3" class="gname gsub">'+guatitle(ch)+"</th></tr>";
  }else{
    thead='<tr><th colspan="6" class="gname gmain">'+guatitle(pri)+"</th></tr>";
  }
  var cls=ch?"board":"board six";
  var cols=ch
    ?'<colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4">'
      +'<col class="c5"><col class="c6"><col class="c7"><col class="c8"><col class="c9"></colgroup>'
    :'<colgroup><col class="c1"><col class="c2"><col class="c3">'
      +'<col class="c4"><col class="c5"><col class="c6"></colgroup>';
  return '<table class="'+cls+'">'+cols
    +"<thead>"+thead+"</thead><tbody>"+body+"</tbody></table>";
}
function headHTML(st,p,ss){
  var who=[];
  if(st.name){who.push("姓名："+esc(st.name));}
  var g=st.gender?esc(st.gender)+"测":"";
  if(g){who.push(g+(st.question?("："+esc(st.question)):""));}
  else if(st.question){who.push(esc(st.question));}
  /* 用「无边框表格」承载信息区：Word 粘贴时表格逐行紧贴、不套段落「段后距」（指令 76/79/81） */
  var rows=[];
  if(who.length){rows.push('<tr><td><span class="ask">'+who.join(" ")+'</span></td></tr>');}
  rows.push('<tr><td><span class="meta">公历：'+esc(st.solarText)+'</span></td></tr>');
  rows.push('<tr><td><span class="meta">干支：'+esc(p.year)+"年 "+esc(p.month)+"月 "+esc(p.day)+"日 "+esc(p.hour)+"时"
    +'<span class="kong">　（旬空：'+esc(p.kong.join(""))+"）</span></span></td></tr>");
  var items=ss.map(function(x){return '<span>'+esc(x[0])+"-"+esc(x[1].join("，"))+"</span>";}).join(" ");
  rows.push('<tr><td class="shenrow"><span class="shen"><span class="lab">神煞：</span>'+items+"</span></td></tr>");
  return '<table class="headtbl"><tbody>'+rows.join("")+"</tbody></table>";
}

/* ---------------- 计算总入口 ---------------- */
function computeJava(st){
  var sy=st.y,sm=st.m,sd=st.d;
  try{
    if(st.cal==="lunar"){var t=lunarToSolar(st.y,st.m,st.d,st.leap);sy=t[0];sm=t[1];sd=t[2];}
    var p=pillars(sy,sm,sd,st.h,st.i,st.lateZi!==false);
  }catch(e){
    return {head:'<table class="headtbl"><tbody><tr><td><span class="meta">'+esc(e.message)
              +"</span></td></tr></tbody></table>",
            board:"", solar:"", err:String(e.message)};
  }
  var yao=st.yao;
  var bits=[],mov=[];
  for(var i=0;i<6;i++){bits.push((yao[i]===7||yao[i]===9)?1:0);mov.push(yao[i]===6||yao[i]===9);}
  var pri=build(bits,mov,p.day.charAt(0));
  addFushen(pri);markKong(pri,p.kong);
  var ch=bian(pri);if(ch){markKong(ch,p.kong);}
  var ss=shensha(p.day.charAt(0),p.day.charAt(1),p.monthZhi);
  var solarText=sy+"年"+sm+"月"+sd+"日 "+st.h+"时"+st.i+"分";
  var stt={name:st.name,gender:st.gender,question:st.question,solarText:solarText};
  return {head:headHTML(stt,p,ss),board:boardHTML(pri,ch),
          solar:[sy,sm,sd].map(pad).join("-")+" "+pad(st.h)+":"+pad(st.i),
          pillars:p,primary:pri,changed:ch,shensha:ss};
}
function pad(n){return (n<10?"0":"")+n;}
window.__pani={compute:computeJava,pillars:pillars,solarToLunar:solarToLunar,lunarToSolar:lunarToSolar,
               lunarMonthLen:lunarMonthLen,lunarLeapOf:lunarLeapOf,lunarSeq:lunarSeq};
})();
"""

UI_JS = r"""
(function(){
"use strict";
var ZHI="子丑寅卯辰巳午未申酉戌亥";
var LMN=["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","腊月"];
var YAOOPT=[["无背 老阴",6],["一个背 少阳",7],["两个背 少阴",8],["三个背 老阳",9]];
var $=function(id){return document.getElementById(id);};
function pad(n){return (n<10?"0":"")+n;}

function dName(n){
  var a="初一初二初三初四初五初六初七初八初九初十十一十二十三十四十五十六十七十八十九二十廿一廿二廿三廿四廿五廿六廿七廿八廿九三十";
  return a.substr((n-1)*2,2);
}
function fill(el,items,sel){
  var h="";
  for(var i=0;i<items.length;i++){
    var v=items[i][0], t=items[i][1];
    h+='<option value="'+v+'"'+(String(v)===String(sel)?" selected":"")+">"+t+"</option>";
  }
  el.innerHTML=h;
}
/* 时间组只占一行：单位并入选项文本（2026年 / 11月 / 1日 / 0-子时 / 46分），
   不再另设「年」「月」等字位，窄屏才排得下 */
function years(){var a=[];for(var y=1900;y<=2100;y++){a.push([y,y+"年"]);}return a;}
function monthsSolar(){var a=[];for(var m=1;m<=12;m++){a.push([m,m+"月"]);}return a;}
/* 公历日下拉按该年该月实有天数收口：不再留下「2月30日」这类不存在的日期
   —— 旧版 jdn() 会把它们静默滚到下月初（指令 89） */
function daysSolar(y,m){
  m=+m; if(!(m>=1&&m<=12)){m=1;}
  var leap=(y%4===0&&(y%100!==0||y%400===0)), n=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31][m-1], a=[];
  for(var d=1;d<=n;d++){a.push([d,d+"日"]);}return a;
}
function hours(){var a=[];for(var h=0;h<24;h++){a.push([h,h+"-"+ZHI.charAt(Math.floor((h+1)/2)%12)+"时"]);}return a;}
function minutes(){var a=[];for(var i=0;i<60;i++){a.push([i,i+"分"]);}return a;}
function monthsLunar(y){
  var rec=window.__LUNAR__.substr((y-1900)*8,8), leap=parseInt(rec.charAt(4),36), a=[];
  for(var m=1;m<=12;m++){a.push(["0-"+m,LMN[m-1]]);if(leap===m){a.push(["1-"+m,"闰"+LMN[m-1]]);}}
  return a;
}
/* 农历日下拉按该月实有天数（小月 29、大月 30）收口，闰月另计 */
function daysLunar(y,m,leap){
  var n=window.__pani.lunarMonthLen(y,+m,!!leap), a=[];
  for(var d=1;d<=n;d++){a.push([d,dName(d)]);}return a;
}

var ST={};
function readState(){
  ST.name=$("f-name").value.trim();
  ST.gender=$("f-gender").value;
  ST.question=$("f-q").value.trim();
  var mode=document.querySelector('input[name=mode]:checked').value;
  ST.cal=document.querySelector('input[name=cal]:checked').value;
  ST.mode=mode;
  if(ST.cal==="solar"){ST.y=+$("f-y").value||1900;ST.m=+$("f-m").value||1;ST.d=+$("f-d").value||1;ST.leap=false;}
  else{var mm=String($("f-m").value).split("-");ST.leap=(mm[0]==="1");ST.m=+(mm[1]||mm[0])||1;ST.y=+$("f-y").value||1900;ST.d=+$("f-d").value||1;}
  ST.h=+$("f-h").value;ST.i=+$("f-i").value;
  ST.yao=[+$("y1").value,+$("y2").value,+$("y3").value,+$("y4").value,+$("y5").value,+$("y6").value];
}
/* 掷钱：一枚钱背记 1、字记 0，三枚一爻，累加得 0–3 背。
   0背老阴 6、1背少阳 7、2背少阴 8、3背老阳 9 —— 概率 1/8、3/8、3/8、1/8，
   这是摇卦本身的分布，不是四选一的均匀随机。 */
function flip(){
  if(window.crypto&&crypto.getRandomValues){
    var a=new Uint8Array(1); crypto.getRandomValues(a); return (a[0]>>7)&1;
  }
  return Math.random()<0.5?1:0;
}
function tossLine(){ return [6,7,8,9][flip()+flip()+flip()]; }   /* 一爻：掷三枚 */
function tossAll(){                                              /* 六爻：自初爻至上爻，一爻一爻排 */
  var v=[];
  for(var i=0;i<6;i++){v.push(tossLine());}
  return v;
}
function fitFont(){          /* 字号随宽度收窄（指令 61/64）：以盘面元素**实测宽度**直算，
  内联样式直写——不依赖 cqw/vw/min/calc 任何 CSS 特性，任何内核必然生效；
  宽度取自盘面本身（getBoundingClientRect），内距是多少都无关 */
  var pan=document.querySelector(".pan");if(!pan)return;
  var pb=$("pan-board");if(!pb)return;
  var bw=pb.getBoundingClientRect().width;if(bw<=0)return;
  var bd=pb.querySelector(".board");
  var six=bd?bd.classList.contains("six"):pan.classList.contains("sixpage");
  var f=Math.min(15,bw/(six?21.2:36.667));
  pb.style.fontSize=f.toFixed(3)+"px";
  var ph=$("pan-head");if(ph){ph.style.fontSize=f.toFixed(3)+"px";
    var hw=ph.parentNode;
    if(hw&&hw.className==="headwrap"){hw.style.fontSize=f.toFixed(3)+"px";}}
  var cs=getComputedStyle(pan);
  var w=pan.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
  if(w>0){var g=Math.min(15,Math.max(9,w/32));
    var t=document.querySelector(".top"),p=document.querySelector(".panel"),
        b=document.querySelector(".brand");
    if(t)t.style.fontSize=g.toFixed(3)+"px";
    if(p)p.style.fontSize=g.toFixed(3)+"px";
    if(b)b.style.fontSize=g.toFixed(3)+"px";}
}
function refresh(){
  fitFont();
  if(!window.__pani){return;}
  readState();
  var st={name:ST.name,gender:ST.gender,question:ST.question,cal:ST.cal,
    y:ST.y,m:ST.m,d:ST.d,h:ST.h,i:ST.i,leap:ST.leap,yao:ST.yao,
    lateZi:window.__INIT__.lateZi!==false};
  var r=window.__pani.compute(st);
  $("pan-head").innerHTML=r.head;
  $("pan-board").innerHTML=r.board+(r.board&&!r.changed?'\n<p class="note">六爻安静，无变卦。</p>':'');
  if(!r.board){return;}          /* 越界等异常：只留一行提示，不画空盘 */
  /* 静卦页掷出变卦后盘面变九列：sixpage 类必须同步摘除（指令 69），
     否则 fitFont/CSS 仍按静卦大字比例算，字号停在 15px 上限 */
  var pan=document.querySelector(".pan");
  if(pan){pan.classList.toggle("sixpage",!r.changed);}
  fitFont();   /* 重绘＋切类之后再量：盘宽/列数已变，旧内联字号必须重算（指令 69） */
}
function syncYaoRow(){
  var auto=document.querySelector('input[name=mode]:checked').value==="auto";
  $("row-yao").style.display=auto?"none":"";
  var btn=$("f-recast");
  btn.hidden=!auto;
  btn.textContent=ST.tossed?"重新摇卦":"点击起卦";   /* 未掷 → 点击起卦；掷过 → 重新摇卦 */
}
function syncCal(){
  var cal=document.querySelector('input[name=cal]:checked').value;
  var y=+$("f-y").value;
  if(cal==="lunar"){
    var cur=window.__pani.solarToLunar(y,+$("f-m").value,+$("f-d").value);
    fill($("f-m"),monthsLunar(cur.y),cur.leap?"1-"+cur.m:"0-"+cur.m);
    fill($("f-d"),daysLunar(cur.y,cur.m,cur.leap),cur.d);
  }else{
    /* 农历 → 公历：真把当前农历日换算成公历日再填，而不是把月份重置到 1 月 */
    var v=String($("f-m").value).split("-");
    var s=window.__pani.lunarToSolar(y,+(v[1]||v[0]),+$("f-d").value,v[0]==="1");
    fill($("f-m"),monthsSolar(),s[1]);
    fill($("f-d"),daysSolar(s[0],s[1]),s[2]);
  }
}
/* 换年换月后按该历法实有日月重填下拉（指令 89）：
   公历按大小月／闰年；农历按小月大月，年变则闰月随之来去 */
function syncSolarDate(){
  var y=+$("f-y").value, m=+$("f-m").value, opts=daysSolar(y,m);
  fill($("f-d"),opts,Math.min(+$("f-d").value||1,opts.length));
}
function syncLunarDate(){
  var y=+$("f-y").value, v=String($("f-m").value).split("-");
  var lm=+(v[1]||v[0])||1, lp=(v[0]==="1"), opts=monthsLunar(y), has=false, i;
  for(i=0;i<opts.length;i++){if(String(opts[i][0])===(lp?"1-":"0-")+lm){has=true;break;}}
  if(!has){lp=false;}                       /* 该年无此闰月：落回本月，不硬凑 */
  fill($("f-m"),opts,(lp?"1-":"0-")+lm);
  var d=daysLunar(y,lm,lp);
  fill($("f-d"),d,Math.min(+$("f-d").value||1,d.length));
}
function syncDate(){
  if(document.querySelector('input[name=cal]:checked').value==="lunar"){syncLunarDate();}
  else{
    /* 月下拉若还是农历值（"0-6"），先换回公历项，免得读出 NaN */
    if(!/^\d+$/.test(String($("f-m").value))){fill($("f-m"),monthsSolar(),1);}
    syncSolarDate();
  }
}
function setNow(){
  var d=new Date();
  document.querySelector('input[name=cal][value="solar"]').checked=true;
  fill($("f-y"),years(),d.getFullYear());
  fill($("f-m"),monthsSolar(),d.getMonth()+1);
  fill($("f-d"),daysSolar(d.getFullYear(),d.getMonth()+1),d.getDate());
  fill($("f-h"),hours(),d.getHours());
  fill($("f-i"),minutes(),d.getMinutes());
}
/* 复制卦例（指令 83）：把「起卦信息＋卦象」按富文本一并写入剪贴板——
   与手工选中复制同一路径，贴到 Word／微信都保留版式。
   选区只包 #pan-head…#pan-board；按钮在 .headwrap 内、head 之外，故不会进剪贴板 */
function copyGua(){
  var head=$("pan-head"),board=$("pan-board");
  if(!head||!board){return false;}
  var sel=window.getSelection();
  var r=document.createRange();
  r.setStartBefore(head);r.setEndAfter(board);
  sel.removeAllRanges();sel.addRange(r);
  var ok=false;
  try{ok=document.execCommand("copy");}catch(e){ok=false;}
  sel.removeAllRanges();
  return ok;
}
/* 兜底：富文本路径不可用时写纯文本（信息四行＋盘面），保证按钮仍有反馈 */
function copyPlain(){
  var head=$("pan-head"),board=$("pan-board");
  var t=((head&&head.innerText)||"")+"\n\n"+((board&&board.innerText)||"");
  t=t.replace(/[ \t]+\n/g,"\n").replace(/\n{3,}/g,"\n\n").trim();
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){flashCopy(true);},
      function(){flashCopy(legacyCopy(t));});
    return;
  }
  flashCopy(legacyCopy(t));
}
function legacyCopy(t){
  var ta=document.createElement("textarea");
  ta.value=t;ta.setAttribute("readonly","");
  ta.style.cssText="position:fixed;left:-9999px;top:0";
  document.body.appendChild(ta);ta.select();
  var ok=false;
  try{ok=document.execCommand("copy");}catch(e){ok=false;}
  document.body.removeChild(ta);
  return ok;
}
function flashCopy(ok){
  var b=$("f-copy");if(!b){return;}
  b.textContent=ok?"已复制":"复制失败";
  if(ok){b.classList.add("done");}
  if(flashCopy._t){clearTimeout(flashCopy._t);}
  flashCopy._t=setTimeout(function(){
    b.textContent="复制卦例";b.classList.remove("done");
  },1300);
}
function bind(){
  var ini=window.__INIT__;
  fill($("f-y"),years(),ini.y);
  /* 首屏控件须按起卦时的历法填：农历页若按公历填月，读出来是「7月」而非「0-7／1-7」，
     readState 取不到月序，农历日期会整盘算错（指令 89） */
  if(ini.cal==="lunar"){
    fill($("f-m"),monthsLunar(ini.y),(ini.leap?"1-":"0-")+ini.m);
    fill($("f-d"),daysLunar(ini.y,ini.m,ini.leap),ini.d);
  }else{
    fill($("f-m"),monthsSolar(),ini.m);
    fill($("f-d"),daysSolar(ini.y,ini.m),ini.d);
  }
  fill($("f-h"),hours(),ini.h);
  fill($("f-i"),minutes(),ini.i);
  for(var i=1;i<=6;i++){
    var el=$("y"+i),h="";
    for(var k=0;k<YAOOPT.length;k++){h+='<option value="'+YAOOPT[k][1]+'">'+YAOOPT[k][0]+"</option>";}
    el.innerHTML=h;el.value=String(window.__INIT__.yao[i-1]);
  }
  $("f-name").value=window.__INIT__.name||"";
  $("f-gender").value=window.__INIT__.gender||"男";
  $("f-q").value=window.__INIT__.question||"";
  document.querySelector('input[name=mode][value="'+window.__INIT__.mode+'"]').checked=true;
  document.querySelector('input[name=cal][value="'+window.__INIT__.cal+'"]').checked=true;
  ST.tossed=false;

  var nodes=document.querySelectorAll("#panel input, #panel select");
  for(var n=0;n<nodes.length;n++){
    nodes[n].addEventListener("change",function(e){
      if(e.target.name==="mode"){syncYaoRow();}
      if(e.target.name==="cal"){syncCal();}
      else if(e.target.id==="f-y"||e.target.id==="f-m"){syncDate();}
      refresh();
    });
    nodes[n].addEventListener("input",function(e){
      if(e.target.tagName==="INPUT"&&e.target.type==="text"){refresh();}
    });
  }
  $("f-now").addEventListener("click",function(){setNow();refresh();});
  $("f-fold").addEventListener("click",function(){
    var p=$("panel"),open=!p.hidden;
    p.hidden=open;
    document.querySelector(".pan").classList.toggle("collapsed",open);
    this.setAttribute("aria-expanded",open?"false":"true");
    this.textContent=open?"展开排卦 ▼":"收起排卦 ▲";
  });
  $("f-recast").addEventListener("click",function(){
    var v=tossAll();                              /* 一次摇卦：六爻各掷三枚 */
    for(var i=0;i<6;i++){$("y"+(i+1)).value=String(v[i]);}
    ST.tossed=true;
    this.textContent="重新摇卦";
    refresh();
  });
  var cb=$("f-copy");
  if(cb){
    cb.addEventListener("click",function(){
      if(copyGua()){flashCopy(true);}else{copyPlain();}
    });
  }
  syncYaoRow();
  if(window.__INIT__.live){setNow();}     // 默认态：打开即取真实当前时刻
  refresh();
  window.addEventListener("resize",fitFont);
  if(window.ResizeObserver){new ResizeObserver(fitFont).observe(document.querySelector(".pan"));}
  window.fitFont=fitFont;   /* 供审计脚本在钉宽后手动触发 */
}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",bind);}else{bind();}
})();
"""
