from pathlib import Path

path=Path('app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')
marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.8 : scouting collaboratif Supabase + Realtime ---
const KPC_SCOUT_CLOUD_V28 = true;
const KPC_V28_URL='https://xfutvyvvhlhpeowtgfbq.supabase.co';
const KPC_V28_KEY='__KPC_SUPABASE_PUBLISHABLE_KEY__';
const KPC_V28_SESSION='kpc_v22_session';
const KPC_V28_MIGRATED='kpc_scout_cloud_migrated_v28';
function kpcV28UuidOk(v){ return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(String(v||'')); }

let kpcV28Me=null;
let kpcV28LastSync=0;
let kpcV28SyncPromise=null;
let kpcV28Socket=null;
let kpcV28Heartbeat=null;
let kpcV28RetryTimer=null;
let kpcV28DebounceTimer=null;
let kpcV28CurrentView={type:null,id:null};
let kpcV28RealtimeState='offline';
let kpcV28Ref=1;
let kpcV28ViewToken=0;

function kpcV28SetView(type,id=null){
  kpcV28ViewToken++;
  kpcV28CurrentView={type,id};
  return kpcV28ViewToken;
}
function kpcV28ClearView(){
  kpcV28ViewToken++;
  kpcV28CurrentView={type:null,id:null};
}
function kpcV28ScoutingVisible(){
  const modal=$('#modal'), host=$('#modal-content');
  if(!modal?.classList.contains('open') || !host) return false;
  return !!host.querySelector('.kpc-scout-list,.kpc-scout-profile-head,.kpc-scout-edit-head,#sc_club,#st_obs,#kpc-v28-sync');
}

function kpcV28Session(){
  try{return JSON.parse(localStorage.getItem(KPC_V28_SESSION)||'null')}catch(e){return null}
}
function kpcV28StoreSession(x){
  localStorage.setItem(KPC_V28_SESSION,JSON.stringify(x));
  return x;
}
async function kpcV28RefreshSession(){
  const s=kpcV28Session();
  if(!s?.refresh_token) throw Error('Session expirée. Reconnecte-toi.');
  const r=await fetch(KPC_V28_URL+'/auth/v1/token?grant_type=refresh_token',{
    method:'POST',
    headers:{'apikey':KPC_V28_KEY,'Content-Type':'application/json'},
    body:JSON.stringify({refresh_token:s.refresh_token})
  });
  const d=await r.json().catch(()=>null);
  if(!r.ok) throw Error(d?.msg||d?.message||d?.error_description||'Session expirée.');
  return kpcV28StoreSession(d);
}
async function kpcV28Api(path,o={},retry=true){
  let s=kpcV28Session();
  if(!s?.access_token) throw Error('Connecte-toi à ton compte KPC.');
  const h={'apikey':KPC_V28_KEY,'Content-Type':'application/json',...(o.headers||{}),Authorization:'Bearer '+s.access_token};
  let r=await fetch(KPC_V28_URL+path,{...o,headers:h});
  if(r.status===401 && retry){
    await kpcV28RefreshSession();
    return kpcV28Api(path,o,false);
  }
  let d=null;
  const txt=await r.text();
  if(txt){ try{d=JSON.parse(txt)}catch(e){d=txt} }
  if(!r.ok) throw Error(d?.message||d?.msg||d?.error_description||d?.hint||('Erreur '+r.status));
  return d;
}
async function kpcV28GetMe(force=false){
  if(kpcV28Me&&!force) return kpcV28Me;
  const s=kpcV28Session();
  if(!s?.user?.id) throw Error('Connecte-toi à ton compte KPC.');
  const a=await kpcV28Api('/rest/v1/profiles?select=id,display_name,approved,role&id=eq.'+encodeURIComponent(s.user.id));
  const p=a?.[0];
  if(!p) throw Error('Profil KPC introuvable.');
  if(!p.approved) throw Error('Ton compte KPC doit être validé pour accéder au scouting partagé.');
  kpcV28Me=p;
  return p;
}

