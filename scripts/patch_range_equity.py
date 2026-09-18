from pathlib import Path

path = Path('app/src/main/assets/index.html')
s = path.read_text(encoding='utf-8')

marker = '</script>'
idx = s.rfind(marker)
if idx < 0:
    raise SystemExit('No closing script tag found')

js = r'''

// --- KPC v1.9 : équité Hero vs range théorique de référence ---
// Modèle pédagogique cEV : positions + profondeur effective + action préflop.
// Les fréquences sont des références théoriques, pas une reproduction d'une solution propriétaire.
const KPC_RANGE_V19 = true;

function kpcNormPos(p){
  p=String(p||'').toUpperCase().replace(/\s+/g,'');
  const map={'UTG1':'UTG+1','UTG2':'UTG+2','LOJACK':'LJ','HIJACK':'HJ','CUTOFF':'CO','BUTTON':'BTN','BU':'BTN','SMALLBLIND':'SB','BIGBLIND':'BB'};
  return map[p]||p;
}
function kpcStackBB(d){
  const bb=+(d.bb||$('#h_bb')?.value||0), hs=+(d.heroStack||$('#h_stack')?.value||0), vs=+(d.villainStack||$('#v_stack')?.value||0);
  if(!bb) return 30;
  const vals=[hs,vs].filter(x=>x>0); return vals.length?Math.max(1,Math.min(...vals)/bb):30;
}
function kpcVillainAction(d){
  const vp=kpcNormPos(d.villainPos||$('#v_pos')?.value||'');
  const acts=(d.actions?.['Préflop']||[]).filter(a=>kpcNormPos(a.pos)===vp);
  if(!acts.length) return 'range de position';
  const a=acts[acts.length-1];
  return String(a.type||'range de position');
}
function kpcTargetPct(d){
  const p=kpcNormPos(d.villainPos||$('#v_pos')?.value||'');
  const base={UTG:17,'UTG+1':19,'UTG+2':20,LJ:22,MP:23,HJ:26,CO:33,BTN:46,SB:42,BB:55}[p]||28;
  const eff=kpcStackBB(d), a=kpcVillainAction(d).toLowerCase();
  let pct=base;
  if(a.includes('5-bet')) pct=3.5;
  else if(a.includes('4-bet')) pct=5.5;
  else if(a.includes('3-bet')) pct=Math.min(14,Math.max(7,base*.32));
  else if(a.includes('all-in')) pct=eff<=8?Math.min(38,base*.95):eff<=15?Math.min(30,base*.72):Math.min(18,base*.45);
  else if(a.includes('call')) pct=Math.min(42,Math.max(10,base*.72));
  else if(a.includes('raise')) pct=base;
  if(eff<=8 && !a.includes('3-bet') && !a.includes('4-bet') && !a.includes('5-bet')) pct=Math.min(38,Math.max(12,pct*.82));
  else if(eff<=15) pct=Math.min(44,Math.max(10,pct*.90));
  return Math.max(3,Math.min(65,pct));
}
function kpcClassScore(r1,r2,suited){
  const v=r=>pokerRankValue(r), a=v(r1), b=v(r2), hi=Math.max(a,b), lo=Math.min(a,b);
  if(a===b) return 125 + hi*8;
  let sc=hi*6+lo*2;
  if(suited) sc+=10;
  const gap=hi-lo;
  if(gap===1) sc+=9; else if(gap===2) sc+=5; else if(gap===3) sc+=2; else if(gap>=5) sc-=6;
  if(hi===14) sc+=9; if(hi===13) sc+=5; if(hi>=11&&lo>=10) sc+=8;
  if(lo<=5&&hi<10) sc-=5;
  return sc;
}
function kpcRangeClasses(pct){
  const ranks=['A','K','Q','J','T','9','8','7','6','5','4','3','2'], all=[];
  for(let i=0;i<ranks.length;i++) for(let j=i;j<ranks.length;j++){
    if(i===j) all.push({key:ranks[i]+ranks[j],r1:ranks[i],r2:ranks[j],suited:false,score:kpcClassScore(ranks[i],ranks[j],false),combos:6});
    else {
      all.push({key:ranks[i]+ranks[j]+'s',r1:ranks[i],r2:ranks[j],suited:true,score:kpcClassScore(ranks[i],ranks[j],true),combos:4});
      all.push({key:ranks[i]+ranks[j]+'o',r1:ranks[i],r2:ranks[j],suited:false,score:kpcClassScore(ranks[i],ranks[j],false),combos:12});
    }
  }
  all.sort((a,b)=>b.score-a.score);
  const target=1326*pct/100, out=[]; let n=0;
  for(const c of all){ if(n>=target) break; const w=Math.min(1,(target-n)/c.combos); out.push({...c,weight:w}); n+=c.combos*w; }
  return out;
}
function kpcExpandClass(c,blocked){
  const suits=['♠','♥','♦','♣'], out=[];
  if(c.r1===c.r2){
    for(let i=0;i<4;i++) for(let j=i+1;j<4;j++){ const a=c.r1+suits[i],b=c.r2+suits[j]; if(!blocked.has(a)&&!blocked.has(b)) out.push([a,b,c.weight]); }
  } else if(c.suited){
    for(const su of suits){ const a=c.r1+su,b=c.r2+su; if(!blocked.has(a)&&!blocked.has(b)) out.push([a,b,c.weight]); }
  } else {
    for(const s1 of suits) for(const s2 of suits) if(s1!==s2){ const a=c.r1+s1,b=c.r2+s2; if(!blocked.has(a)&&!blocked.has(b)) out.push([a,b,c.weight]); }
  }
  return out;
}
function kpcWeightedPick(arr){
  let total=0; arr.forEach(x=>total+=x[2]); let r=Math.random()*total;
  for(const x of arr){ r-=x[2]; if(r<=0) return x; } return arr[arr.length-1];
}
function kpcHeroVsRange(hero,board,d){
  if(hero.length!==2) return null;
  const blocked=new Set(hero.concat(board));
  const pct=kpcTargetPct(d), classes=kpcRangeClasses(pct);
  const combos=classes.flatMap(c=>kpcExpandClass(c,blocked));
  if(!combos.length) return null;
  const deck0=allDeck().filter(c=>!blocked.has(c));
  let share=0,tie=0,total=0;
  const tally=(vc,extra)=>{
    const hs=evalHoldem(hero.concat(board,extra)), vs=evalHoldem(vc.concat(board,extra));
    const cmp=compareScore(hs,vs); total++; if(cmp>0) share++; else if(cmp===0){share+=.5;tie++;}
  };
  if(board.length===5){
    combos.forEach(x=>{ const reps=Math.max(1,Math.round(x[2]*10)); for(let k=0;k<reps;k++) tally([x[0],x[1]],[]); });
  } else {
    const samples=board.length>=3?5000:7500;
    for(let n=0;n<samples;n++){
      const pick=kpcWeightedPick(combos), vc=[pick[0],pick[1]];
      const deck=deck0.filter(c=>!vc.includes(c)), missing=5-board.length, extra=[];
      for(let k=0;k<missing;k++){ const j=k+Math.floor(Math.random()*(deck.length-k)); [deck[k],deck[j]]=[deck[j],deck[k]]; extra.push(deck[k]); }
      tally(vc,extra);
    }
  }
  return {equity:100*share/total,tie:100*tie/total,pct,action:kpcVillainAction(d),eff:kpcStackBB(d),combos:combos.length,approx:board.length<5};
}
function kpcRangeLabel(d,r){
  const p=kpcNormPos(d.villainPos||$('#v_pos')?.value||'Vilain')||'Vilain';
  return `${p} • ${r.action} • ${r.eff.toFixed(0)} BB eff. • range ≈ ${r.pct.toFixed(0)} %`;
}
function kpcRangeEquityRow(label,hero,board,d){
  const r=kpcHeroVsRange(hero,board,d); if(!r) return '';
  return `<div class="kpc-range-card"><div class="kpc-range-head"><b>${label} — vs range théorique</b><strong>≈ ${r.equity.toFixed(1)} %</strong></div><div class="muted small">${esc(kpcRangeLabel(d,r))}</div><div class="kpc-range-note">Range théorique de référence cEV, pondérée selon position, profondeur effective et action préflop. ICM non calculé.</div></div>`;
}
function kpcCurrentHero(d){ return [$('#hc1')?.value||d.heroCards?.[0]||'', $('#hc2')?.value||d.heroCards?.[1]||''].filter(Boolean); }
function kpcRangePanelHTML(d,fromSaved=false){
  const hero=fromSaved?(d.heroCards||[]).filter(Boolean):kpcCurrentHero(d); if(hero.length!==2) return '';
  const villain=fromSaved?(d.villainCards||[]).filter(Boolean):[$('#vc1')?.value||d.villainCards?.[0]||'', $('#vc2')?.value||d.villainCards?.[1]||''].filter(Boolean);
  let html='<div class="toolbox kpc-range-box"><b>Équité théorique contre la range adverse</b><p class="muted small">Utilisée quand la main exacte du vilain est inconnue. Si sa main est renseignée, les deux lectures restent visibles.</p>';
  html+=kpcRangeEquityRow('Préflop',hero,[],d);
  const flop=fromSaved?(d.board?.flop||[]).filter(Boolean):['f1','f2','f3'].map(x=>$('#'+x)?.value||'').filter(Boolean);
  const turn=fromSaved?(d.board?.turn||''):($('#turnc')?.value||'');
  const river=fromSaved?(d.board?.river||''):($('#riverc')?.value||'');
  if(flop.length===3) html+=kpcRangeEquityRow('Flop',hero,flop,d);
  if(flop.length===3&&turn) html+=kpcRangeEquityRow('Turn',hero,flop.concat(turn),d);
  if(flop.length===3&&turn&&river) html+=kpcRangeEquityRow('River',hero,flop.concat(turn,river),d);
  if(villain.length===2) html+='<div class="muted small" style="margin-top:8px">✓ Main du vilain connue : compare cette valeur avec l’équité exacte main contre main affichée au-dessus.</div>';
  return html+'</div>';
}

// Remplace l'affichage live sans supprimer le calcul exact déjà présent.
const kpcOldUpdateEquityPanel=window.updateEquityPanel;
window.updateEquityPanel=function(){
  if(typeof kpcOldUpdateEquityPanel==='function') kpcOldUpdateEquityPanel();
  const el=$('#equity-live'); if(!el) return;
  const d=state.handDraft||{}; const extra=kpcRangePanelHTML(d,false);
  if(extra) el.insertAdjacentHTML('beforeend',extra);
};
updateEquityPanel=window.updateEquityPanel;

// Ajoute aussi la lecture range dans la review d'une main sauvegardée.
const kpcOldEquityHistoryHTML=equityHistoryHTML;
equityHistoryHTML=function(d){
  const exact=typeof kpcOldEquityHistoryHTML==='function'?kpcOldEquityHistoryHTML(d):'';
  return exact+kpcRangePanelHTML(d,true);
};
window.equityHistoryHTML=equityHistoryHTML;
'''

s = s[:idx] + js + '\n' + s[idx:]

styles = r'''
<style id="kpc-range-v19">
.kpc-range-box{margin-top:10px}.kpc-range-card{padding:11px 12px;border:1px solid var(--line);border-radius:12px;margin:7px 0;background:#091b31}.kpc-range-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.kpc-range-head strong{color:var(--gold);white-space:nowrap}.kpc-range-note{font-size:.76rem;line-height:1.35;opacity:.68;margin-top:6px}
</style>
'''
if 'id="kpc-range-v19"' not in s:
    s = s.replace('</head>', styles + '</head>')

path.write_text(s, encoding='utf-8')
print('V1.9 theoretical range equity patch applied')
