from pathlib import Path

path=Path('app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')
marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.5 : le bouton "fin du coup" bascule vers l'écran final au lieu d'enregistrer immédiatement ---
const KPC_FINISH_REVIEW_V25 = true;

function kpcV25RestoreFinalFields(){
  const d=state.handDraft||{};
  if($('#h_result') && d.result){
    const values=Array.from($('#h_result').options||[]).map(o=>o.value||o.textContent);
    if(values.includes(d.result)) $('#h_result').value=d.result;
  }
  if($('#h_potend') && d.potEnd!=null) $('#h_potend').value=d.potEnd;
  if($('#h_mental') && d.mental!=null){
    $('#h_mental').value=d.mental;
    const v=$('#h_mental').nextElementSibling;
    if(v) v.textContent=d.mental+'/5';
  }
  if($('#h_note') && d.note!=null) $('#h_note').value=d.note;
  if($('#h_status') && d.status){
    const values=Array.from($('#h_status').options||[]).map(o=>o.value||o.textContent);
    if(values.includes(d.status)) $('#h_status').value=d.status;
  }
  $$('.chip').forEach(ch=>{
    ch.classList.toggle('selected',Array.isArray(d.tags)&&d.tags.includes(ch.dataset.tag));
  });

  const host=$('#modal-content');
  if(host && d.endedEarly && !$('#kpc-v25-ended-note')){
    const note=document.createElement('div');
    note.id='kpc-v25-ended-note';
    note.className='kpc-v25-ended-note';
    note.innerHTML='<b>⏹ Coup terminé au '+esc(d.endedAtStreet||'point choisi')+'</b><div class="muted small">Complète maintenant le résultat, tes notes et ton état mental, puis enregistre la main.</div>';
    const head=host.querySelector('.modal-head');
    if(head) head.insertAdjacentElement('afterend',note);
    else host.prepend(note);
  }
}

function kpcV25GoToFinal(step){
  const d=state.handDraft;
  if(!d){ if(typeof toast==='function') toast('Aucune main en cours'); return; }

  try{
    if(typeof kpcV24CollectVisible==='function') kpcV24CollectVisible();
    else {
      if(step===0 && typeof draftFromBase==='function') draftFromBase();
      if(step===2 && typeof saveBoardDraft==='function') saveBoardDraft();
    }
  }catch(e){ console.warn('KPC v2.5 collecte finale',e); }

  d.tags=Array.isArray(d.tags)?d.tags:[];
  d.endedEarly=true;
  d.endedAtStreet=(typeof kpcV24EndStreet==='function')?kpcV24EndStreet(d):(step===1?'Préflop':'Postflop');
  d.endedAt=new Date().toISOString();

  const acts=d.actions?.[d.endedAtStreet]||[];
  const hero=kpcNormPos(d.heroPos||'');
  const lastHero=[...acts].reverse().find(a=>kpcNormPos(a.pos||'')===hero);
  if(lastHero && String(lastHero.type||'').toLowerCase().includes('fold')){
    d.result='Fold avant showdown';
  }

  const tag='Fin '+d.endedAtStreet;
  if(!d.tags.includes(tag)) d.tags.push(tag);

  renderHandWizard(3);
}

kpcV24InjectFinishButton=function(step){
  const host=$('#modal-content');
  if(!host || !state.handDraft || $('#kpc-v24-finish') || step===3) return;
  if(step!==1 && step!==2) return;

  const b=document.createElement('button');
  b.id='kpc-v24-finish';
  b.type='button';
  b.className='secondary full kpc-v24-finish';
  b.innerHTML='⏭ Fin du coup → notes et enregistrement';
  b.onclick=()=>kpcV25GoToFinal(step);

  const rows=host.querySelectorAll('.row');
  const anchor=rows.length?rows[rows.length-1]:null;
  if(anchor) host.insertBefore(b,anchor);
  else host.appendChild(b);
};
window.kpcV24InjectFinishButton=kpcV24InjectFinishButton;

const kpcV25BaseRenderHandWizard=window.renderHandWizard;
window.renderHandWizard=function(step){
  const r=kpcV25BaseRenderHandWizard(step);
  if(step===3) setTimeout(kpcV25RestoreFinalFields,0);
  return r;
};
renderHandWizard=window.renderHandWizard;
'''

s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-finish-review-v25">
.kpc-v25-ended-note{margin:0 0 14px;padding:10px 12px;border-radius:11px;border-left:4px solid var(--gold);background:rgba(217,180,74,.09)}
</style>'''
if 'id="kpc-finish-review-v25"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.5 finish-to-review patch applied')
