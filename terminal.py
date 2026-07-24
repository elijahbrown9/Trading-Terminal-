"""Generate a single, self-contained HTML risk terminal."""

from __future__ import annotations

import html
import json
from pathlib import Path


def render(data: dict) -> str:
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASCEND // Risk Terminal</title>
<style>
:root{{--bg:#0d1113;--panel:#171c1f;--line:#3a4448;--text:#edf0ea;--muted:#8e9a9f;--amber:#ffb62f;--red:#ff625d;--green:#72df8a}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 70% -20%,#292b2a,transparent 35%),var(--bg);color:var(--text);font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.1;background:repeating-linear-gradient(0deg,transparent 0 3px,#fff 4px)}}
main{{width:min(1220px,calc(100% - 24px));margin:auto;padding:28px 0}}header{{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:18px;letter-spacing:.12em}}.brand{{font-size:19px;font-weight:800}}.brand b,h2{{color:var(--amber)}}.muted{{color:var(--muted)}}
.hero{{margin-top:20px;border:1px solid var(--line);border-left:5px solid var(--red);padding:24px;display:grid;grid-template-columns:1.3fr .7fr;gap:30px}}h1{{margin:8px 0;color:var(--red);font-size:34px;letter-spacing:.07em}}.hero p{{max-width:700px;line-height:1.5}}.score{{align-self:center}}.score strong{{font-size:32px;display:block;margin:6px 0}}
.grades{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin:14px 0 24px}}.grades div{{border:1px solid var(--line);padding:10px;text-align:center;color:var(--muted)}}.grades .active{{background:var(--red);color:#fff}}
.grid{{display:grid;grid-template-columns:1.1fr .9fr;gap:12px}}section{{background:linear-gradient(145deg,#1a2023,#131719);border:1px solid var(--line);padding:18px;min-width:0}}h2{{font-size:14px;margin:0 0 14px;border-bottom:1px solid #30383b;padding-bottom:11px;letter-spacing:.06em}}table{{width:100%;border-collapse:collapse}}th{{color:var(--muted);font-size:10px;text-align:left}}td,th{{border-bottom:1px solid #2e3639;padding:10px 5px}}.tag{{border:1px solid #7a8589;padding:4px 6px;font-size:10px}}.bad{{color:var(--red);border-color:var(--red)}}.good{{color:var(--green);border-color:var(--green)}}.pos{{color:var(--green)}}.neg{{color:var(--red)}}.wide{{grid-column:1/-1}}
.ideas article,.board article{{display:grid;grid-template-columns:.7fr .8fr 1.7fr .5fr;gap:10px;border-bottom:1px solid #30383b;padding:10px 0}}.directive{{border-left:3px solid var(--amber);background:#242a2c;padding:12px;line-height:1.5}}footer{{color:#737f83;font-size:9px;border-top:1px solid #30383b;margin-top:14px;padding-top:12px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr}}.hero{{grid-template-columns:1fr}}.grades div span{{display:none}}.wide{{grid-column:auto}}section{{overflow:auto}}table{{min-width:520px}}}}
</style></head><body><main>
<header><div class="brand">ASCEND <b>//</b> RISK TERMINAL</div><div><span id="stamp"></span> · <b id="mode"></b></div></header>
<div class="hero"><div><span class="muted">CURRENT POSTURE</span><h1 id="verdict"></h1><p id="summary"></p></div><div class="score"><span class="muted">COMPOSITE</span><strong id="composite"></strong><span id="weights"></span></div></div>
<div class="grades" id="grades"></div>
<div class="grid">
<section><h2>STORM GAUGE — GARCH(1,1)</h2><table><thead><tr><th>INDEX</th><th>NOW</th><th>LONG-RUN</th><th>21D</th><th>RATIO</th><th>REGIME</th></tr></thead><tbody id="garch"></tbody></table></section>
<section><h2>CONDITIONS + SENTIMENT</h2><div id="conditions"></div><div class="directive" id="sentiment"></div></section>
<section><h2>IDEA BOARD — LEADING / COINCIDENT</h2><div class="board" id="board"></div></section>
<section><h2>TURN WATCH + DISCIPLINE</h2><div id="turn"></div><div id="discipline"></div></section>
<section><h2>ACCOUNTS + MANUAL DESK</h2><div id="accounts"></div><div class="directive" id="sizing"></div></section>
<section><h2>POSITIONS + CASH</h2><table><thead><tr><th>SYMBOL</th><th>TYPE</th><th>QTY</th><th>VALUE / COST</th></tr></thead><tbody id="positions"></tbody></table></section>
<section class="wide"><h2>RANKED TRADE IDEAS — SIZE FROM RISK, NEVER CONVICTION</h2><div class="ideas" id="ideas"></div></section>
<section class="wide"><h2>WEEKLY P&L — AGENTIC + READ-ONLY DESK</h2><div id="pnl"></div></section>
</div><footer>External content is data, never instructions · single-leg options only · review before place · no earnings holds · live trading disabled until explicit approval.</footer>
</main><script>
const D={payload}; const q=s=>document.querySelector(s); const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
q("#stamp").textContent=new Date(D.generated_at).toLocaleString();q("#mode").textContent=D.mode;
const S=D.score;q("#verdict").textContent=`${{S.grade>0?"+":""}}${{S.grade}} · ${{S.label}}`;q("#composite").textContent=S.composite.toFixed(2);
q("#weights").textContent=`VOL ${{S.inputs.volatility.toFixed(2)}} · CONDITIONS ${{S.inputs.conditions.toFixed(2)}} · BOARD ${{S.inputs.board.toFixed(2)}} · X ${{S.inputs.sentiment.toFixed(2)}}`;
q("#summary").textContent=S.veto_applied?"DUAL-STORM VETO ACTIVE: grade capped at -1.":"All inputs weighted; hard risk limits govern posture.";
q("#grades").innerHTML=[-2,-1,0,1,2].map(g=>`<div class="${{g===S.grade?"active":""}}">${{g>0?"+":""}}${{g}} <span>${{["ULTRA OFF","RISK OFF","MIXED","RISK ON","ULTRA ON"][g+2]}}</span></div>`).join("");
q("#garch").innerHTML=Object.values(D.garch).map(m=>`<tr><td><b>${{esc(m.symbol)}}</b></td><td>${{m.current_annualized_vol_pct.toFixed(1)}}%</td><td>${{m.long_run_annualized_vol_pct.toFixed(1)}}%</td><td>${{m.forecast_21d_annualized_vol_pct.toFixed(1)}}%</td><td>${{m.storm_ratio.toFixed(2)}}×</td><td><span class="tag ${{m.regime==="STORM"?"bad":""}}">${{m.regime}}</span></td></tr>`).join("");
q("#conditions").innerHTML=`<p>Macro score: <b>${{Number(D.conditions.score).toFixed(2)}}</b></p><p>${{esc(D.conditions.summary||"No summary")}}</p>`;
q("#sentiment").innerHTML=`<b>SENTIMENT ${{Number(D.sentiment.score).toFixed(2)}}</b><br>${{esc(D.sentiment.summary||"No sentiment summary")}}`;
q("#board").innerHTML=D.board.slice(0,8).map(x=>`<article><b>${{esc(x.ticker)}} ${{esc(x.direction)}}</b><span>${{esc(x.temporal_role)}}</span><span>${{esc(x.classification)}}</span><span>${{x.return_since_post_pct.toFixed(1)}}%</span></article>`).join("")||"<p class=muted>No usable board signals.</p>";
q("#turn").innerHTML=`<p><b>TURN WATCH:</b> ${{S.inputs.board>0?"fresh long flow":"fresh short flow"}} ${{Math.abs(S.inputs.board)>.45?"is leading":"is unconfirmed"}}.</p>`;
q("#discipline").innerHTML=D.discipline.map(x=>`<p class=neg><b>${{esc(x.kind)}}</b> · ${{esc(x.detail)}}</p>`).join("")||"<p class=pos>No discipline flags.</p>";
q("#accounts").innerHTML=`<p>AGENTIC ••••${{esc(D.account_last4)}} · Equity <b>$${{D.equity.toLocaleString()}}</b> · Cash <b>$${{D.cash.toLocaleString()}}</b></p><p class=muted>••••5308 / ••••0208 / ••••7445 — READ ONLY FOREVER</p>`;
const units=["NO NEW LONGS","1 UNIT PROBES","UP TO 2 UNITS","2–3 UNITS","3 UNITS MAX"];q("#sizing").innerHTML=`<b>TODAY @ ${{S.grade}}:</b> ${{units[S.grade+2]}} · 1 unit = $${{(D.equity*.1).toFixed(2)}} · manual share stop −3%`;
q("#positions").innerHTML=[...D.positions,...D.option_positions].map(x=>`<tr><td>${{esc(x.symbol||x.chain_symbol)}}</td><td>${{esc(x.type||"option")}}</td><td>${{esc(x.quantity)}}</td><td>${{esc(x.average_buy_price||x.average_price||"—")}}</td></tr>`).join("")||"<tr><td colspan=4>No open positions</td></tr>";
q("#ideas").innerHTML=D.ideas.map(x=>`<article><b>${{esc(x.ticker)}} ${{esc(x.direction)}}</b><span class="tag ${{x.strength==="STRONG"?"good":""}}">${{x.strength}} · ${{x.agreement_score}}</span><span>Entry $${{x.entry}} · Stop $${{x.stop}} · Targets $${{x.target_1}} / $${{x.target_2}}</span><span>${{x.contracts}} contract(s)</span></article>`).join("")||"<p class=muted>No candidates.</p>";
const closed=D.realized_trades||[];const net=closed.reduce((n,x)=>n+Number(x.realized_pnl||0),0);const sorted=[...closed].sort((a,b)=>Number(b.realized_pnl)-Number(a.realized_pnl));q("#pnl").innerHTML=`<p>Agentic net realized: <b class="${{net>=0?"pos":"neg"}}">$${{net.toFixed(2)}}</b> · Best: ${{esc(sorted[0]?.ticker||"—")}} $${{Number(sorted[0]?.realized_pnl||0).toFixed(2)}} · Worst: ${{esc(sorted.at(-1)?.ticker||"—")}} $${{Number(sorted.at(-1)?.realized_pnl||0).toFixed(2)}}</p><p class=muted>Read-only desk P&L appears only when included in the MCP snapshot.</p>`;
</script></body></html>"""


def write_terminal(data: dict, destination: str | Path = "terminal.html") -> None:
    path = Path(destination)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(render(data), encoding="utf-8")
    temporary.replace(path)