function kpcV28ProfileData(p){
  return {
    type:p.type||'Inconnu',
    aggression:+p.aggression||3,
    looseness:+p.looseness||3,
    threebet:+p.threebet||3,
    blindDefense:+p.blindDefense||3,
    icm:+p.icm||3,
    pressure:+p.pressure||3,
    tags:Array.isArray(p.tags)?p.tags:[],
    preflop:p.preflop||'',
    postflop:p.postflop||'',
    pushfold:p.pushfold||'',
    sizings:p.sizings||'',
    exploit:p.exploit||'',
    notes:p.notes||''
  };
}
function kpcV28TellFromRow(t){
  return {
    id:t.id,
    category:t.category||'Autre',
    observation:t.observation||'',
    context:t.context||'',
    hypothesis:t.hypothesis||'',
    confidence:+t.confidence||1,
    confirmed:!!t.confirmed,
    at:t.created_at,
    createdByName:t.created_by_name||'',
    updatedByName:t.updated_by_name||''
  };
}
function kpcV28PlayerFromRow(r,tells){
  return {
    id:r.id,club:r.club||'',pseudo:r.pseudo||'',name:r.name||'',
    ...(r.profile_data||{}),
    encounters:+r.encounters||0,
    lastSeen:r.last_seen||'',
    createdAt:r.created_at,
    updatedAt:r.updated_at,
    createdByName:r.created_by_name||'',
    updatedByName:r.updated_by_name||'',
    tells:(tells||[]).filter(t=>t.player_id===r.id).map(kpcV28TellFromRow)
  };
}
async function kpcV28MigrateLocal(localBefore,remotePlayers,me){
  if(localStorage.getItem(KPC_V28_MIGRATED)==='1') return false;
  if(!Array.isArray(localBefore)||!localBefore.length){
    localStorage.setItem(KPC_V28_MIGRATED,'1'); return false;
  }
  let wrote=false;
  for(const p of localBefore){
    const same=remotePlayers.find(r=>r.id===p.id ||
      ((r.club||'').trim().toLowerCase()===(p.club||'').trim().toLowerCase() &&
       (r.pseudo||'').trim().toLowerCase()===(p.pseudo||'').trim().toLowerCase()));
    if(same) continue;
    try{
      const photo=await kpcScoutGetPhoto(p.id);
      const body={
        id:p.id,club:p.club||'Sans club',pseudo:p.pseudo||'Sans pseudo',name:p.name||null,
        profile_data:kpcV28ProfileData(p),photo_data:photo||null,
        encounters:+p.encounters||0,last_seen:p.lastSeen||null,
        created_by:me.id,created_by_name:me.display_name||'Membre KPC',
        updated_by:me.id,updated_by_name:me.display_name||'Membre KPC',
        created_at:p.createdAt||new Date().toISOString(),updated_at:new Date().toISOString()
      };
      await kpcV28Api('/rest/v1/scouting_players',{method:'POST',headers:{Prefer:'return=minimal'},body:JSON.stringify(body)});
      for(const t of (p.tells||[])){
        await kpcV28Api('/rest/v1/scouting_tells',{method:'POST',headers:{Prefer:'return=minimal'},body:JSON.stringify({
          id:t.id||kpcScoutUid(),player_id:p.id,category:t.category||'Autre',
          observation:t.observation||'Observation importée',context:t.context||'',hypothesis:t.hypothesis||'',
          confidence:+t.confidence||2,confirmed:!!t.confirmed,
          created_by:me.id,created_by_name:t.createdByName||me.display_name||'Membre KPC',
          updated_by:me.id,updated_by_name:me.display_name||'Membre KPC',
          created_at:t.at||new Date().toISOString(),updated_at:new Date().toISOString()
        })});
      }
      wrote=true;
    }catch(e){ console.warn('Migration scouting local:',e.message); }
  }
  localStorage.setItem(KPC_V28_MIGRATED,'1');
  return wrote;
}

