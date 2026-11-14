#!/usr/bin/env python3
"""Applique F1-F5 sur fire-monitor-aurel.html (original propre)."""
import sys
from pathlib import Path

FILE = Path('fire-monitor-aurel.html')
content = FILE.read_text(encoding='utf-8')

errors = []

# ============ 1. CSS ============
css = '''/* ---- Couche risque (F1-F5) ---- */
#riskSphere{position:absolute;bottom:6.5rem;left:max(1rem,env(safe-area-inset-left));z-index:900;width:3.2rem;height:3.2rem;display:grid;place-items:center;border-radius:50%;background:linear-gradient(145deg,#FF8447,var(--ember) 55%,#C23805);color:#fff;box-shadow:var(--sh),inset 0 1px 0 rgb(255 255 255/.35);cursor:pointer;transition:transform .2s,box-shadow .2s}
#riskSphere:hover{transform:scale(1.08);box-shadow:var(--sh),0 0 0 6px rgb(242 84 27/.18),inset 0 1px 0 rgb(255 255 255/.35)}
#riskSphere .ic{width:1.5rem;height:1.5rem}
#riskSphere .pulse-dot{position:absolute;top:.25rem;right:.25rem;width:.55rem;height:.55rem;border-radius:50%;background:#FFC83D;box-shadow:0 0 0 3px rgb(14 42 37/.5)}
#riskSphere.has-data .pulse-dot{animation:riskPulse 2.2s infinite}
@keyframes riskPulse{0%{box-shadow:0 0 0 0 rgb(255 200 61/.7)}70%,100%{box-shadow:0 0 0 .5rem rgb(255 200 61/0)}}
.risk-cell{cursor:pointer;transition:fill-opacity .15s}
.risk-cell:hover{fill-opacity:.85 !important}
.risk-legend{margin-top:.5rem}
.risk-legend .rl-title{font-weight:700;font-size:.78rem;margin-bottom:.3rem;color:var(--text)}
.risk-scale{display:flex;height:.55rem;border-radius:999px;overflow:hidden;margin:.25rem 0 .35rem}
.risk-scale span{flex:1}
.risk-labels{display:flex;justify-content:space-between;font-size:.68rem;color:var(--muted)}
.risk-meta{font-size:.72rem;color:var(--muted);margin-top:.25rem}
.rp-status{display:inline-flex;align-items:center;gap:.35rem;padding:.25rem .65rem;border-radius:999px;font-size:.72rem;font-weight:700}
.rp-status.ok{color:var(--ok);background:var(--ok-bg)}.rp-status.warn{color:var(--warn);background:var(--warn-bg)}.rp-status.err{color:var(--bad);background:var(--bad-bg)}.rp-status.none{color:var(--muted);background:#E6EDEA}
.metrics-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin-top:.5rem}
.metric-card{padding:.6rem .7rem;background:var(--ash);border-radius:var(--r-s);text-align:center}
.metric-card .mk{font-size:.65rem;font-weight:700;text-transform:uppercase;color:var(--muted);letter-spacing:.04em}
.metric-card .mv{font:700 1.2rem var(--display);color:var(--text);font-variant-numeric:tabular-nums}
@media (max-width:760px){#riskSphere{bottom:5.5rem;left:.75rem}}
'''

anchor = '@media (prefers-reduced-motion:reduce)'
if anchor not in content:
    errors.append("CSS anchor not found"); sys.exit(1)
content = content.replace(anchor, css + anchor, 1)
print("[css] OK")

# ============ 2. HTML — sphère ============
sphere = '''<div id="riskSphere" title="Couche risque de feu" aria-label="Afficher la couche risque de feu">
  <svg class="ic" aria-hidden="true"><use href="#i-flame"/></svg>
  <span class="pulse-dot"></span>
</div>'''
anchor = '<main id="map" role="application" aria-label="Carte interactive des feux actifs" tabindex="-1"></main>'
if anchor not in content:
    errors.append("main anchor not found"); sys.exit(1)
content = content.replace(anchor, anchor + sphere, 1)
print("[sphere] OK")

# ============ 3. HTML — bouton dock Risque ============
dock_old = '''  <button class="navbtn" data-view="dq" type="button" title="Rapport de qualité des données" aria-current="false"><svg class="ic" aria-hidden="true"><use href="#i-checks"/></svg><span class="lbl">Qualité</span></button>
</nav>'''
dock_new = '''  <button class="navbtn" data-view="dq" type="button" title="Rapport de qualité des données" aria-current="false"><svg class="ic" aria-hidden="true"><use href="#i-checks"/></svg><span class="lbl">Qualité</span></button>
  <button class="navbtn" data-view="risk" type="button" title="Couche risque de feu" aria-current="false"><svg class="ic" aria-hidden="true"><use href="#i-flame"/></svg><span class="lbl">Risque</span></button>
</nav>'''
if dock_old not in content:
    errors.append("dock anchor not found"); sys.exit(1)
content = content.replace(dock_old, dock_new, 1)
print("[dock btn] OK")

