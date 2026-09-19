from pathlib import Path

path=Path('app/src/main/assets/index.html')
s=path.read_text(encoding='utf-8')

# Ajout du bouton TELLS dans la grille d'accueil.
needle='''    <button class="dash-card journal" onclick="navigate('journal')">'''
card='''    <button class="dash-card tells" onclick="openTellsModule()">
      <span class="dash-icon">👁</span><b>TELLS</b><small>Lire les signaux</small><em>Observe. Recoupe. Confirme.</em>
    </button>
'''
if card.strip() not in s:
    if needle not in s:
        raise SystemExit('Dashboard insertion point not found')
    s=s.replace(needle,card+needle,1)

marker='</script>'
idx=s.rfind(marker)
if idx<0:
    raise SystemExit('No closing script tag found')

js=r'''
// --- KPC v2.6 : module pédagogique TELLS ---
const KPC_TELLS_V26 = true;

const kpcTellFamilies=[
  {
    icon:'⏱️',title:'Timing',subtitle:'Vitesse et rythme de décision',
    text:'Observe surtout les changements par rapport au rythme habituel du joueur : snap action, tank inhabituel, pause avant de miser, ou décision prise avant même que l’action arrive.',
    watch:'À recouper avec le sizing, la position et les habitudes déjà observées.'
  },
  {
    icon:'🧍',title:'Posture',subtitle:'Corps, tension et immobilité',
    text:'Changement soudain de posture, immobilité inhabituelle, recul, rapprochement de la table, épaules ou bras plus tendus : ce sont des variations d’état, pas des preuves de force ou de faiblesse.',
    watch:'La déviation par rapport au comportement normal vaut plus que le geste lui-même.'
  },
  {
    icon:'🪙',title:'Mains & jetons',subtitle:'Manipulation, comptage, préparation',
    text:'Regarde comment le joueur manipule ses jetons, prépare une mise, protège ses cartes ou recompte son stack. Une modification nette de sa routine peut signaler une décision plus chargée émotionnellement.',
    watch:'Ne confonds pas nervosité générale et information liée à la main.'
  },
  {
    icon:'🫁',title:'Respiration & voix',subtitle:'Souffle, débit, volume',
    text:'Respiration retenue ou accélérée, déglutition, voix plus basse, plus rapide ou soudainement différente : ces indices peuvent révéler de l’activation émotionnelle.',
    watch:'Activation émotionnelle ne veut pas dire automatiquement bluff.'
  },
  {
    icon:'👀',title:'Regard & attention',subtitle:'Où va l’attention ?',
    text:'Observe les ruptures : regard répété vers ton stack, le pot, les cartes ou un joueur précis. L’important est le changement de comportement et le moment où il survient.',
    watch:'Évite les règles simplistes du type “il regarde à gauche = il bluffe”.'
  },
  {
    icon:'💬',title:'Parole',subtitle:'Silence, bavardage, justification',
    text:'Un joueur très bavard qui devient silencieux — ou l’inverse — peut mériter ton attention. Les explications non sollicitées, questions ou tentatives d’influencer ta décision sont surtout intéressantes si elles sont inhabituelles.',
    watch:'Compare toujours avec sa manière normale de parler.'
  },
  {
    icon:'📏',title:'Sizing + comportement',subtitle:'Le combo le plus utile',
    text:'Un changement de sizing accompagné d’un changement de timing ou de posture est souvent plus intéressant qu’un tell physique isolé.',
    watch:'Le betting pattern reste généralement plus exploitable que le langage corporel seul.'
  }
];

const kpcTellCombos=[
  {
    icon:'🧊',name:'Immobilité + souffle modifié + gros bet',
    signal:'Le joueur devient soudain très immobile, sa respiration change et il utilise un sizing important ou inhabituel.',
    orient:'Hypothèse : forte activation émotionnelle. Cherche ensuite si ce profil a déjà montré ce cluster en value ou en bluff.',
    level:'Cluster fort à noter'
  },
  {
    icon:'🎭',name:'Parole inhabituelle + regard sur ton stack + sizing atypique',
    signal:'Le joueur change soudain son niveau de parole, vérifie ton stack et choisit une taille de mise inhabituelle.',
    orient:'Hypothèse : tentative d’influence ou décision à fort enjeu. Ne décide pas “bluff/value” sans historique.',
    level:'Très intéressant avec historique'
  },
  {
    icon:'🧮',name:'Tank + recomptage + hésitation de jetons',
    signal:'Temps de réflexion inhabituel, stack recompté plusieurs fois et préparation/abandon de jetons.',
    orient:'Hypothèse : vraie zone de décision ou construction du sizing. Compare avec ses tanks précédents et la cohérence de sa ligne.',
    level:'Bon signal de difficulté'
  },
  {
    icon:'⚡',name:'Snap action + sizing standard + corps inchangé',
    signal:'Décision immédiate, sizing habituel, aucune rupture visible de posture ou de respiration.',
    orient:'Hypothèse : action préparée ou décision facile pour ce joueur. C’est souvent un cluster plus “routine” qu’émotionnel.',
    level:'Faible charge apparente'
  },
  {
    icon:'🫨',name:'Tremblement + respiration + manipulation différente',
    signal:'Les mains tremblent davantage, le souffle change et la manipulation des jetons devient différente.',
    orient:'Hypothèse : adrénaline / excitation. Cela peut accompagner une très grosse main comme un bluff : valide au showdown avant de l’utiliser.',
    level:'Arousal, direction incertaine'
  },
  {
    icon:'🔁',name:'Rupture de routine sur plusieurs streets',
    signal:'Le même joueur change de rythme, posture ou parole exactement quand le pot grossit, puis revient à sa routine après l’action.',
    orient:'Hypothèse : cluster personnel reproductible. C’est ce type de répétition qu’il faut mémoriser.',
    level:'Le plus précieux à long terme'
  }
];

function kpcTellFamilyHTML(x){
  return `<details class="kpc-tell-detail">
    <summary><span class="kpc-tell-icon">${x.icon}</span><div><b>${esc(x.title)}</b><small>${esc(x.subtitle)}</small></div><span>＋</span></summary>
    <p>${esc(x.text)}</p>
    <div class="kpc-tell-watch">🎯 ${esc(x.watch)}</div>
  </details>`;
}
function kpcTellComboHTML(x){
  return `<article class="kpc-tell-combo">
    <div class="kpc-tell-combo-head"><span>${x.icon}</span><div><b>${esc(x.name)}</b><small>${esc(x.level)}</small></div></div>
    <p><strong>Ce que tu vois :</strong> ${esc(x.signal)}</p>
    <p><strong>Comment t’orienter :</strong> ${esc(x.orient)}</p>
  </article>`;
}

function openTellsModule(){
  const html=`<div class="modal-head"><div><span class="eyebrow">Observation live</span><h2>👁 Tells Poker</h2></div><button class="icon-btn" onclick="closeModal()">✕</button></div>
  <p class="lead">Un tell est un <b>indice</b>, jamais une preuve. La bonne lecture vient d’un <b>changement par rapport au comportement habituel</b>, renforcé par plusieurs signaux et par le contexte de la main.</p>

  <div class="kpc-tell-rule">
    <b>La règle KPC : 1 tell = rien • 2 tells = hypothèse • 3 signaux cohérents + historique = information exploitable</b>
  </div>

  <div class="kpc-tell-method">
    <div><b>1</b><span><strong>Baseline</strong><small>Comment joue-t-il quand rien de spécial ne se passe ?</small></span></div>
    <div><b>2</b><span><strong>Déviation</strong><small>Qu’est-ce qui vient de changer ?</small></span></div>
    <div><b>3</b><span><strong>Cluster</strong><small>Y a-t-il 2 ou 3 signaux au même moment ?</small></span></div>
    <div><b>4</b><span><strong>Contexte</strong><small>Sizing, position, stack, action précédente.</small></span></div>
    <div><b>5</b><span><strong>Validation</strong><small>Showdown ou répétition future avant d’en faire une règle.</small></span></div>
  </div>

  <h3>Qu’est-ce que je peux regarder ?</h3>
  <div class="kpc-tell-families">${kpcTellFamilies.map(kpcTellFamilyHTML).join('')}</div>

  <h3 class="kpc-tell-title-space">Combos de tells à surveiller</h3>
  <p class="muted small">Ces combos servent à construire une hypothèse. Ils ne disent pas automatiquement “force” ou “bluff”.</p>
  <div class="kpc-tell-combos">${kpcTellCombos.map(kpcTellComboHTML).join('')}</div>

  <div class="toolbox">
    <b>🎯 Exercice KPC — 1 orbite</b>
    <p>Choisis un seul joueur. Pendant une orbite, ne cherche pas à deviner ses cartes. Observe seulement sa routine : timing, posture, parole, respiration, manipulation des jetons. Note mentalement les ruptures. Au showdown, vérifie si une rupture se répète.</p>
  </div>

  <div class="note">
    <b>À retenir</b>
    <p>Le tell le plus fiable n’est pas “un geste universel”. C’est souvent <b>un comportement personnel qui se répète dans le même contexte</b>.</p>
  </div>

  <button class="primary full" onclick="closeModal()">Retour à l’application</button>`;
  openModal(html);
}
window.openTellsModule=openTellsModule;
'''