async function kpcV28LoadAll({migrate=true,render=false,silent=false}={}){
  if(kpcV28SyncPromise) return kpcV28SyncPromise;
  kpcV28SyncPromise=(async()=>{
    try{
      kpcV28SetState('syncing');
      const me=await kpcV28GetMe();
      const localBefore=Array.isArray(kpcScoutProfiles)?JSON.parse(JSON.stringify(kpcScoutProfiles)):[];
      let players=await kpcV28Api('/rest/v1/scouting_players?select=*&order=club.asc,pseudo.asc');
      if(migrate && await kpcV28MigrateLocal(localBefore,players,me)){
        players=await kpcV28Api('/rest/v1/scouting_players?select=*&order=club.asc,pseudo.asc');
      }
      const tells=await kpcV28Api('/rest/v1/scouting_tells?select=*&order=created_at.asc');
      const mapped=players.map(r=>kpcV28PlayerFromRow(r,tells||[]));
      for(const r of players){
        if(r.photo_data){
          try{ await kpcScoutSetPhoto(r.id,r.photo_data); }catch(e){}
        }
      }
      kpcScoutProfiles=mapped;
      kpcScoutSaveAll();
      kpcV28LastSync=Date.now();
      kpcV28SetState('online');
      if(render) kpcV28RenderCurrent();
      return mapped;
    }catch(e){
      kpcV28SetState('offline',e.message);
      if(!silent) console.warn('Scouting cloud:',e.message);
      throw e;
    }finally{kpcV28SyncPromise=null}
  })();
  return kpcV28SyncPromise;
}

function kpcV28SetState(state,msg=''){
  kpcV28RealtimeState=state;
  const el=$('#kpc-v28-sync');
  if(!el) return;
  el.className='kpc-v28-sync '+state;
  el.textContent=state==='online'?'☁️ KPC partagé • synchronisé':state==='syncing'?'↻ Synchronisation…':'⚠ Hors ligne • cache local';
  if(msg) el.title=msg;
}
function kpcV28InjectStatus(){
  const host=$('#modal-content'); if(!host) return;
  let el=$('#kpc-v28-sync');
  if(!el){
    el=document.createElement('div');
    el.id='kpc-v28-sync';
    const head=host.querySelector('.modal-head');
    if(head) head.insertAdjacentElement('afterend',el); else host.prepend(el);
  }
  kpcV28SetState(kpcV28RealtimeState);
}
function kpcV28Editing(){ return !!($('#sc_club')||$('#st_obs')); }

const kpcV28BaseOpenScouting=window.openScouting;
const kpcV28BaseOpenProfile=window.openScoutProfile;
const kpcV28BaseOpenEdit=window.openScoutEdit;

window.openScouting=async function(){
  const token=kpcV28SetView('list',null);
  try{ await kpcV28LoadAll({migrate:true,silent:true}); }catch(e){}
  if(token!==kpcV28ViewToken || kpcV28CurrentView.type!=='list') return;
  const r=await kpcV28BaseOpenScouting();
  if(token!==kpcV28ViewToken) return r;
  setTimeout(()=>{ if(token===kpcV28ViewToken && kpcV28ScoutingVisible()) kpcV28InjectStatus(); },0);
  kpcV28ConnectRealtime();
  return r;
};
openScouting=window.openScouting;

window.openScoutProfile=async function(id){
  const token=kpcV28SetView('profile',id);
  if(Date.now()-kpcV28LastSync>5000){
    try{ await kpcV28LoadAll({migrate:true,silent:true}); }catch(e){}
  }
  if(token!==kpcV28ViewToken || kpcV28CurrentView.type!=='profile' || kpcV28CurrentView.id!==id) return;
  const r=await kpcV28BaseOpenProfile(id);
  if(token!==kpcV28ViewToken) return r;
  setTimeout(()=>{ if(token===kpcV28ViewToken && kpcV28ScoutingVisible()) kpcV28InjectStatus(); },0);
  kpcV28ConnectRealtime();
  return r;
};
openScoutProfile=window.openScoutProfile;

window.openScoutEdit=async function(id=''){
  const token=kpcV28SetView('edit',id||null);
  if(Date.now()-kpcV28LastSync>5000){
    try{ await kpcV28LoadAll({migrate:true,silent:true}); }catch(e){}
  }
  if(token!==kpcV28ViewToken || kpcV28CurrentView.type!=='edit') return;
  return kpcV28BaseOpenEdit(id);
};
openScoutEdit=window.openScoutEdit;

