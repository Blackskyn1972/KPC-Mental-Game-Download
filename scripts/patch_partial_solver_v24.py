from pathlib import Path

path = Path('app/src/main/assets/index.html')
s = path.read_text(encoding='utf-8')
marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.4 : arrêt/enregistrement à tout moment + analyseur de décisions préflop ---
const KPC_PARTIAL_SOLVER_V24 = true;

function kpcV24Num(v){ const n=Number(v); return Number.isFinite(n)?n:0; }
function kpcV24NormType(v){ return String(v||'').toLowerCase().trim(); }
function kpcV24IsAggressive(t){ t=kpcV24NormType(t); return t.includes('raise')||t.includes('3-bet')||t.includes('4-bet')||t.includes('5-bet')||t.includes('all-in')||t==='bet'; }

function kpcV24EndStreet(d){
  const r=d.actions?.River||[], t=d.actions?.Turn||[], f=d.actions?.Flop||[], p=d.actions?.['Préflop']||[];
  if(r.length || d.board?.river) return 'River';
  if(t.length || d.board?.turn) return 'Turn';
  if(f.length || (d.board?.flop||[]).filter(Boolean).length) return 'Flop';
  return p.length?'Préflop':'Contexte';
}
function kpcV24CollectVisible(){
  const d=state.handDraft;
  if(!d) return;
  try{ if(typeof draftFromBase==='function') draftFromBase(); }catch(e){}
  try{ if(typeof saveBoardDraft==='function' && ($('#f1')||$('#turnc')||$('#riverc'))) saveBoardDraft(); }catch(e){}
  if($('#h_result')) d.result=$('#h_result').value;
  if($('#h_potend')) d.potEnd=$('#h_potend').value;
  if($('#h_mental')) d.mental=+$('#h_mental').value;
  if($('#h_note')) d.note=$('#h_note').value;
  if($('#h_status')) d.status=$('#h_status').value;
  const chips=$$('.chip.selected');
  if(chips.length) d.tags=chips.map(x=>x.dataset.tag).filter(Boolean);
}
function kpcV24SaveHand(stopHere=false){
  const d=state.handDraft;
  if(!d){ if(typeof toast==='function') toast('Aucune main en cours'); return; }
  kpcV24CollectVisible();
  d.tags=Array.isArray(d.tags)?d.tags:[];
  d.status=d.status||'À revoir';
  if(stopHere){
    d.endedEarly=true;
    d.endedAtStreet=kpcV24EndStreet(d);
    d.endedAt=new Date().toISOString();
    if(!d.result) d.result='Coup terminé avant showdown';
    const tag='Fin '+d.endedAtStreet;
    if(!d.tags.includes(tag)) d.tags.push(tag);
  }else{
    d.endedEarly=!!d.endedEarly;
  }
  state.hands.unshift(JSON.parse(JSON.stringify(d)));
  store.set('kpc_hands',state.hands);
  try{ if(typeof kpcClearHandDraftSafety==='function') kpcClearHandDraftSafety(); }catch(e){}
  closeModal();
  toast(stopHere?'Main arrêtée et enregistrée ✓':'Main enregistrée ✓');
  renderHome();
  navigate('hands');
  return true;
}
window.saveHand=function(mode){ return kpcV24SaveHand(mode==='partial'); };
saveHand=window.saveHand;

function kpcV24InjectFinishButton(step){
  const host=$('#modal-content');
  if(!host || !state.handDraft || $('#kpc-v24-finish')) return;
  const b=document.createElement('button');
  b.id='kpc-v24-finish';
  b.type='button';
  b.className='secondary full kpc-v24-finish';
  b.innerHTML='⏹ Terminer la main ici et enregistrer';
  b.onclick=()=>saveHand('partial');
  const rows=host.querySelectorAll('.row');
  const anchor=rows.length?rows[rows.length-1]:null;
  if(anchor) host.insertBefore(b,anchor); else host.appendChild(b);
}

