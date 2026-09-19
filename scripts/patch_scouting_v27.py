from pathlib import Path

path=Path('app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')

# Carte SCOUTING sur l'accueil, placée après TELLS si présent.
needle='''    <button class="dash-card journal" onclick="navigate('journal')">'''
card='''    <button class="dash-card scouting" onclick="openScouting()">
      <span class="dash-icon">🎯</span><b>SCOUTING</b><small>Profils adverses</small><em>Club. Joueur. Tendances. Tells.</em>
    </button>
'''
if card.strip() not in s:
    if needle not in s:
        raise SystemExit('Scouting dashboard insertion point not found')
    s=s.replace(needle,card+needle,1)

marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.7 : scouting joueurs par club / pseudo ---
const KPC_SCOUTING_V27 = true;
const KPC_SCOUT_KEY='kpc_scout_profiles_v27';
let kpcScoutProfiles=store.get(KPC_SCOUT_KEY,[]);
let kpcScoutFilterClub='';
let kpcScoutSearch='';
let kpcScoutDraftPhoto=null;

const kpcScoutTypes=[
  'Inconnu','Nit','Tight passif','TAG','LAG','Loose passif',
  'Calling station','Maniac','Reg solide','Récréatif','Tricky / créatif'
];

const kpcScoutTags=[
  'Open tight','Open large','3-bet fréquent','3-bet polarisé','Limp fréquent',
  'Défend beaucoup BB','Overfold BB','Shove large','Push/fold solide',
  'C-bet fréquent','2-barrel fréquent','Check-raise','Donk bet',
  'Hero call','Overfold postflop','Trap / slowplay','Bluff fréquent',
  'Value thin','Sizing tell','ICM prudent','ICM agressif',
  'Tilt visible','Très patient','Imprévisible'
];

const kpcTellCats=['Timing','Posture','Jetons','Respiration / voix','Regard','Parole','Sizing + comportement','Autre'];

function kpcScoutSaveAll(){ store.set(KPC_SCOUT_KEY,kpcScoutProfiles); }
function kpcScoutUid(){
  const c=window.crypto||window.msCrypto;
  if(c&&typeof c.randomUUID==='function') return c.randomUUID();
  const b=new Uint8Array(16);
  if(c&&typeof c.getRandomValues==='function') c.getRandomValues(b);
  else for(let i=0;i<16;i++) b[i]=Math.floor(Math.random()*256);
  b[6]=(b[6]&15)|64; b[8]=(b[8]&63)|128;
  const h=[...b].map(x=>x.toString(16).padStart(2,'0')).join('');
  return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20);
}
function kpcScoutStars(v){ v=Math.max(0,Math.min(5,+v||0)); return '●'.repeat(v)+'○'.repeat(5-v); }
function kpcScoutDate(v){
  if(!v) return '—';
  try{return new Date(v).toLocaleDateString('fr-FR')}catch(e){return v}
}
function kpcScoutFind(id){ return kpcScoutProfiles.find(x=>x.id===id); }

