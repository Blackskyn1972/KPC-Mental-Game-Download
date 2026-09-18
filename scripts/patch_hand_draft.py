from pathlib import Path

path = Path('app/src/main/assets/index.html')
s = path.read_text(encoding='utf-8')
marker='</script>'
idx=s.rfind(marker)
if idx<0: raise SystemExit('No closing script tag')

js=r'''

// --- KPC v2.1 : brouillon de main persistant sans interférer avec la sélection des cartes ---
const KPC_HAND_DRAFT_V21=true;
const KPC_DRAFT_KEY='kpc_hand_draft_v21';
const KPC_DRAFT_HISTORY='kpc_hand_draft_history_v21';
let kpcRestoringDraft=false, kpcDraftTimer=null;

function kpcIsHandField(el){
  if(!el||!el.id) return false;
  return /^(h_|v_|hc|vc|f[123]$|turnc$|riverc$)/.test(el.id) || !!el.closest?.('.hand-form,.hand-editor,#hand-form,#hand-editor');
}
function kpcDraftSnapshot(){
  const fields={};
  document.querySelectorAll('input[id],select[id],textarea[id]').forEach(el=>{
    if(kpcIsHandField(el)) fields[el.id]=(el.type==='checkbox'||el.type==='radio')?el.checked:el.value;
  });
  return {at:Date.now(),fields,handDraft:(typeof state!=='undefined'&&state?.handDraft)?JSON.parse(JSON.stringify(state.handDraft)):null};
}
function kpcDraftMeaningful(x){return x&&Object.values(x.fields||{}).some(v=>v!==''&&v!==false&&v!=null);}
function kpcPushHistory(snap){
  let h=[];try{h=JSON.parse(localStorage.getItem(KPC_DRAFT_HISTORY)||'[]')}catch(e){}
  const sig=JSON.stringify(snap.fields||{}),last=h[0]&&JSON.stringify(h[0].fields||{});
  if(sig!==last){h.unshift(snap);h=h.slice(0,25);localStorage.setItem(KPC_DRAFT_HISTORY,JSON.stringify(h));}
}
function kpcSaveDraft(){
  if(kpcRestoringDraft)return;
  const snap=kpcDraftSnapshot();if(!kpcDraftMeaningful(snap))return;
  kpcPushHistory(snap);localStorage.setItem(KPC_DRAFT_KEY,JSON.stringify(snap));
}
function kpcScheduleDraft(){clearTimeout(kpcDraftTimer);kpcDraftTimer=setTimeout(kpcSaveDraft,180);}

// IMPORTANT v2.1 : on ne restaure jamais automatiquement pendant les clics/rerenders.
// Cela laisse le sélecteur de cartes original fonctionner exactement comme en v1.9.
function kpcRestoreDraft(snap){
  if(!snap)return;kpcRestoringDraft=true;
  if(snap.handDraft&&typeof state!=='undefined')state.handDraft=JSON.parse(JSON.stringify(snap.handDraft));
  Object.entries(snap.fields||{}).forEach(([id,v])=>{const el=document.getElementById(id);if(!el)return;if(el.type==='checkbox'||el.type==='radio')el.checked=!!v;else el.value=v;});
  kpcRestoringDraft=false;
  if(typeof updateEquityPanel==='function')try{updateEquityPanel()}catch(e){}
}
function kpcRestoreSavedDraft(){let d=null;try{d=JSON.parse(localStorage.getItem(KPC_DRAFT_KEY)||'null')}catch(e){};if(d&&kpcDraftMeaningful(d))kpcRestoreDraft(d);}
function kpcUndoDraft(){
  let h=[];try{h=JSON.parse(localStorage.getItem(KPC_DRAFT_HISTORY)||'[]')}catch(e){}
  if(h.length<2){if(typeof toast==='function')toast('Aucune étape précédente');return;}
  h.shift();localStorage.setItem(KPC_DRAFT_HISTORY,JSON.stringify(h));localStorage.setItem(KPC_DRAFT_KEY,JSON.stringify(h[0]));kpcRestoreDraft(h[0]);if(typeof toast==='function')toast('Étape précédente restaurée ✓');
}
window.kpcUndoDraft=kpcUndoDraft;

// Sauvegarde passive seulement : aucun preventDefault, stopPropagation ou interception de clic.
document.addEventListener('input',e=>{if(kpcIsHandField(e.target))kpcScheduleDraft()},true);
document.addEventListener('change',e=>{if(kpcIsHandField(e.target))kpcScheduleDraft()},true);

function kpcEnsureUndoButton(){
  const hasHand=document.querySelector('#h_bb,#h_stack,#h_pos,#hc1');if(!hasHand)return;
  if(document.getElementById('kpc-hand-undo'))return;
  const host=document.querySelector('.modal-head,.hand-form,.hand-editor,#hand-form,#hand-editor');if(!host)return;
  const b=document.createElement('button');b.id='kpc-hand-undo';b.type='button';b.className='secondary kpc-undo';b.textContent='↶ Revenir en arrière';b.onclick=kpcUndoDraft;host.appendChild(b);
}

// Observer limité au bouton : surtout aucune restauration automatique lors d'une mutation DOM.
const kpcObs=new MutationObserver(()=>kpcEnsureUndoButton());
kpcObs.observe(document.body,{childList:true,subtree:true});
setTimeout(()=>{kpcEnsureUndoButton();kpcRestoreSavedDraft()},350);

function kpcClearHandDraftSafety(){localStorage.removeItem(KPC_DRAFT_KEY);localStorage.removeItem(KPC_DRAFT_HISTORY);}
window.kpcClearHandDraftSafety=kpcClearHandDraftSafety;
'''
s=s[:idx]+js+'\n'+s[idx:]
styles=r'''<style id="kpc-hand-v21">.kpc-undo{margin:8px 0 10px;width:auto;min-height:38px}.modal-head .kpc-undo{margin-left:auto;margin-right:8px;white-space:nowrap}</style>'''
if 'id="kpc-hand-v21"' not in s:s=s.replace('</head>',styles+'</head>')
path.write_text(s,encoding='utf-8')
print('V2.1 hand draft patch applied - card picker untouched')