function kpcV24HeroClass(cards){
  if(!cards || cards.length!==2) return '';
  const a=cards[0],b=cards[1], av=pokerRankValue(a[0]),bv=pokerRankValue(b[0]);
  if(!av||!bv) return '';
  if(av===bv) return a[0]+b[0];
  const hi=av>bv?a:b, lo=av>bv?b:a;
  return hi[0]+lo[0]+(hi.slice(1)===lo.slice(1)?'s':'o');
}
function kpcV24InTopRange(cards,pct){
  const key=kpcV24HeroClass(cards);
  if(!key) return false;
  return kpcRangeClasses(Math.max(1,Math.min(65,pct))).some(c=>c.key===key);
}
function kpcV24OpeningPct(d){
  const x=JSON.parse(JSON.stringify(d||{}));
  x.villainPos=d.heroPos||'';
  x.villainStack=d.heroStack||d.villainStack||'';
  x.actions=x.actions||{};
  x.actions['Préflop']=[];
  return kpcTargetPct(x);
}
function kpcV24PotBefore(d,i){
  const hero=kpcNormPos(d.heroPos||'');
  const sb=kpcV24Num(d.sb), bb=kpcV24Num(d.bb), ante=kpcV24Num(d.ante);
  const n=Math.max(2,kpcV24Num(d.playersAtTable)||2);
  const contrib={SB:sb,BB:bb};
  let pot=sb+bb+(ante*n), max=Math.max(sb,bb);
  const acts=d.actions?.['Préflop']||[];
  for(let j=0;j<i;j++){
    const a=acts[j],pos=kpcNormPos(a.pos||''),type=kpcV24NormType(a.type),amt=kpcV24Num(a.amount);
    if(!pos || type.includes('fold') || type.includes('check')) continue;
    let target=0;
    if(type.includes('call')) target=amt>0?amt:max;
    else if(kpcV24IsAggressive(type)) target=amt>0?amt:max;
    else continue;
    const prev=contrib[pos]||0;
    if(target<prev && amt>0 && type.includes('call')) target=prev+amt;
    const inc=Math.max(0,target-prev);
    contrib[pos]=prev+inc;
    pot+=inc;
    max=Math.max(max,contrib[pos]);
  }
  return {pot,contrib,max,toCall:Math.max(0,max-(contrib[hero]||0))};
}
function kpcV24BeforeAction(d,i){
  const x=JSON.parse(JSON.stringify(d||{}));
  x.actions=x.actions||{};
  x.actions['Préflop']=(d.actions?.['Préflop']||[]).slice(0,i);
  return x;
}
function kpcV24LastVillainAggression(d,i){
  const vp=kpcNormPos(d.villainPos||'');
  const acts=(d.actions?.['Préflop']||[]).slice(0,i);
  for(let j=acts.length-1;j>=0;j--){
    const a=acts[j];
    if(kpcNormPos(a.pos)===vp && kpcV24IsAggressive(a.type)) return a;
  }
  return null;
}
function kpcV24AggressiveResponsePct(lastAgg,eff){
  const t=kpcV24NormType(lastAgg?.type);
  let pct=t.includes('4-bet')||t.includes('5-bet')?3.5:t.includes('3-bet')?5.5:10;
  if(eff<=15) pct*=1.35;
  if(eff<=8) pct*=1.35;
  return Math.min(22,pct);
}
function kpcV24Verdict(kind,title,detail,extra){
  return {kind,title,detail,extra:extra||''};
}
function kpcV24AnalysePreflop(d,i){
  const acts=d.actions?.['Préflop']||[], a=acts[i];
  if(!a || kpcNormPos(a.pos)!==kpcNormPos(d.heroPos)) return null;
  const hero=(d.heroCards||[]).filter(Boolean);
  if(hero.length!==2) return null;
  const type=kpcV24NormType(a.type), before=kpcV24BeforeAction(d,i), lastAgg=kpcV24LastVillainAggression(d,i);
  const ctx=kpcV24PotBefore(d,i);

  if(!lastAgg){
    const pct=kpcV24OpeningPct(d);
    const inRange=kpcV24InTopRange(hero,pct);
    const nearRange=kpcV24InTopRange(hero,Math.min(65,pct*1.22));
    if(kpcV24IsAggressive(type)){
      if(inRange) return kpcV24Verdict('good','Cohérent avec la range d’ouverture',`Main dans la range de référence ≈ ${pct.toFixed(0)} % depuis ${d.heroPos||'?'}.`,'Modèle cEV de référence.');
      if(nearRange) return kpcV24Verdict('mix','Décision mixte / limite',`Main proche de la frontière d’ouverture ≈ ${pct.toFixed(0)} %.`,'Le stack, les profils et l’ICM peuvent faire varier la décision.');
      return kpcV24Verdict('review','Move à revoir',`Main hors de la range d’ouverture de référence ≈ ${pct.toFixed(0)} %.`,'Une adaptation exploitante reste possible.');
    }
    if(type.includes('fold')){
      if(!inRange) return kpcV24Verdict('good','Fold cohérent',`Main hors de la range d’ouverture de référence ≈ ${pct.toFixed(0)} %.`);
      return kpcV24Verdict('review','Fold à revoir',`La main appartient à la range d’ouverture de référence ≈ ${pct.toFixed(0)} %.`);
    }
    return kpcV24Verdict('mix','Décision à contextualiser','Pas assez d’éléments pour trancher ce move d’ouverture.');
  }

  const r=kpcHeroVsActionRange(hero,before);
  if(!r) return null;
  const needed=ctx.toCall>0?100*ctx.toCall/(ctx.pot+ctx.toCall):0;
  const margin=r.equity-needed;
  const odds=ctx.toCall>0?`Équité ≈ ${r.equity.toFixed(1)} % • seuil pour call ≈ ${needed.toFixed(1)} %`:`Équité ≈ ${r.equity.toFixed(1)} %`;

  if(type.includes('fold')){
    if(ctx.toCall<=0) return kpcV24Verdict('mix','Fold inhabituel sans mise à payer',odds);
    if(margin<-2.5) return kpcV24Verdict('good','Fold cohérent avec les cotes',odds,`Il manque ≈ ${Math.abs(margin).toFixed(1)} points d’équité pour un call direct.`);
    if(margin<=2.5) return kpcV24Verdict('mix','Fold / call proche de la frontière',odds,'Spot potentiellement mixte selon ranges, ICM et profils.');
    return kpcV24Verdict('review','Fold à revoir',odds,`L’équité dépasse le seuil direct d’environ ${margin.toFixed(1)} points.`);
  }
  if(type.includes('call')){
    if(ctx.toCall<=0) return kpcV24Verdict('mix','Call à contextualiser',odds);
    if(margin>2.5) return kpcV24Verdict('good','Call cohérent avec les cotes',odds,`Marge ≈ +${margin.toFixed(1)} points d’équité.`);
    if(margin>=-2.5) return kpcV24Verdict('mix','Call proche de la frontière',odds,'Spot potentiellement mixte selon réalisation d’équité, ICM et profils.');
    return kpcV24Verdict('review','Call à revoir',odds,`Déficit ≈ ${Math.abs(margin).toFixed(1)} points d’équité avant prise en compte de la réalisation.`);
  }
  if(kpcV24IsAggressive(type)){
    const pct=kpcV24AggressiveResponsePct(lastAgg,r.eff);
    const core=kpcV24InTopRange(hero,pct), fringe=kpcV24InTopRange(hero,Math.min(35,pct*1.55));
    if(core) return kpcV24Verdict('good','Relance cohérente avec la range agressive',`Main dans une range agressive de référence ≈ ${pct.toFixed(1)} % • équité ≈ ${r.equity.toFixed(1)} %.`,'Le calcul ne modélise pas encore précisément la fold equity adverse.');
    if(fringe) return kpcV24Verdict('mix','Relance mixte / bluff possible',`Main dans la zone périphérique de la range agressive ≈ ${pct.toFixed(1)} %.`,'Dépend fortement des bloqueurs, sizings et profils.');
    return kpcV24Verdict('review','Relance à revoir',`Main hors de la range agressive de référence ≈ ${pct.toFixed(1)} % • équité ≈ ${r.equity.toFixed(1)} %.`,'Peut rester valable comme adaptation exploitante.');
  }
  return null;
}
function kpcV24SolverCard(street,i,d=state.handDraft){
  if(street!=='Préflop' || !d) return '';
  const x=kpcV24AnalysePreflop(d,i);
  if(!x) return '';
  const icon=x.kind==='good'?'✓':x.kind==='mix'?'≈':'!';
  return `<div class="kpc-v24-solver ${x.kind}">
    <div class="kpc-v24-solver-head"><b>${icon} Analyse du move</b><strong>${esc(x.title)}</strong></div>
    <div class="small">${esc(x.detail)}</div>
    ${x.extra?`<div class="muted small">${esc(x.extra)}</div>`:''}
  </div>`;
}
function kpcV24SavedSolverHTML(d){
  const acts=d.actions?.['Préflop']||[];
  const rows=acts.map((a,i)=>kpcNormPos(a.pos)===kpcNormPos(d.heroPos)?kpcV24SolverCard('Préflop',i,d):'').filter(Boolean);
  if(!rows.length) return '';
  return `<div class="toolbox kpc-v24-review"><b>Analyseur de décisions • préflop</b>
    <p class="muted small">Lecture pédagogique cEV à partir des ranges de référence, de l’équité et des cotes du pot. Ce n’est pas un solveur Nash/ICM complet.</p>
    ${rows.join('')}
  </div>`;
}