function kpcScoutPhotoDB(){
  return new Promise((resolve,reject)=>{
    const q=indexedDB.open('kpc_scout_media',1);
    q.onupgradeneeded=()=>{ const db=q.result; if(!db.objectStoreNames.contains('photos')) db.createObjectStore('photos',{keyPath:'id'}); };
    q.onsuccess=()=>resolve(q.result); q.onerror=()=>reject(q.error);
  });
}
async function kpcScoutSetPhoto(id,dataUrl){
  if(!dataUrl) return;
  const db=await kpcScoutPhotoDB();
  await new Promise((resolve,reject)=>{
    const tx=db.transaction('photos','readwrite');
    tx.objectStore('photos').put({id,dataUrl});
    tx.oncomplete=resolve; tx.onerror=()=>reject(tx.error);
  });
  db.close();
}
async function kpcScoutGetPhoto(id){
  try{
    const db=await kpcScoutPhotoDB();
    const row=await new Promise((resolve,reject)=>{
      const tx=db.transaction('photos','readonly');
      const r=tx.objectStore('photos').get(id);
      r.onsuccess=()=>resolve(r.result); r.onerror=()=>reject(r.error);
    });
    db.close(); return row?.dataUrl||'';
  }catch(e){ return ''; }
}
async function kpcScoutDeletePhoto(id){
  try{
    const db=await kpcScoutPhotoDB();
    await new Promise((resolve,reject)=>{
      const tx=db.transaction('photos','readwrite');
      tx.objectStore('photos').delete(id);
      tx.oncomplete=resolve; tx.onerror=()=>reject(tx.error);
    });
    db.close();
  }catch(e){}
}
function kpcScoutResizePhoto(file){
  return new Promise((resolve,reject)=>{
    const rd=new FileReader();
    rd.onload=()=>{
      const im=new Image();
      im.onload=()=>{
        const max=420, scale=Math.min(1,max/Math.max(im.width,im.height));
        const w=Math.max(1,Math.round(im.width*scale)), h=Math.max(1,Math.round(im.height*scale));
        const cv=document.createElement('canvas'); cv.width=w; cv.height=h;
        cv.getContext('2d').drawImage(im,0,0,w,h);
        resolve(cv.toDataURL('image/jpeg',0.76));
      };
      im.onerror=reject; im.src=rd.result;
    };
    rd.onerror=reject; rd.readAsDataURL(file);
  });
}
async function kpcScoutPhotoChanged(ev){
  const f=ev.target.files?.[0]; if(!f) return;
  try{
    kpcScoutDraftPhoto=await kpcScoutResizePhoto(f);
    const p=$('#sc_photo_preview'); if(p) p.src=kpcScoutDraftPhoto;
  }catch(e){ alert('Impossible de lire cette photo.'); }
}
window.kpcScoutPhotoChanged=kpcScoutPhotoChanged;

function kpcScoutProfileSummary(p){
  const bits=[];
  if(p.type&&p.type!=='Inconnu') bits.push(p.type);
  if(p.tags?.length) bits.push(...p.tags.slice(0,2));
  return bits.join(' • ')||'Profil à compléter';
}
function kpcScoutAvatarHTML(photo,p,size='normal'){
  const cls='kpc-scout-avatar '+(size==='large'?'large':'');
  if(photo) return '<img class="'+cls+'" src="'+photo+'" alt="">';
  const ch=(p?.pseudo||'?').trim().charAt(0).toUpperCase()||'?';
  return '<div class="'+cls+' fallback">'+esc(ch)+'</div>';
}

