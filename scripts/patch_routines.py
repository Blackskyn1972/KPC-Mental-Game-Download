from pathlib import Path

path = Path('app/src/main/assets/index.html')
s = path.read_text(encoding='utf-8')

start = s.index('function startWarmup(){')
end_marker = 'window.finishCooldown=finishCooldown;'
end = s.index(end_marker, start) + len(end_marker)

replacement = r'''let routineFlow = {};

function routineProgress(step,total,label){
  return `<div class="routine-progress"><span>${label}</span><b>${step}/${total}</b></div>`;
}

function startWarmup(){
  routineFlow={type:'warmup'};
  openModal(`<div class="modal-head"><div><span class="eyebrow">Préparation</span><h2>Warm-up mental</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(1,3,'État du moment')}
  <p class="muted">Rapide : note simplement où tu en es avant de jouer.</p>
  <label>Énergie <input type="range" min="1" max="5" value="3" id="wu0" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <label>Concentration <input type="range" min="1" max="5" value="3" id="wu1" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <label>Stabilité émotionnelle <input type="range" min="1" max="5" value="3" id="wu2" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <button class="primary full" onclick="warmupStep2()">Continuer</button>`);
}
window.startWarmup=startWarmup;

function warmupStep2(){
  routineFlow.energy=+$('#wu0').value; routineFlow.focus=+$('#wu1').value; routineFlow.mood=+$('#wu2').value;
  openModal(`<div class="modal-head"><div><span class="eyebrow">Préparation</span><h2>Mon intention</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(2,3,'Objectif de session')}
  <label>Mon objectif de processus
  <select id="wugoal"><option>Prendre mon temps avant les décisions importantes</option><option>Rester attentif aux sizings</option><option>Accepter la variance sans réaction immédiate</option><option>Observer les profils adverses</option><option>Ne pas jouer en pilote automatique</option><option>Rester discipliné après un gros pot</option></select></label>
  <label>Mon risque principal ce soir
  <select id="wurisk"><option>Aucun particulier</option><option>Fatigue</option><option>Impatience</option><option>Résultat / peur de perdre</option><option>Excès de confiance</option><option>Distraction</option></select></label>
  <button class="primary full" onclick="warmupStep3()">Continuer</button>`);
}
window.warmupStep2=warmupStep2;

function warmupStep3(){
  routineFlow.goal=$('#wugoal').value; routineFlow.risk=$('#wurisk').value;
  const last=store.get('kpc_last_cooldown',null);
  openModal(`<div class="modal-head"><div><span class="eyebrow">Préparation</span><h2>Je me recentre</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(3,3,'30 secondes')}
  ${last&&last.next?`<div class="routine-card"><b>Rappel de la dernière session</b><span>${esc(last.next)}</span></div>`:''}
  <div class="breath"><b>Respiration 4–6</b><span>Inspire 4 s • Expire 6 s • 3 cycles</span></div>
  <div class="routine-card"><b>Ma phrase d'ancrage</b><span>Je ne contrôle pas les cartes. Je contrôle mes décisions.</span></div>
  <button class="primary full" onclick="finishWarmup()">Je suis prêt</button>`);
}
window.warmupStep3=warmupStep3;

function finishWarmup(){
  state.routines.warmups++; store.set('kpc_routines',state.routines);
  const item={at:new Date().toISOString(),energy:routineFlow.energy,focus:routineFlow.focus,mood:routineFlow.mood,goal:routineFlow.goal,risk:routineFlow.risk};
  store.set('kpc_last_warmup',item);
  closeModal(); toast('Warm-up enregistré ✓'); renderHome();
}
window.finishWarmup=finishWarmup;

function startSOS(){
  routineFlow={type:'sos'};
  openModal(`<div class="modal-head"><div><span class="eyebrow">Urgence mentale</span><h2>🆘 SOS TILT</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(1,3,'Identifier')}
  <p class="muted">Pas d'analyse compliquée. Dis juste ce qui se passe.</p>
  <label>Niveau de tilt <input type="range" id="sostilt" min="1" max="5" value="3" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <label>Ce qui me touche le plus
  <select id="sostype"><option>Bad beat / injustice</option><option>Erreur que je viens de faire</option><option>Adversaire irritant</option><option>Peur de perdre / pression du résultat</option><option>Impatience / ennui</option><option>Excès de confiance / excitation</option></select></label>
  <button class="primary full" onclick="sosStep2()">Me recentrer</button>`);
}
window.startSOS=startSOS;

function sosStep2(){
  routineFlow.tilt=+$('#sostilt').value; routineFlow.tiltType=$('#sostype').value;
  openModal(`<div class="modal-head"><div><span class="eyebrow">Urgence mentale</span><h2>Reprendre le contrôle</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(2,3,'Protocole express')}
  <div class="sos-step"><b>1. STOP</b><span>Aucune décision précipitée. Ralentis.</span></div>
  <div class="sos-step"><b>2. RESPIRE</b><span>3 cycles : inspire 4 s, expire 6 s.</span></div>
  <div class="sos-step"><b>3. RECENTRE</b><span>Le coup précédent est terminé. Ma seule mission : la prochaine bonne décision.</span></div>
  <button class="primary full" onclick="sosStep3()">J'ai repris un peu de recul</button>`);
}
window.sosStep2=sosStep2;

function sosStep3(){
  openModal(`<div class="modal-head"><div><span class="eyebrow">Urgence mentale</span><h2>Et maintenant ?</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(3,3,'Décider lucidement')}
  <p class="muted">Choisis l'action la plus saine, pas la plus courageuse.</p>
  <div class="routine-actions">
    <button onclick="finishSOS('Continuer')"><b>✓ Continuer</b><span>Je me sens lucide</span></button>
    <button onclick="finishSOS('Pause')"><b>⏸ Pause 2 min</b><span>J'ai besoin de redescendre</span></button>
    <button onclick="finishSOS('Arrêter')"><b>■ Arrêter</b><span>Je protège ma qualité de jeu</span></button>
  </div>`);
}
window.sosStep3=sosStep3;

function finishSOS(action){
  state.routines.sos++; store.set('kpc_routines',state.routines);
  const item={id:uid(),type:'SOS Tilt',at:new Date().toISOString(),tilt:routineFlow.tilt,trigger:routineFlow.tiltType,action};
  state.journal.unshift(item); store.set('kpc_journal',state.journal);
  closeModal(); toast(action==='Continuer'?'Recentrage terminé ✓':action+' enregistrée ✓');
}
window.finishSOS=finishSOS;

function startCooldown(){
  routineFlow={type:'cooldown'};
  const last=store.get('kpc_last_warmup',null);
  openModal(`<div class="modal-head"><div><span class="eyebrow">Après-session</span><h2>Débrief</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(1,3,'Qualité de session')}
  ${last&&last.goal?`<div class="routine-card"><b>Objectif du warm-up</b><span>${esc(last.goal)}</span></div>`:''}
  <label>Qualité de mes décisions <input type="range" id="cd1" min="1" max="5" value="3" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <label>Gestion émotionnelle <input type="range" id="cd2" min="1" max="5" value="3" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <label>Concentration <input type="range" id="cd3" min="1" max="5" value="3" oninput="this.nextElementSibling.textContent=this.value+'/5'"><span class="range-val">3/5</span></label>
  <button class="primary full" onclick="cooldownStep2()">Continuer</button>`);
}
window.startCooldown=startCooldown;

function cooldownStep2(){
  routineFlow.decision=+$('#cd1').value; routineFlow.emotion=+$('#cd2').value; routineFlow.focus=+$('#cd3').value;
  openModal(`<div class="modal-head"><div><span class="eyebrow">Après-session</span><h2>Ce que je retiens</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(2,3,'Deux réponses suffisent')}
  <label>Une chose bien faite <textarea id="cdgood" placeholder="Ex. J’ai pris mon temps sur les décisions importantes."></textarea></label>
  <label>Une chose à revoir <textarea id="cdwork" placeholder="Ex. J’ai accéléré après avoir perdu un gros pot."></textarea></label>
  <button class="primary full" onclick="cooldownStep3()">Continuer</button>`);
}
window.cooldownStep2=cooldownStep2;

function cooldownStep3(){
  routineFlow.good=$('#cdgood').value.trim(); routineFlow.work=$('#cdwork').value.trim();
  openModal(`<div class="modal-head"><div><span class="eyebrow">Après-session</span><h2>Prochaine session</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  ${routineProgress(3,3,'Un seul axe de travail')}
  <p class="muted">Choisis quelque chose de simple et concret à retrouver au prochain warm-up.</p>
  <label>Mon prochain axe
  <select id="cdnext"><option>Prendre plus de temps avant les grosses décisions</option><option>Accepter plus vite les coups perdus</option><option>Rester concentré entre les mains</option><option>Observer davantage les adversaires</option><option>Éviter le pilote automatique</option><option>Respecter ma discipline même sous pression</option></select></label>
  <button class="primary full" onclick="finishCooldown()">Enregistrer mon débrief</button>`);
}
window.cooldownStep3=cooldownStep3;

function finishCooldown(){
  const item={id:uid(),type:'Cooldown',at:new Date().toISOString(),decision:routineFlow.decision,emotion:routineFlow.emotion,focus:routineFlow.focus,good:routineFlow.good,work:routineFlow.work,next:$('#cdnext').value};
  state.journal.unshift(item); state.routines.cooldowns++;
  store.set('kpc_journal',state.journal); store.set('kpc_routines',state.routines); store.set('kpc_last_cooldown',item);
  closeModal(); toast('Débrief enregistré ✓'); renderHome();
}
window.finishCooldown=finishCooldown;'''

s = s[:start] + replacement + s[end:]

styles = r'''
<style id="kpc-routine-v18">
.routine-progress{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:4px 0 14px;padding:9px 12px;border-radius:12px;background:rgba(255,255,255,.06);font-size:.9rem}.routine-progress b{font-size:.8rem;opacity:.75}.routine-card{display:flex;flex-direction:column;gap:5px;margin:10px 0;padding:12px 14px;border-radius:14px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.08)}.routine-card span{font-size:.92rem;line-height:1.35;opacity:.86}.routine-actions{display:grid;gap:10px;margin-top:12px}.routine-actions button{display:flex;flex-direction:column;align-items:flex-start;gap:4px;width:100%;padding:14px;border-radius:14px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.055);color:inherit;text-align:left}.routine-actions button b{font-size:1rem}.routine-actions button span{font-size:.84rem;opacity:.72}.modal label{margin-bottom:12px}.modal textarea{min-height:74px}
</style>
'''
if 'id="kpc-routine-v18"' not in s:
    s = s.replace('</head>', styles + '</head>')

path.write_text(s, encoding='utf-8')
print('V1.8 routines patch applied')