s=s[:idx]+js+'\n'+s[idx:]

styles=r'''<style id="kpc-tells-v26">
.dash-card.tells{border-color:#62c3a9;background:linear-gradient(155deg,#0b4a43,#071a25 72%)}
.kpc-tell-rule{margin:12px 0 16px;padding:12px 13px;border:1px solid #d8ad3e88;border-radius:13px;background:#392f1238;color:#f2d27c;font-size:.9rem;line-height:1.45}
.kpc-tell-method{display:grid;gap:7px;margin:12px 0 18px}
.kpc-tell-method>div{display:grid;grid-template-columns:32px 1fr;gap:9px;align-items:center;padding:9px 10px;border:1px solid var(--line);border-radius:11px;background:#091d32}
.kpc-tell-method>div>b{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:#173c5b;color:var(--gold)}
.kpc-tell-method span{display:flex;flex-direction:column}.kpc-tell-method small{color:var(--muted);margin-top:2px;line-height:1.3}
.kpc-tell-detail{border:1px solid var(--line);border-radius:12px;background:#091c31;margin:8px 0;overflow:hidden}
.kpc-tell-detail summary{list-style:none;display:grid;grid-template-columns:35px 1fr 20px;gap:8px;align-items:center;padding:11px;cursor:pointer}
.kpc-tell-detail summary::-webkit-details-marker{display:none}.kpc-tell-detail summary div{display:flex;flex-direction:column}.kpc-tell-detail summary small{color:var(--muted);margin-top:2px}
.kpc-tell-detail p{margin:0;padding:0 12px 10px;line-height:1.5;color:#d7e2ed}
.kpc-tell-icon{font-size:24px}.kpc-tell-watch{margin:0 10px 10px;padding:9px;border-radius:9px;background:#0e2a46;color:#bcd0df;font-size:.78rem;line-height:1.4}
.kpc-tell-title-space{margin-top:20px}
.kpc-tell-combos{display:grid;gap:9px}
.kpc-tell-combo{border:1px solid #315875;border-left:4px solid var(--gold);border-radius:12px;padding:11px;background:#081a2d}
.kpc-tell-combo-head{display:flex;gap:9px;align-items:center}.kpc-tell-combo-head>span{font-size:25px}.kpc-tell-combo-head div{display:flex;flex-direction:column}.kpc-tell-combo-head small{color:var(--gold);margin-top:2px}
.kpc-tell-combo p{font-size:.82rem;line-height:1.45;color:#c8d6e3;margin:8px 0 0}.kpc-tell-combo strong{color:#fff}
</style>'''
if 'id="kpc-tells-v26"' not in s:
    s=s.replace('</head>',styles+'</head>')

path.write_text(s,encoding='utf-8')
print('KPC v2.6 tells training module applied')