async function openScouting(){
  const clubs=[...new Set(kpcScoutProfiles.map(p=>(p.club||'').trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'fr'));
  const filtered=kpcScoutProfiles
    .filter(p=>!kpcScoutFilterClub||p.club===kpcScoutFilterClub)
    .filter(p=>{
      const q=kpcScoutSearch.trim().toLowerCase();
      return !q||[p.pseudo,p.club,p.name,p.type,(p.tags||[]).join(' ')].join(' ').toLowerCase().includes(q);
    })
    .sort((a,b)=>(a.club||'').localeCompare(b.club||'','fr')||(a.pseudo||'').localeCompare(b.pseudo||'','fr'));

  const photoPairs=await Promise.all(filtered.map(async p=>[p.id,await kpcScoutGetPhoto(p.id)]));
  const photos=Object.fromEntries(photoPairs);

  const chips=['<button class="chip '+(!kpcScoutFilterClub?'selected':'')+'" onclick="kpcScoutSetClub(\'\')">Tous</button>']
    .concat(clubs.map(c=>'<button class="chip '+(kpcScoutFilterClub===c?'selected':'')+'" onclick="kpcScoutSetClub('+JSON.stringify(c).replace(/"/g,'&quot;')+')">'+esc(c)+'</button>')).join('');

  const cards=filtered.length?filtered.map(p=>`
    <article class="kpc-scout-card" onclick="openScoutProfile('${p.id}')">
      ${kpcScoutAvatarHTML(photos[p.id],p)}
      <div class="kpc-scout-card-main">
        <div class="kpc-scout-club">${esc(p.club||'Sans club')}</div>
        <b>${esc(p.pseudo||'Sans pseudo')}</b>
        <small>${esc(kpcScoutProfileSummary(p))}</small>
        <div class="kpc-scout-mini">
          <span>AGR ${+p.aggression||3}/5</span><span>LOOSE ${+p.looseness||3}/5</span><span>ICM ${+p.icm||3}/5</span>
        </div>
      </div>
      <span class="kpc-scout-arrow">›</span>
    </article>`).join(''):'<div class="empty">Aucun profil pour ce filtre.</div>';

  openModal(`<div class="modal-head"><div><span class="eyebrow">Compétitions par équipes</span><h2>🎯 Scouting joueurs</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
    <p class="muted">Retrouve les adversaires par club et pseudo avant vos Sit & Go.</p>
    <div class="kpc-scout-top">
      <input id="kpcScoutSearch" placeholder="Rechercher un pseudo, club, profil..." value="${esc(kpcScoutSearch)}" oninput="kpcScoutSearch=this.value;openScouting()">
      <button class="primary" onclick="openScoutEdit()">+ Joueur</button>
    </div>
    <div class="chips kpc-scout-clubchips">${chips}</div>
    <div class="kpc-scout-list">${cards}</div>`);
}
window.openScouting=openScouting;
function kpcScoutSetClub(c){ kpcScoutFilterClub=c; openScouting(); }
window.kpcScoutSetClub=kpcScoutSetClub;

async function openScoutEdit(id=''){
  const old=id?kpcScoutFind(id):null;
  const p=old?JSON.parse(JSON.stringify(old)):{
    id:kpcScoutUid(),club:'',pseudo:'',name:'',type:'Inconnu',
    aggression:3,looseness:3,threebet:3,blindDefense:3,icm:3,pressure:3,
    tags:[],preflop:'',postflop:'',pushfold:'',sizings:'',exploit:'',notes:'',
    encounters:0,lastSeen:'',tells:[],createdAt:new Date().toISOString()
  };
  kpcScoutDraftPhoto=await kpcScoutGetPhoto(p.id);
  const typeOpts=kpcScoutTypes.map(x=>'<option '+(p.type===x?'selected':'')+'>'+esc(x)+'</option>').join('');
  const tags=kpcScoutTags.map(t=>'<button type="button" class="chip '+(p.tags?.includes(t)?'selected':'')+'" data-scout-tag="'+esc(t)+'" onclick="this.classList.toggle(\'selected\')">'+esc(t)+'</button>').join('');
  const initial=(p.pseudo||'?').trim().charAt(0).toUpperCase()||'?';
  const ph='data:image/svg+xml;charset=UTF-8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220"><rect width="100%" height="100%" fill="#0d2b49"/><text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle" font-size="92" font-family="Arial" fill="#e5b84d">'+initial+'</text></svg>');
  const preview=kpcScoutDraftPhoto||ph;

  openModal(`<div class="modal-head"><div><span class="eyebrow">${old?'Modifier le profil':'Nouveau profil'}</span><h2>🎯 ${esc(p.pseudo||'Joueur')}</h2></div><button class="icon-btn" onclick="openScouting()">✕</button></div>
    <div class="kpc-scout-edit-head">
      <div class="kpc-scout-photo-pick"><img id="sc_photo_preview" class="kpc-scout-avatar large" src="${preview}" alt="Photo du joueur"><input id="sc_photo" type="file" accept="image/*" onchange="kpcScoutPhotoChanged(event)"><button type="button" class="secondary tiny" onclick="document.getElementById('sc_photo').click()">📷 Choisir / changer</button></div>
      <div class="kpc-scout-idfields">
        <label>Club / équipe<input id="sc_club" value="${esc(p.club)}" placeholder="Ex. CAC Poker"></label>
        <label>Pseudo<input id="sc_pseudo" value="${esc(p.pseudo)}" placeholder="Pseudo du joueur"></label>
        <label>Nom / prénom <span class="muted small">(facultatif)</span><input id="sc_name" value="${esc(p.name||'')}"></label>
      </div>
    </div>

    <label>Profil principal<select id="sc_type">${typeOpts}</select></label>

    <h3>Tendances générales</h3>
    <div class="kpc-scout-sliders">
      ${kpcScoutSlider('aggression','Agressivité',p.aggression,'passif','agressif')}
      ${kpcScoutSlider('looseness','Largeur de range',p.looseness,'tight','loose')}
      ${kpcScoutSlider('threebet','Fréquence 3-bet',p.threebet,'rare','fréquente')}
      ${kpcScoutSlider('blindDefense','Défense de blindes',p.blindDefense,'fold beaucoup','défend beaucoup')}
      ${kpcScoutSlider('icm','Discipline ICM',p.icm,'faible','forte')}
      ${kpcScoutSlider('pressure','Réaction à la pression',p.pressure,'résiste','se dérègle')}
    </div>

    <h3>Étiquettes rapides</h3><div class="chips" id="sc_tags">${tags}</div>

    <h3>Notes techniques</h3>
    <label>Préflop<textarea id="sc_preflop" placeholder="Open, limp, 3-bet, défense BB...">${esc(p.preflop||'')}</textarea></label>
    <label>Postflop<textarea id="sc_postflop" placeholder="C-bet, barrel, check-raise, hero call...">${esc(p.postflop||'')}</textarea></label>
    <label>Push / Fold & ICM<textarea id="sc_pushfold" placeholder="Short stack, bulle, pression ICM...">${esc(p.pushfold||'')}</textarea></label>
    <label>Sizings remarquables<textarea id="sc_sizings" placeholder="Tailles récurrentes, sizing tells...">${esc(p.sizings||'')}</textarea></label>
    <label>Plan d'exploitation<textarea id="sc_exploit" placeholder="Comment adapter notre jeu contre lui ?">${esc(p.exploit||'')}</textarea></label>
    <label>Notes libres<textarea id="sc_notes">${esc(p.notes||'')}</textarea></label>

    <div class="grid2">
      <label>Nombre de rencontres<input id="sc_encounters" inputmode="numeric" value="${esc(p.encounters||0)}"></label>
      <label>Dernière rencontre<input id="sc_lastseen" type="date" value="${esc(p.lastSeen||'')}"></label>
    </div>

    <div class="row">
      <button class="secondary" onclick="openScouting()">Annuler</button>
      <button id="sc_save_btn" class="primary grow" onclick="kpcScoutSaveProfile('${p.id}')">💾 Enregistrer le profil</button>
    </div>`);
}
window.openScoutEdit=openScoutEdit;

function kpcScoutSlider(id,label,value,left,right){
  return `<label class="kpc-scout-slider"><div><b>${esc(label)}</b><span id="sc_${id}_v">${value||3}/5</span></div>
    <input type="range" id="sc_${id}" min="1" max="5" value="${value||3}" oninput="$('#sc_${id}_v').textContent=this.value+'/5'">
    <small><span>${esc(left)}</span><span>${esc(right)}</span></small></label>`;
}

async function kpcScoutSaveProfile(id){
  const club=$('#sc_club')?.value.trim(), pseudo=$('#sc_pseudo')?.value.trim();
  if(!club||!pseudo){ alert('Le club et le pseudo sont nécessaires.'); return; }
  const old=kpcScoutFind(id);
  const p=old?JSON.parse(JSON.stringify(old)):{id,createdAt:new Date().toISOString(),tells:[]};
  Object.assign(p,{
    club,pseudo,name:$('#sc_name')?.value.trim()||'',type:$('#sc_type')?.value||'Inconnu',
    aggression:+$('#sc_aggression')?.value||3,looseness:+$('#sc_looseness')?.value||3,
    threebet:+$('#sc_threebet')?.value||3,blindDefense:+$('#sc_blindDefense')?.value||3,
    icm:+$('#sc_icm')?.value||3,pressure:+$('#sc_pressure')?.value||3,
    tags:$$('[data-scout-tag].selected').map(x=>x.dataset.scoutTag),
    preflop:$('#sc_preflop')?.value||'',postflop:$('#sc_postflop')?.value||'',
    pushfold:$('#sc_pushfold')?.value||'',sizings:$('#sc_sizings')?.value||'',
    exploit:$('#sc_exploit')?.value||'',notes:$('#sc_notes')?.value||'',
    encounters:+$('#sc_encounters')?.value||0,lastSeen:$('#sc_lastseen')?.value||'',
    updatedAt:new Date().toISOString()
  });
  if(old) kpcScoutProfiles[kpcScoutProfiles.findIndex(x=>x.id===id)]=p;
  else kpcScoutProfiles.push(p);
  kpcScoutSaveAll();
  if(kpcScoutDraftPhoto) await kpcScoutSetPhoto(id,kpcScoutDraftPhoto);
  kpcScoutDraftPhoto=null;
  toast('Profil joueur enregistré ✓');
  openScoutProfile(id);
}
window.kpcScoutSaveProfile=kpcScoutSaveProfile;

async function openScoutProfile(id){
  const p=kpcScoutFind(id); if(!p){ openScouting(); return; }
  const photo=await kpcScoutGetPhoto(id);
  const tags=(p.tags||[]).map(t=>'<span>'+esc(t)+'</span>').join('');
  const tells=(p.tells||[]).length?(p.tells||[]).slice().reverse().map(t=>`
    <article class="kpc-scout-tell">
      <div class="kpc-scout-tell-head"><b>${esc(t.category||'Tell')}</b><span>Confiance ${+t.confidence||1}/5</span></div>
      <p><strong>Observation :</strong> ${esc(t.observation||'')}</p>
      ${t.context?'<p><strong>Contexte :</strong> '+esc(t.context)+'</p>':''}
      ${t.hypothesis?'<p><strong>Hypothèse :</strong> '+esc(t.hypothesis)+'</p>':''}
      <small>${t.confirmed?'✓ Validé / revu au showdown':'À confirmer'} • ${kpcScoutDate(t.at)}${t.createdByName?' • ajouté par '+esc(t.createdByName):''}</small>
    </article>`).join(''):'<div class="empty small">Aucun tell enregistré pour ce joueur.</div>';

  openModal(`<div class="modal-head"><div><span class="eyebrow">${esc(p.club||'Club')}</span><h2>${esc(p.pseudo||'Joueur')}</h2></div><button class="icon-btn" onclick="openScouting()">✕</button></div>
    <div class="kpc-scout-profile-head">
      ${kpcScoutAvatarHTML(photo,p,'large')}
      <div><b class="kpc-scout-type">${esc(p.type||'Inconnu')}</b>${p.name?'<p>'+esc(p.name)+'</p>':''}
      <small>${+p.encounters||0} rencontre(s) • dernière : ${kpcScoutDate(p.lastSeen)}</small>${p.updatedByName?'<small>Dernière mise à jour : '+esc(p.updatedByName)+'</small>':''}</div>
    </div>

    <div class="kpc-scout-gauges">
      ${kpcScoutGauge('Agressivité',p.aggression)}
      ${kpcScoutGauge('Ranges',p.looseness)}
      ${kpcScoutGauge('3-bet',p.threebet)}
      ${kpcScoutGauge('Défense BB',p.blindDefense)}
      ${kpcScoutGauge('ICM',p.icm)}
      ${kpcScoutGauge('Pression',p.pressure)}
    </div>
    ${tags?'<div class="tags kpc-scout-tags">'+tags+'</div>':''}

    ${kpcScoutTextBlock('Préflop',p.preflop)}
    ${kpcScoutTextBlock('Postflop',p.postflop)}
    ${kpcScoutTextBlock('Push / Fold & ICM',p.pushfold)}
    ${kpcScoutTextBlock('Sizings remarquables',p.sizings)}
    ${kpcScoutTextBlock('Plan d’exploitation',p.exploit)}
    ${kpcScoutTextBlock('Notes libres',p.notes)}

    <div class="section-head"><h3>👁 Tells observés</h3><button class="tiny" onclick="openScoutTellEdit('${id}')">+ Tell</button></div>
    <div>${tells}</div>

    <div class="row kpc-scout-actions">
      <button class="secondary" onclick="openScoutEdit('${id}')">✎ Modifier</button>
      <button class="secondary" onclick="kpcScoutMarkSeen('${id}')">✓ Rencontré aujourd’hui</button>
      <button class="danger" onclick="kpcScoutDelete('${id}')">Supprimer</button>
    </div>`);
}
window.openScoutProfile=openScoutProfile;

function kpcScoutGauge(label,v){
  const n=Math.max(1,Math.min(5,+v||3));
  return '<div><span>'+esc(label)+'</span><b>'+kpcScoutStars(n)+'</b></div>';
}
function kpcScoutTextBlock(title,text){
  return text?'<div class="toolbox kpc-scout-block"><b>'+esc(title)+'</b><p>'+esc(text).replace(/\n/g,'<br>')+'</p></div>':'';
}

function openScoutTellEdit(id){
  const p=kpcScoutFind(id); if(!p) return;
  const opts=kpcTellCats.map(x=>'<option>'+esc(x)+'</option>').join('');
  openModal(`<div class="modal-head"><div><span class="eyebrow">${esc(p.club)}</span><h2>👁 Nouveau tell • ${esc(p.pseudo)}</h2></div><button class="icon-btn" onclick="openScoutProfile('${id}')">✕</button></div>
    <label>Catégorie<select id="st_cat">${opts}</select></label>
    <label>Ce que j’ai observé<textarea id="st_obs" placeholder="Décris uniquement le comportement observé..."></textarea></label>
    <label>Contexte<textarea id="st_ctx" placeholder="Ex. river, pot important, après un check-raise..."></textarea></label>
    <label>Hypothèse<textarea id="st_hyp" placeholder="Ex. semble associé à une grosse décision ; à confirmer..."></textarea></label>
    <label>Niveau de confiance <input type="range" id="st_conf" min="1" max="5" value="2" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">2/5</span></label>
    <label class="kpc-check"><input type="checkbox" id="st_confirmed"> Observation validée / revue au showdown</label>
    <div class="note"><b>Rappel</b><p>Un tell isolé n’est pas une preuve. Note le fait observé séparément de ton interprétation.</p></div>
    <div class="row"><button class="secondary" onclick="openScoutProfile('${id}')">Annuler</button><button class="primary grow" onclick="kpcScoutSaveTell('${id}')">Enregistrer le tell</button></div>`);
}
window.openScoutTellEdit=openScoutTellEdit;

function kpcScoutSaveTell(id){
  const p=kpcScoutFind(id); if(!p) return;
  const obs=$('#st_obs')?.value.trim();
  if(!obs){ alert('Décris le tell observé.'); return; }
  p.tells=p.tells||[];
  p.tells.push({
    id:kpcScoutUid(),category:$('#st_cat')?.value||'Autre',observation:obs,
    context:$('#st_ctx')?.value||'',hypothesis:$('#st_hyp')?.value||'',
    confidence:+$('#st_conf')?.value||1,confirmed:!!$('#st_confirmed')?.checked,
    at:new Date().toISOString()
  });
  p.updatedAt=new Date().toISOString(); kpcScoutSaveAll(); toast('Tell ajouté ✓'); openScoutProfile(id);
}
window.kpcScoutSaveTell=kpcScoutSaveTell;

function kpcScoutMarkSeen(id){
  const p=kpcScoutFind(id); if(!p) return;
  p.encounters=(+p.encounters||0)+1;
  p.lastSeen=new Date().toISOString().slice(0,10);
  p.updatedAt=new Date().toISOString();
  kpcScoutSaveAll(); toast('Rencontre mise à jour ✓'); openScoutProfile(id);
}
window.kpcScoutMarkSeen=kpcScoutMarkSeen;

async function kpcScoutDelete(id){
  const p=kpcScoutFind(id); if(!p) return;
  if(!confirm('Supprimer définitivement le profil de '+(p.pseudo||'ce joueur')+' ?')) return;
  kpcScoutProfiles=kpcScoutProfiles.filter(x=>x.id!==id); kpcScoutSaveAll(); await kpcScoutDeletePhoto(id);
  toast('Profil supprimé'); openScouting();
}
window.kpcScoutDelete=kpcScoutDelete;
'''

s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-scouting-v27">
.dash-card.scouting{border-color:#efb84a;background:linear-gradient(155deg,#503513,#14180f 72%)}
.kpc-scout-top{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}.kpc-scout-top input{margin:0}
.kpc-scout-clubchips{margin:12px 0;flex-wrap:nowrap;overflow:auto;padding-bottom:4px}.kpc-scout-clubchips .chip{white-space:nowrap}
.kpc-scout-list{display:grid;gap:8px}.kpc-scout-card{display:grid;grid-template-columns:54px 1fr 18px;gap:10px;align-items:center;padding:10px;border:1px solid var(--line);border-radius:14px;background:#091d32;cursor:pointer}
.kpc-scout-avatar{width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid #d8ad3e88;background:#0d2b49}
.kpc-scout-avatar.large{width:88px;height:88px}.kpc-scout-avatar.fallback{display:grid;place-items:center;font-size:22px;font-weight:900;color:var(--gold)}
.kpc-scout-avatar.large.fallback{font-size:34px}.kpc-scout-card-main{min-width:0;display:flex;flex-direction:column}.kpc-scout-card-main>b{font-size:1.05rem}.kpc-scout-card-main small{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpc-scout-club{font-size:.68rem;color:var(--gold);text-transform:uppercase;letter-spacing:.09em}.kpc-scout-arrow{font-size:27px;color:var(--gold)}
.kpc-scout-mini{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}.kpc-scout-mini span{font-size:.62rem;border:1px solid #315875;border-radius:999px;padding:3px 5px;color:#bdd0df}
.kpc-scout-edit-head{display:grid;grid-template-columns:110px 1fr;gap:13px;align-items:start}.kpc-scout-photo-pick{margin:0;text-align:center}.kpc-scout-photo-pick input{display:none}.kpc-scout-photo-pick button{margin-top:7px;width:100%;font-size:.68rem;padding:7px 5px}
.kpc-scout-idfields label{margin-top:0}.kpc-scout-sliders{display:grid;grid-template-columns:1fr 1fr;gap:8px}.kpc-scout-slider{border:1px solid var(--line);border-radius:12px;padding:9px;margin:0;background:#091d32}.kpc-scout-slider>div{display:flex;justify-content:space-between;gap:8px}.kpc-scout-slider input{margin:7px 0 4px}.kpc-scout-slider small{display:flex;justify-content:space-between;color:var(--muted)}
.kpc-scout-profile-head{display:flex;gap:14px;align-items:center;margin:4px 0 15px}.kpc-scout-profile-head p{margin:4px 0}.kpc-scout-profile-head small{color:var(--muted)}.kpc-scout-type{color:var(--gold);font-size:1.05rem}
.kpc-scout-gauges{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:12px}.kpc-scout-gauges>div{display:flex;justify-content:space-between;gap:8px;padding:8px 9px;border-radius:10px;background:#091d32;border:1px solid var(--line)}.kpc-scout-gauges span{font-size:.72rem;color:var(--muted)}.kpc-scout-gauges b{letter-spacing:2px;color:var(--gold);font-size:.72rem}
.kpc-scout-tags{margin:9px 0 13px}.kpc-scout-block{margin:8px 0}.kpc-scout-block p{margin:6px 0 0;line-height:1.45}
.kpc-scout-tell{border:1px solid #345d79;border-left:4px solid #60bfa8;border-radius:12px;padding:10px;margin:8px 0;background:#081a2d}.kpc-scout-tell-head{display:flex;justify-content:space-between;gap:8px}.kpc-scout-tell-head span{font-size:.72rem;color:var(--gold)}.kpc-scout-tell p{font-size:.8rem;line-height:1.42;margin:7px 0}.kpc-scout-tell small{color:var(--muted)}
.kpc-scout-actions{margin-top:14px;flex-wrap:wrap}.kpc-check{display:flex;align-items:center;gap:8px}.kpc-check input{width:auto;margin:0}
@media(max-width:520px){.kpc-scout-edit-head{grid-template-columns:90px 1fr}.kpc-scout-avatar.large{width:76px;height:76px}.kpc-scout-sliders{grid-template-columns:1fr}.kpc-scout-gauges{grid-template-columns:1fr}.kpc-scout-top{grid-template-columns:1fr}.kpc-scout-top .primary{width:100%}}
</style>'''
if 'id="kpc-scouting-v27"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.7 player scouting module applied')