function kpcV28RenderCurrent(){
  if(!kpcV28ScoutingVisible() || kpcV28Editing()) return;
  const token=kpcV28ViewToken;
  if(kpcV28CurrentView.type==='profile' && kpcV28CurrentView.id){
    kpcV28BaseOpenProfile(kpcV28CurrentView.id).then(()=>{
      if(token===kpcV28ViewToken && kpcV28ScoutingVisible()) setTimeout(kpcV28InjectStatus,0);
    });
  }else if(kpcV28CurrentView.type==='list'){
    kpcV28BaseOpenScouting().then(()=>{
      if(token===kpcV28ViewToken && kpcV28ScoutingVisible()) setTimeout(kpcV28InjectStatus,0);
    });
  }
}

const kpcV28BaseCloseModal=window.closeModal;
window.closeModal=function(){
  kpcV28ClearView();
  return kpcV28BaseCloseModal();
};
closeModal=window.closeModal;

const kpcV28BaseNavigate=window.navigate;
window.navigate=function(view){
  kpcV28ClearView();
  return kpcV28BaseNavigate(view);
};
navigate=window.navigate;

window.kpcScoutSaveProfile=async function(id){
  const club=$('#sc_club')?.value.trim(), pseudo=$('#sc_pseudo')?.value.trim();
  if(!club||!pseudo){ alert('Le club et le pseudo sont nécessaires.'); return; }
  const btn=$('#sc_save_btn');
  const originalLabel=btn?.innerHTML||'💾 Enregistrer le profil';
  if(btn){btn.disabled=true;btn.innerHTML='↻ Enregistrement…';}
  const sourceId=id;
  if(!kpcV28UuidOk(id)) id=kpcScoutUid();
  try{
    kpcV28SetState('syncing');
    const me=await kpcV28GetMe();
    const sess=kpcV28Session();
    const old=kpcScoutFind(sourceId)||kpcScoutFind(id);
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
      encounters:+$('#sc_encounters')?.value||0,lastSeen:$('#sc_lastseen')?.value||''
    });
    const photo=kpcScoutDraftPhoto||await kpcScoutGetPhoto(sourceId)||await kpcScoutGetPhoto(id)||null;
    const common={
      club,pseudo,name:p.name||null,profile_data:kpcV28ProfileData(p),photo_data:photo,
      encounters:p.encounters,last_seen:p.lastSeen||null,
      updated_by:sess.user.id,updated_by_name:me.display_name||'Membre KPC',
      updated_at:new Date().toISOString()
    };
    if(old && kpcV28UuidOk(sourceId)){
      await kpcV28Api('/rest/v1/scouting_players?id=eq.'+encodeURIComponent(sourceId),{
        method:'PATCH',headers:{Prefer:'return=minimal'},body:JSON.stringify(common)
      });
    }else{
      await kpcV28Api('/rest/v1/scouting_players',{
        method:'POST',headers:{Prefer:'return=minimal'},body:JSON.stringify({
          id,...common,created_by:sess.user.id,created_by_name:me.display_name||'Membre KPC',created_at:new Date().toISOString()
        })
      });
    }
    if(photo) await kpcScoutSetPhoto(id,photo);
    if(sourceId!==id){ try{await kpcScoutDeletePhoto(sourceId)}catch(e){} }
    kpcScoutDraftPhoto=null;
    await kpcV28LoadAll({migrate:false,silent:true});
    toast('Profil partagé avec l’équipe ✓');
    await window.openScoutProfile(id);
  }catch(e){
    kpcV28SetState('offline',e.message);
    alert(e.message.includes('duplicate')?'Ce pseudo existe déjà dans ce club.':('Synchronisation impossible : '+e.message));
    if(btn){btn.disabled=false;btn.innerHTML=originalLabel;}
  }
};
kpcScoutSaveProfile=window.kpcScoutSaveProfile;

