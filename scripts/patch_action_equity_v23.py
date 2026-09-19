from pathlib import Path

path = Path('app/src/main/assets/index.html')
s = path.read_text(encoding='utf-8')
marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.3 : équité préflop recalculée après chaque action ---
const KPC_ACTION_EQUITY_V23 = true;
const kpcActionEqCache = new Map();

function kpcActionEqHash(str){
  let h=2166136261>>>0;
  for(let i=0;i<str.length;i++){ h^=str.charCodeAt(i); h=Math.imul(h,16777619); }
  return h>>>0;
}
function kpcActionEqRandom(seed){
  let a=seed>>>0;
  return function(){
    a+=0x6D2B79F5;
    let t=a;
    t=Math.imul(t^t>>>15,t|1);
    t^=t+Math.imul(t^t>>>7,t|61);
    return ((t^t>>>14)>>>0)/4294967296;
  };
}
function kpcDraftAtAction(d,street,i){
  const x=JSON.parse(JSON.stringify(d||{}));
  x.actions=x.actions||{};
  if(street==='Préflop'){
    x.actions['Préflop']=(d.actions?.['Préflop']||[]).slice(0,i+1);
  }
  return x;
}
function kpcHeroVsActionRange(hero,d){
  if(hero.length!==2) return null;
  const pct=kpcTargetPct(d), classes=kpcRangeClasses(pct), blocked=new Set(hero);
  const combos=classes.flatMap(c=>kpcExpandClass(c,blocked));
  if(!combos.length) return null;
  const deck0=allDeck().filter(c=>!blocked.has(c));
  const key=JSON.stringify({hero,pct,bb:d.bb,hs:d.heroStack,vs:d.villainStack,vp:d.villainPos,acts:d.actions?.['Préflop']||[]});
  if(kpcActionEqCache.has(key)) return kpcActionEqCache.get(key);
  const rnd=kpcActionEqRandom(kpcActionEqHash(key));
  let totalWeight=0; combos.forEach(x=>totalWeight+=x[2]);
  let share=0,total=0;
  const samples=2600;
  for(let n=0;n<samples;n++){
    let r=rnd()*totalWeight,pick=combos[combos.length-1];
    for(const x of combos){ r-=x[2]; if(r<=0){ pick=x; break; } }
    const vc=[pick[0],pick[1]];
    const deck=deck0.filter(c=>!vc.includes(c));
    const board=[];
    for(let k=0;k<5;k++){
      const j=k+Math.floor(rnd()*(deck.length-k));
      [deck[k],deck[j]]=[deck[j],deck[k]];
      board.push(deck[k]);
    }
    const hs=evalHoldem(hero.concat(board)),vs=evalHoldem(vc.concat(board));
    const cmp=compareScore(hs,vs);
    total++;
    if(cmp>0) share++;
    else if(cmp===0) share+=.5;
  }
  const out={equity:100*share/total,pct,action:kpcVillainAction(d),eff:kpcStackBB(d)};
  kpcActionEqCache.set(key,out);
  if(kpcActionEqCache.size>180) kpcActionEqCache.clear();
  return out;
}
function kpcActionEquityHTML(street,i){
  if(street!=='Préflop') return '';
  const d=state.handDraft||{}, hero=(d.heroCards||[]).filter(Boolean);
  const actions=d.actions?.['Préflop']||[];
  const a=actions[i];
  if(!a||hero.length!==2) return '';
  const snap=kpcDraftAtAction(d,street,i);
  const r=kpcHeroVsActionRange(hero,snap);
  if(!r) return '';
  const villain=kpcNormPos(d.villainPos||'')||'Vilain';
  const actor=kpcNormPos(a.pos||'')||a.pos||'?';
  const action=String(a.type||'Action');
  const villainActed=(snap.actions?.['Préflop']||[]).some(x=>kpcNormPos(x.pos)===villain);
  const title=villainActed
    ? `Équité maintenant vs range de ${villain}`
    : `Équité après ${actor} ${action}`;
  const detail=villainActed
    ? `${villain} • ${r.action} • range ≈ ${r.pct.toFixed(0)} % • ${r.eff.toFixed(0)} BB eff.`
    : `${villain} • range de position ≈ ${r.pct.toFixed(0)} % • ${r.eff.toFixed(0)} BB eff.`;
  return `<div class="kpc-action-eq">
    <div class="kpc-action-eq-head"><span>${esc(title)}</span><strong>≈ ${r.equity.toFixed(1)} %</strong></div>
    <div class="muted small">${esc(detail)}</div>
  </div>`;
}

const kpcV23BaseActionRow=actionRow;
actionRow=function(street,a,i){
  return kpcV23BaseActionRow(street,a,i)+kpcActionEquityHTML(street,i);
};
window.actionRow=actionRow;

const kpcV23BaseUpdateAct=updateAct;
updateAct=function(street,i,k,v){
  kpcV23BaseUpdateAct(street,i,k,v);
  kpcActionEqCache.clear();
  if(street==='Préflop') rerenderStreet(street);
};
window.updateAct=updateAct;
'''
s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-action-equity-v23">
.kpc-action-eq{margin:-2px 0 10px;padding:9px 11px;border-left:3px solid var(--gold);border-radius:0 10px 10px 0;background:rgba(217,180,74,.08)}
.kpc-action-eq-head{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:.9rem}
.kpc-action-eq-head strong{color:var(--gold);font-size:1rem;white-space:nowrap}
</style>'''
if 'id="kpc-action-equity-v23"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.3 action-by-action preflop equity patch applied')