# ============ 4. HTML — légende + contrôles risque dans le HUD ============
hud_insert = '''      <div class="row"><span class="sw"><i style="width:5px;height:5px;background:#c9a39a;opacity:.85"></i></span>Il y a 2 à 7 jours</div>
      <!-- F3 : Bandeau honnêteté -->
      <div class="row" style="margin-top:.6rem;padding-top:.5rem;border-top:1px dashed var(--mist)">
        <span class="rp-status none" id="riskStatus">En attente</span>
      </div>
      <div class="row">
        <div style="font-size:.72rem;color:var(--muted);width:100%">
          <b>Risque d'activité de feu détectée</b><br>
          <small id="honestyMeta">Chargement de l'artéfact…</small>
        </div>
      </div>
      <!-- F4 : Slider de seuil -->
      <div class="row">
        <div style="width:100%">
          <div style="display:flex;justify-content:space-between;font-size:.7rem;color:var(--muted);margin-bottom:.15rem">
            <span>Seuil</span><span id="riskThVal">0%</span>
          </div>
          <input type="range" id="riskThreshold" min="0" max="100" value="0" step="1" style="width:100%;accent-color:var(--canopy)">
        </div>
      </div>
      <!-- F5 : Métriques -->
      <div class="row" style="margin-top:.4rem">
        <div class="metrics-grid" id="riskMetricsGrid" style="display:none;grid-template-columns:repeat(3,1fr);gap:.3rem"></div>
      </div>
      <div class="row" style="font-size:.72rem;color:var(--muted)" id="riskCellsMeta"></div>
    </div>
  </details>'''
hud_anchor = '''      <div class="row"><span class="sw"><i style="width:5px;height:5px;background:#c9a39a;opacity:.85"></i></span>Il y a 2 à 7 jours</div>
    </div>
  </details>'''
if hud_anchor not in content:
    errors.append("HUD anchor not found"); sys.exit(1)
content = content.replace(hud_anchor, hud_insert, 1)
print("[hud] OK")