window.kpcScoutSaveTell=async function(id){
  const obs=$('#st_obs')?.value.trim();
  if(!obs){ alert('Décris le tell observé.'); return; }
  try{
    const me=await kpcV28GetMe(), sess=kpcV28Session();
    await kpcV28Api('/rest/v1/scouting_tells',{
      method:'POST',headers:{Prefer:'return=minimal'},body:JSON.stringify({
        id:kpcScoutUid(),player_id:id,category:$('#st_cat')?.value||'Autre',observation:obs,
        context:$('#st_ctx')?.value||'',hypothesis:$('#st_hyp')?.value||'',
        confidence:+$('#st_conf')?.value||2,confirmed:!!$('#st_confirmed')?.checked,
        created_by:sess.user.id,created_by_name:me.display_name||'Membre KPC',
        updated_by:sess.user.id,updated_by_name:me.display_name||'Membre KPC',
        created_at:new Date().toISOString(),updated_at:new Date().toISOString()
      })
    });
    await kpcV28LoadAll({migrate:false,silent:true});
    toast('Tell partagé avec l’équipe ✓');
    await window.openScoutProfile(id);
  }catch(e){ alert('Impossible d’ajouter le tell : '+e.message); }
};
kpcScoutSaveTell=window.kpcScoutSaveTell;

window.kpcScoutMarkSeen=async function(id){
  const p=kpcScoutFind(id); if(!p) return;
  try{
    const me=await kpcV28GetMe(), sess=kpcV28Session();
    await kpcV28Api('/rest/v1/scouting_players?id=eq.'+encodeURIComponent(id),{
      method:'PATCH',headers:{Prefer:'return=minimal'},body:JSON.stringify({
        encounters:(+p.encounters||0)+1,last_seen:new Date().toISOString().slice(0,10),
        updated_by:sess.user.id,updated_by_name:me.display_name||'Membre KPC',updated_at:new Date().toISOString()
      })
    });
    await kpcV28LoadAll({migrate:false,silent:true});
    toast('Rencontre synchronisée ✓');
    await window.openScoutProfile(id);
  }catch(e){ alert('Mise à jour impossible : '+e.message); }
};
kpcScoutMarkSeen=window.kpcScoutMarkSeen;

window.kpcScoutDelete=async function(id){
  const p=kpcScoutFind(id); if(!p) return;
  if(!confirm('Supprimer définitivement le profil partagé de '+(p.pseudo||'ce joueur')+' ?')) return;
  try{
    await kpcV28Api('/rest/v1/scouting_players?id=eq.'+encodeURIComponent(id),{method:'DELETE',headers:{Prefer:'return=minimal'}});
    await kpcScoutDeletePhoto(id);
    await kpcV28LoadAll({migrate:false,silent:true});
    toast('Profil partagé supprimé');
    await window.openScouting();
  }catch(e){
    alert('Suppression refusée. Seul le créateur du profil ou un administrateur peut le supprimer.');
  }
};
kpcScoutDelete=window.kpcScoutDelete;