const kpcV24BaseActionRow=actionRow;
actionRow=function(street,a,i){
  return kpcV24BaseActionRow(street,a,i)+kpcV24SolverCard(street,i);
};
window.actionRow=actionRow;

const kpcV24BaseEquityHistory=equityHistoryHTML;
equityHistoryHTML=function(d){
  const base=typeof kpcV24BaseEquityHistory==='function'?kpcV24BaseEquityHistory(d):'';
  return base+kpcV24SavedSolverHTML(d);
};
window.equityHistoryHTML=equityHistoryHTML;

const kpcV24BaseRenderHandWizard=window.renderHandWizard;
window.renderHandWizard=function(step){
  const r=kpcV24BaseRenderHandWizard(step);
  setTimeout(()=>kpcV24InjectFinishButton(step),0);
  return r;
};
renderHandWizard=window.renderHandWizard;
'''

s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-partial-solver-v24">
.kpc-v24-finish{margin:12px 0;border-style:dashed!important}
.kpc-v24-solver{margin:-2px 0 12px;padding:10px 11px;border-radius:11px;border:1px solid var(--line);background:#09182b}
.kpc-v24-solver.good{border-left:4px solid #5fbf82}.kpc-v24-solver.mix{border-left:4px solid var(--gold)}.kpc-v24-solver.review{border-left:4px solid #d56a6a}
.kpc-v24-solver-head{display:flex;flex-direction:column;gap:3px;margin-bottom:5px}.kpc-v24-solver-head strong{font-size:.9rem}
.kpc-v24-review{margin-top:12px}
</style>'''
if 'id="kpc-partial-solver-v24"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.4 partial-save and preflop decision analyser patch applied')