# ============ 5. JS — couche risque (F1-F5) ============
js = '''

/* =========================================================
   COUCHE RISQUE DE FEU (F1-F5)
   - Lecture seule de fire_risk.json ou /api/v1/fire-risk
   - Aucun calcul côté client
   ========================================================= */
const RISK_GRID = 0.25;
const CAM_BBOX = [8.4, 4.1, 16.4, 13.2];      // emprise
const RISK_LEVELS = [
  {min:0.0, label:'Faible',   color:'#FFC83D'},
  {min:0.3, label:'Modéré',   color:'#FF8A00'},
  {min:0.6, label:'Élevé',    color:'#F2541B'},
  {min:0.8, label:'Critique', color:'#A4201B'}
];
let riskData = null, riskLayer = null, riskVisible = true, riskThreshold = 0;

function riskLabel(p){ for(let i=RISK_LEVELS.length-1;i>=0;i--) if(p>=RISK_LEVELS[i].min) return RISK_LEVELS[i].label; return RISK_LEVELS[0].label; }
function riskColor(p){ for(let i=RISK_LEVELS.length-1;i>=0;i--) if(p>=RISK_LEVELS[i].min) return RISK_LEVELS[i].color; return RISK_LEVELS[0].color; }
function fmtDate(iso){ try{ return new Date(iso).toLocaleDateString('fr-FR'); }catch(e){ return '?'; } }

/* F1 : cellules colorées bornées à l'emprise */
function buildRiskRects(){
  if(!riskData || !riskData.cells) return [];
  const b = map.getBounds(), out = [];
  for(const c of riskData.cells){
    if(c.prob < riskThreshold) continue;
    let lat = c.lat, lon = c.lon;
    if(lat == null) lat = CAM_BBOX[1] + c.cell_j * RISK_GRID + RISK_GRID / 2;
    if(lon == null) lon = CAM_BBOX[0] + c.cell_i * RISK_GRID + RISK_GRID / 2;
    if(lat < CAM_BBOX[1] || lat > CAM_BBOX[3] || lon < CAM_BBOX[0] || lon > CAM_BBOX[2]) continue;
    if(!b.contains([lat, lon])) continue;
    out.push({
      i:c.cell_i, j:c.cell_j, lat, lon, prob:c.prob,
      bounds:[[lat - RISK_GRID/2, lon - RISK_GRID/2],[lat + RISK_GRID/2, lon + RISK_GRID/2]]
    });
  }
  return out;
}
function applyRiskLayer(){
  if(riskLayer){ map.removeLayer(riskLayer); riskLayer = null; }
  if(!riskData || !riskVisible) return;
  const lg = L.layerGroup();
  for(const r of buildRiskRects()){
    L.rectangle(r.bounds, {
      color:'transparent', weight:0,
      fillColor:riskColor(r.prob), fillOpacity:.55,
      className:'risk-cell', interactive:true
    }).bindPopup(
      '<b>Cellule ('+r.i+', '+r.j+')</b><br>'
      +'Probabilité : '+(r.prob*100).toFixed(1)+'%<br>'
      +'Niveau : '+riskLabel(r.prob)+'<br>'
      +'<small>'+(riskData.data_origin||'provenance ?')+' · généré le '+fmtDate(riskData.generated_at)+'</small>'
    ).addTo(lg);
  }
  lg.addTo(map);
  riskLayer = lg;
}

/* F3+F5 : bandeau honnêteté + métriques */
function renderRiskBanner(){
  const status = document.getElementById('riskStatus');
  const meta = document.getElementById('honestyMeta');
  if(!riskData){
    if(status){ status.textContent='Indisponible'; status.className='rp-status err'; }
    if(meta) meta.textContent='Artéfact fire_risk.json introuvable — couche masquée';
    return;
  }
  const m = riskData.metrics || {};
  if(status){ status.textContent='Données chargées'; status.className='rp-status ok'; }
  const origin = riskData.data_origin || 'inconnue';
  const gen = fmtDate(riskData.generated_at);
  let txt = 'données '+origin+' · généré le '+gen;
  if(m.pr_auc != null) txt += ' · PR-AUC '+m.pr_auc.toFixed(3);
  if(m.f1 != null) txt += ' · F1 '+m.f1.toFixed(3);
  if(m.baseline_pr_auc != null) txt += ' · baseline '+m.baseline_pr_auc.toFixed(3);
  if(meta) meta.textContent = txt;

  // métriques
  const grid = document.getElementById('riskMetricsGrid');
  const cells = riskData.cells || [];
  if(grid && (m.pr_auc != null || m.f1 != null)){
    grid.style.display = '';
    grid.innerHTML = [
      {k:'PR-AUC', v:m.pr_auc}, {k:'F1', v:m.f1}, {k:'Baseline', v:m.baseline_pr_auc}
    ].map(x => '<div class="metric-card"><div class="mk">'+x.k+'</div><div class="mv">'+(x.v!=null?x.v.toFixed(3):'—')+'</div></div>').join('');
  }
  const cm = document.getElementById('riskCellsMeta');
  if(cm){
    const high = cells.filter(c=>c.prob>=0.6).length;
    cm.innerHTML = '<b>'+cells.length+'</b> cellules · <b>'+high+'</b> ≥ 60% · grille '+RISK_GRID+'°';
  }
  document.getElementById('riskSphere').classList.add('has-data');
}

/* Chargement (règle 3.2) */
async function loadRiskData(){
  const status = document.getElementById('riskStatus');
  if(status){ status.textContent='Chargement…'; status.className='rp-status warn'; }
  const urls = ['/artifacts/fire_risk.json', '/api/v1/fire-risk'];
  for(const url of urls){
    try{
      const r = await fetch(url);
      if(!r.ok) continue;
      riskData = await r.json();
      renderRiskBanner();
      applyRiskLayer();
      return;
    }catch(e){}
  }
  if(status){ status.textContent='Indisponible'; status.className='rp-status err'; }
}

/* F2 : légende dans le HUD */
(function addRiskLegend(){
  const leg = document.getElementById('legend');
  if(!leg) return;
  const div = document.createElement('div');
  div.className = 'risk-legend';
  div.innerHTML = '<div class="rl-title">Risque détecté (probabilité)</div>'
    + '<div class="risk-scale">'+RISK_LEVELS.map(l=>'<span style="background:'+l.color+'"></span>').join('')+'</div>'
    + '<div class="risk-labels">'+RISK_LEVELS.map(l=>'<span>'+l.label+'</span>').join('')+'</div>';
  leg.querySelector('.legend-rows').appendChild(div);
})();

/* F4 : contrôles sphère + slider */
document.getElementById('riskSphere').onclick = function(){
  riskVisible = !riskVisible;
  applyRiskLayer();
  toast(riskVisible ? 'Couche risque affichée' : 'Couche risque masquée');
};
document.querySelector('.navbtn[data-view=risk]').onclick = function(){
  riskVisible = !riskVisible;
  applyRiskLayer();
  toast(riskVisible ? 'Couche risque affichée' : 'Couche risque masquée');
};
(function initSlider(){
  const s = document.getElementById('riskThreshold');
  if(!s) return;
  s.oninput = function(e){
    riskThreshold = +e.target.value / 100;
    document.getElementById('riskThVal').textContent = e.target.value+'%';
    applyRiskLayer();
  };
})();

/* Lancer le chargement après que la carte soit prête */
(function initRisk(){
  let tries = 0;
  const wait = setInterval(function(){
    if(typeof map !== 'undefined' && map.getBounds){ clearInterval(wait); loadRiskData(); }
    else if(++tries > 40) clearInterval(wait);
  }, 500);
})();
'''

anchor = '</script>\n</body>\n</html>'
if anchor not in content:
    errors.append("end anchor not found"); sys.exit(1)
content = content.replace(anchor, js + '\n' + anchor, 1)
print("[js] OK")

FILE.write_text(content, encoding='utf-8')

print(f"\nRésultat : {FILE.name} → {len(content)} octets, {len(content.splitlines())} lignes")
if errors:
    print("ERREURS:", errors)
    sys.exit(1)
print("Tout OK")