function kpcV28DisconnectRealtime(){
  if(kpcV28Heartbeat){clearInterval(kpcV28Heartbeat);kpcV28Heartbeat=null}
  if(kpcV28RetryTimer){clearTimeout(kpcV28RetryTimer);kpcV28RetryTimer=null}
  if(kpcV28Socket){try{kpcV28Socket.close()}catch(e){} kpcV28Socket=null}
  kpcV28SetState('offline');
}
function kpcV28ScheduleRefresh(){
  clearTimeout(kpcV28DebounceTimer);
  kpcV28DebounceTimer=setTimeout(async()=>{
    try{
      await kpcV28LoadAll({migrate:false,silent:true});
      if(kpcV28ScoutingVisible() && !kpcV28Editing()){
        kpcV28RenderCurrent();
        if(kpcV28ScoutingVisible() && (kpcV28CurrentView.type==='list'||kpcV28CurrentView.type==='profile')) toast('Scouting KPC mis à jour ✓');
      }
    }catch(e){}
  },450);
}
function kpcV28Send(msg){
  if(kpcV28Socket?.readyState===WebSocket.OPEN) kpcV28Socket.send(JSON.stringify(msg));
}
function kpcV28ConnectRealtime(){
  const sess=kpcV28Session();
  if(!sess?.access_token){ if(kpcV28Socket) kpcV28DisconnectRealtime(); return; }
  if(kpcV28Socket && (kpcV28Socket.readyState===WebSocket.OPEN||kpcV28Socket.readyState===WebSocket.CONNECTING)) return;
  try{
    const url='wss://xfutvyvvhlhpeowtgfbq.supabase.co/realtime/v1/websocket?apikey='+encodeURIComponent(KPC_V28_KEY)+'&vsn=1.0.0';
    const ws=new WebSocket(url); kpcV28Socket=ws;
    ws.onopen=()=>{
      kpcV28SetState('online');
      const ref=String(kpcV28Ref++);
      kpcV28Send({
        topic:'realtime:kpc-scouting',event:'phx_join',ref,join_ref:ref,
        payload:{config:{
          broadcast:{self:false},presence:{key:''},
          postgres_changes:[
            {event:'*',schema:'public',table:'scouting_players'},
            {event:'*',schema:'public',table:'scouting_tells'}
          ],
          private:false
        },access_token:kpcV28Session()?.access_token||''}
      });
      if(kpcV28Heartbeat) clearInterval(kpcV28Heartbeat);
      kpcV28Heartbeat=setInterval(()=>kpcV28Send({topic:'phoenix',event:'heartbeat',payload:{},ref:String(kpcV28Ref++)}),25000);
    };
    ws.onmessage=ev=>{
      let m=null; try{m=JSON.parse(ev.data)}catch(e){return}
      if(m?.event==='postgres_changes') kpcV28ScheduleRefresh();
      if(m?.event==='phx_reply' && m?.payload?.status==='error') console.warn('KPC Realtime:',m.payload.response);
    };
    ws.onerror=()=>kpcV28SetState('offline');
    ws.onclose=()=>{
      if(kpcV28Socket===ws) kpcV28Socket=null;
      if(kpcV28Heartbeat){clearInterval(kpcV28Heartbeat);kpcV28Heartbeat=null}
      kpcV28SetState('offline');
      if(kpcV28Session()?.access_token && !kpcV28RetryTimer){
        kpcV28RetryTimer=setTimeout(()=>{kpcV28RetryTimer=null;kpcV28ConnectRealtime()},5000);
      }
    };
  }catch(e){ kpcV28SetState('offline',e.message); }
}
window.kpcV28ForceSync=async function(){
  try{await kpcV28LoadAll({migrate:true,render:true});toast('Scouting KPC synchronisé ✓')}catch(e){alert(e.message)}
};

setTimeout(()=>{ if(kpcV28Session()?.access_token) kpcV28ConnectRealtime(); },2500);
setInterval(()=>{
  if(kpcV28Session()?.access_token){
    if(!kpcV28Socket || kpcV28Socket.readyState>1) kpcV28ConnectRealtime();
  }else if(kpcV28Socket) kpcV28DisconnectRealtime();
},20000);
setInterval(()=>{
  if(document.hidden || kpcV28Editing()) return;
  if(!kpcV28Session()?.access_token) return;
  if((kpcV28CurrentView.type==='list'||kpcV28CurrentView.type==='profile') && Date.now()-kpcV28LastSync>12000){
    kpcV28LoadAll({migrate:false,render:true,silent:true}).catch(()=>{});
  }
},15000);
window.addEventListener('online',()=>{kpcV28ConnectRealtime();kpcV28ScheduleRefresh()});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&kpcV28Session()?.access_token){kpcV28ConnectRealtime(); if(Date.now()-kpcV28LastSync>30000)kpcV28ScheduleRefresh();}});
'''

s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-scout-cloud-v28">
.kpc-v28-sync{margin:0 0 12px;padding:7px 10px;border-radius:10px;border:1px solid var(--line);font-size:.72rem;text-align:center}
.kpc-v28-sync.online{background:#0b342d;border-color:#3c987d;color:#bfe8dc}
.kpc-v28-sync.syncing{background:#382f12;border-color:#a98532;color:#f0d47d}
.kpc-v28-sync.offline{background:#3c1d25;border-color:#974d5d;color:#ffc0ca}
</style>'''
if 'id="kpc-scout-cloud-v28"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.8 collaborative cloud scouting patch applied')
