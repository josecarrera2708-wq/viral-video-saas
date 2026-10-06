const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let SET = {}, WALLETS = [], FEED = [], FILTER = '', timer = null;

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {credentials: 'same-origin'} :
    {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (r.status === 401) { showAuth(false); throw new Error('sesión'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || ('error ' + r.status));
  return j;
}
function toast(m) { const t = $('#toast'); t.textContent = m; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 2600); }
function ago(t) {
  if (!t) return '—';
  const s = Date.now() / 1000 - t;
  if (s < 60) return 'ahora'; if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`; return `hace ${Math.floor(s / 86400)} d`;
}
function hm(t) { const d = new Date(t * 1000); return d.toLocaleDateString('es-ES', {day: '2-digit', month: '2-digit'}) + ' ' + d.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'}); }
function usd(v) {
  if (v == null) return '?'; v = +v;
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B'; if (v >= 1e6) return '$' + (v / 1e6).toFixed(2) + 'M';
  if (v >= 1e3) return '$' + (v / 1e3).toFixed(1) + 'k'; return '$' + v.toFixed(0);
}
function price(p) {
  if (!p) return '?'; if (p >= 1) return '$' + p.toFixed(4);
  const dec = p.toFixed(15).split('.')[1]; const z = dec.length - dec.replace(/^0+/, '').length; return '$' + p.toFixed(z + 4);
}
function xs(v) { return v == null ? '' : `<span class="x ${v >= 1 ? 'up' : 'dn'}">x${v.toFixed(2)}</span>`; }
function tagCls(o) { o = (o || '').toLowerCase(); return o.includes('nacid') ? 'new' : o.includes('list') ? 'list' : o.includes('unip') ? 'uni' : ''; }
function copy(t) { (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => toast('Copiado'), () => toast(t)); }

// ---------- acceso ----------
async function boot() {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
  const me = await fetch('/api/me', {credentials: 'same-origin'}).then(r => r.json()).catch(() => ({}));
  if (me.setup) showAuth(true); else if (!me.logged) showAuth(false); else start();
}
function showAuth(setup) {
  $('#main').hidden = true; $('#tabs').hidden = true; $('#v-login').hidden = false;
  $('#code-wrap').hidden = !setup;
  $('#auth-title').textContent = setup ? 'Configurar' : 'Entrar';
  $('#auth-help').textContent = setup ? 'Primera vez: escribe el código que te dio el instalador y elige una contraseña (mínimo 8 caracteres).' : 'Escribe tu contraseña.';
  $('#pw').autocomplete = setup ? 'new-password' : 'current-password';
  $('#auth-go').onclick = async () => {
    $('#auth-err').textContent = '';
    try {
      if (setup) await api('/api/setup', {code: $('#code').value, password: $('#pw').value});
      else await api('/api/login', {password: $('#pw').value});
      $('#pw').value = ''; start();
    } catch (e) { $('#auth-err').textContent = e.message; }
  };
}
async function start() {
  $('#v-login').hidden = true; $('#main').hidden = false; $('#tabs').hidden = false;
  await refreshMeta();
  route(); window.onhashchange = route;
  clearInterval(timer); timer = setInterval(() => { if (!document.hidden) { refreshMeta(); const v = curView(); if (v === 'feed') loadFeed(); } }, 20000);
}
async function refreshMeta() {
  try {
    [SET, WALLETS] = await Promise.all([api('/api/settings'), api('/api/wallets')]);
    const last = Math.max(SET.last_hook || 0, SET.last_poll || 0);
    const fresh = Date.now() / 1000 - last < 300;
    $('#live').className = 'dot ' + (fresh ? 'ok' : 'warn');
    $('#status').textContent = (SET.helius && SET.webhook_ok ? 'tiempo real' : 'sin Helius') + ' · revisado ' + ago(last);
  } catch (e) {}
}

// ---------- vistas ----------
function curView() { const h = location.hash.slice(1); return h.startsWith('t/') ? 'token' : (h || 'feed'); }
function route() {
  const v = curView();
  for (const s of document.querySelectorAll('.view')) if (s.id !== 'v-login') s.hidden = s.id !== 'v-' + v;
  for (const b of document.querySelectorAll('.tabs button')) b.classList.toggle('on', b.dataset.v === v);
  ({feed: loadFeed, copy: loadCopy, wallets: loadWallets, scan: loadScan, settings: loadSettings, token: loadToken}[v] || loadFeed)();
}
document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => { location.hash = b.dataset.v; });
$('#token-back').onclick = () => history.length > 1 ? history.back() : (location.hash = 'feed');

function tradeRow(r) {
  const buy = r.side === 'buy';
  return `<div class="trow" onclick="location.hash='t/${r.mint}'">
    <span class="side ${r.side}">${buy ? 'COMPRA' : 'VENDE'}</span>
    <div class="l1"><span class="sym">${esc(r.sym)}</span><span class="who">${esc(r.name)}</span>${r.hint ? `<span class="tag ${r.hint === 'posible listado' ? 'hint' : 'cexs'}">${esc(r.hint)}</span>` : ''}</div>
    <div class="xr">${buy ? xs(r.x_now) + `<small>máx ${r.x_max ? 'x' + r.x_max.toFixed(2) : '—'}</small>` : sellGain(r)}</div>
    <div class="l2">${hm(r.t)} · ${usd(r.usd)}${r.sol >= 0.05 ? ' (' + r.sol.toFixed(2) + ' SOL)' : ''} · MC ${usd(r.mc)}</div>
  </div>`;
}
function pnlTxt(v) { return `<b class="${v >= 0 ? 'up' : 'dn'}">${v >= 0 ? 'ganó' : 'perdió'} ${usd(Math.abs(v))}</b>`; }
function sellGain(r) {
  if (r.pnl != null) return xs(r.x_sell) + `<small>${pnlTxt(r.pnl)}</small>`;
  return `<span class="muted">${usd(r.usd)}</span><small>${r.entry === 0 ? 'compra no vista' : 'buscando compra…'}</small>`;
}
async function loadFeed() {
  try { FEED = await api('/api/feed?limit=200'); } catch (e) { return; }
  const names = [...new Set(WALLETS.map(w => w.name))];
  $('#feed-filters').innerHTML = ['', ...names].map(n => `<span class="chip ${n === FILTER ? 'on' : ''}" data-n="${esc(n)}">${n ? esc(n) : 'Todas'}</span>`).join('');
  document.querySelectorAll('#feed-filters .chip').forEach(c => c.onclick = () => { FILTER = c.dataset.n; loadFeed(); });
  const rows = FEED.filter(r => !FILTER || r.name === FILTER);
  $('#feed').innerHTML = rows.length ? rows.map(tradeRow).join('') :
    `<div class="empty">Todavía no hay compras ni ventas registradas.<br>En cuanto una de tus wallets opere, aparecerá aquí y te llegará el aviso.</div>`;
}

function pct(v) { return v == null ? '—' : (v >= 0 ? '+' : '') + Math.round(v) + '%'; }
function money(v) { return (v >= 0 ? '+' : '−') + '$' + Math.abs(v).toFixed(2); }
async function loadCopy() {
  let d;
  try { d = await api('/api/sim'); } catch (e) { return; }
  if (!d.cfg) { $('#copy').innerHTML = `<div class="empty">La simulación no está en marcha.</div>`; return; }
  const end = d.cfg.start + d.cfg.days * 86400, now = Date.now() / 1000;
  $('#copy-info').textContent = `${d.cfg.usd} USDT por operación, con comisiones del 1% al comprar y al vender. Empezó el ${hm(d.cfg.start)} y ` +
    (now < end ? `termina el ${hm(end)}.` : `terminó el ${hm(end)}.`) + ' Las operaciones abiertas se valoran al precio de ahora.';
  const tot = d.rows.reduce((a, r) => ({inv: a.inv + r.invested, pnl: a.pnl + r.pnl, won: a.won + r.won, lost: a.lost + r.lost, open: a.open + r.open}),
    {inv: 0, pnl: 0, won: 0, lost: 0, open: 0});
  const row = (name, plan, r, pct) => `<div class="crow">
      <div class="c1"><span class="nm">${esc(name)}</span>${plan ? `<span class="tag">${esc(plan)}</span>` : ''}</div>
      <div class="cr"><span class="x ${r.pnl >= 0 ? 'up' : 'dn'}">${pct == null ? '—' : (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%'}</span><small class="${r.pnl >= 0 ? 'up' : 'dn'}">${money(r.pnl)}</small></div>
      <div class="c2">${r.won} ganadas · ${r.lost} perdidas · ${r.open} abiertas · invertido $${(r.invested ?? r.inv).toFixed(0)}${r.medido != null ? ` · medido antes ${r.medido >= 0 ? '+' : ''}${r.medido}%` : ''}</div>
    </div>`;
  $('#copy').innerHTML = d.rows.map(r => row(r.name, r.plan, r, r.pct)).join('') +
    (d.rows.length > 1 ? row('Total', '', tot, tot.inv ? 100 * tot.pnl / tot.inv : null) : '');
}

async function loadWallets() {
  try { WALLETS = await api('/api/wallets'); } catch (e) { return; }
  if (!WALLETS.length) { $('#wallets').innerHTML = `<div class="empty">No hay wallets. Añádelas en Ajustes.</div>`; return; }
  $('#wallets').innerHTML = WALLETS.map((w, i) => {
    const s = w.stats || {};
    return `<div class="wrow ${w.active ? '' : 'off'}" data-i="${i}">
      <span class="rk">${i + 1}</span><span class="nm">${esc(w.name)}</span>
      ${w.origin ? `<span class="tag ${tagCls(w.origin)}">${esc(w.origin)}</span>` : ''}
      <span class="sp"></span><span class="last">${w.last ? (w.last.side === 'buy' ? 'compró ' : 'vendió ') + esc(w.last.sym) + ' ' + ago(w.last.t) : 'sin operaciones aún'}</span>
    </div>
    <div class="wdet" id="wd${i}" hidden>
      <div class="addr">${esc(w.addr)} <button class="btn sm" onclick="event.stopPropagation();copy('${w.addr}')">copiar</button></div>
      <div class="stats">
        <div class="stat"><b>${s.n || 0}</b><span>compras 30 d</span></div>
        <div class="stat"><b>${s.n ? s.pct_x2 + '%' : '—'}</b><span>llegan a x2</span></div>
        <div class="stat"><b>${s.n ? 'x' + s.avg_xmax : '—'}</b><span>x máx media</span></div>
        <div class="stat"><b>${s.n ? (s.ladder >= 0 ? '+' : '') + s.ladder + '%' : '—'}</b><span>tu método</span></div>
      </div>
      ${w.note ? `<div class="muted">${esc(w.note)}</div>` : ''}
      <div class="links"><a href="https://gmgn.ai/sol/address/${w.addr}" target="_blank" rel="noopener">GMGN</a><a href="https://solscan.io/account/${w.addr}" target="_blank" rel="noopener">Solscan</a></div>
    </div>`;
  }).join('');
  document.querySelectorAll('.wrow').forEach(r => r.onclick = () => { const d = $('#wd' + r.dataset.i); d.hidden = !d.hidden; });
}

async function loadToken() {
  const mint = location.hash.slice(3);
  let rows = [];
  try { rows = await api('/api/feed?mint=' + encodeURIComponent(mint)); } catch (e) { return; }
  const sym = rows[0]?.sym || mint.slice(0, 6);
  const buys = rows.filter(r => r.side === 'buy'), buy = buys[buys.length - 1];
  const sold = rows.filter(r => r.side === 'sell' && r.pnl != null), pnl = sold.reduce((a, r) => a + r.pnl, 0);
  $('#token').innerHTML = `<div class="card">
    <h1>${esc(sym)}</h1>
    <div class="addr">${esc(mint)} <button class="btn sm" onclick="copy('${mint}')">copiar contrato</button></div>
    ${buy ? `<div class="stats">
      <div class="stat"><b>${price(buy.price)}</b><span>precio compra</span></div>
      <div class="stat"><b>${usd(buy.mc)}</b><span>MC compra</span></div>
      <div class="stat"><b>${buy.x_now ? 'x' + buy.x_now.toFixed(2) : '—'}</b><span>ahora</span></div>
      <div class="stat"><b>${buy.x_max ? 'x' + buy.x_max.toFixed(2) : '—'}</b><span>máximo</span></div></div>
      <p class="small muted">Objetivo x2: MC ${usd(buy.mc * 2)} · tu método: vender 50% en x2, 50% del resto en x4…</p>` : ''}
    ${sold.length ? `<p class="small">Con sus ventas de este token ${pnlTxt(pnl)} (vendió ${usd(sold.reduce((a, r) => a + r.usd, 0))} en ${sold.length} ${sold.length > 1 ? 'ventas' : 'venta'}).</p>` : ''}
    <div class="links">
      <a href="https://gmgn.ai/sol/token/${mint}" target="_blank" rel="noopener">Comprar en GMGN</a>
      <a href="https://jup.ag/swap/SOL-${mint}" target="_blank" rel="noopener">Jupiter</a>
      <a href="https://dexscreener.com/solana/${mint}" target="_blank" rel="noopener">Gráfico</a>
    </div></div>
    <div class="list">${rows.map(tradeRow).join('')}</div>`;
}

async function loadScan() {
  let d;
  try { d = await api('/api/candidates'); } catch (e) { return; }
  const c = d.counts || {}, measured = (c['no pasa'] || 0) + (c.nueva || 0) + (c.seguida || 0);
  $('#scan-info').innerHTML = `Revisa los nuevos listados de los exchanges, busca las wallets que compraron antes y mide cuánto habría dado copiarlas (10 USDT por compra, vendiendo cuando venden, con y sin stop). Pasan las que, en al menos 15 compras, tienen más del 40% de acierto (llegan a x2) y copiarlas da +15% o más. Busca en dos categorías: compran antes de los listados, y compran tokens recién nacidos a MC muy bajo.
    <div class="stats"><div class="stat"><b>${d.tokens}</b><span>listados revisados</span></div><div class="stat"><b>${measured}</b><span>wallets medidas</span></div>
    <div class="stat"><b>${c.bot || 0}</b><span>bots descartados</span></div><div class="stat"><b>${(c.nueva || 0) + (c.seguida || 0)}</b><span>pasan el corte</span></div></div>
    Última búsqueda: ${d.last_scan ? hm(d.last_scan.t) + ' · ' + esc(d.last_scan.msg || '') : 'todavía no'}.
    <br>Marca «posible listado» (compras de tokens jóvenes que aún no cotizan en MEXC, Gate, Bitget ni KuCoin): ${d.hint ? `${d.hint.marked} tokens marcados, ${d.hint.listed} listados después` : '—'}.`;
  $('#cands').innerHTML = d.rows.length ? d.rows.map(c => `<div class="card">
      <div class="row" style="margin:0;align-items:center"><b class="addr" style="flex:1">${esc(c.addr.slice(0, 6))}…${esc(c.addr.slice(-4))}</b>
      <span class="tag ${tagCls(c.origin)}">${esc(c.origin)}</span>${c.status === 'seguida' ? '<span class="tag">seguida</span>' : ''}</div>
      <div class="stats">
        <div class="stat"><b>${c.n}</b><span>compras medidas</span></div>
        <div class="stat"><b>${c.pct_x2}%</b><span>llegan a x2</span></div>
        <div class="stat"><b>${pct(c.detail?.copia?.best ?? c.score)}</b><span>copiarla (mejor)</span></div>
        <div class="stat"><b>${pct(c.ladder)}</b><span>tu método</span></div>
      </div>
      ${c.detail?.copia ? `<div class="small muted">Copiarla: sin stop ${pct(c.detail.copia.copy)} · stop 30% ${pct(c.detail.copia.copy_sl30)} · stop 50% ${pct(c.detail.copia.copy_sl50)} · todo en x2 ${pct(c.all_x2)}</div>` : ''}
      <div class="small muted">Compró antes del listado en ${c.hits} tokens · x máx media x${c.avg_xmax}</div>
      ${c.status !== 'seguida' ? `<div class="row"><button class="btn primary" onclick="cand('${c.addr}','seguir')">Seguir</button><button class="btn ghost" onclick="cand('${c.addr}','descartar')">Descartar</button></div>` : ''}
    </div>`).join('') : `<div class="empty">Aún no hay candidatas que pasen el corte. El buscador sigue cada 4 horas.</div>`;
}
async function cand(a, act) { try { await api(`/api/candidates/${a}/${act}`, {}); toast(act === 'seguir' ? 'Añadida a tus wallets' : 'Descartada'); loadScan(); refreshMeta(); } catch (e) { toast(e.message); } }

async function loadSettings() {
  await refreshMeta();
  $('#w-edit').value = WALLETS.map(w => [w.name, w.addr, w.origin || '', (w.payers || []).join(', ')].join(' | ').replace(/ \| $/, '')).join('\n');
  $('#helius-state').textContent = SET.helius ? (SET.webhook_ok ? `Conectado. Último aviso de Helius: ${ago(SET.last_hook)}.` : 'Clave guardada, falta conectar.') : 'Sin clave: solo funciona el sondeo cada 90 s (más lento).';
  $('#puburl').value = SET.public_url || location.origin;
  $('#dhour').value = SET.daily_hour; $('#tz').value = SET.tz;
  $('#push-msg').textContent = SET.subs ? `Avisos activos en ${SET.subs} dispositivo(s).` : '';
}
$('#w-save').onclick = async () => {
  const ws = $('#w-edit').value.split('\n').map(l => l.trim()).filter(Boolean).map(l => {
    const [name, addr, origin, payers] = l.split('|').map(s => (s || '').trim());
    return {name, addr, origin, payers: (payers || '').split(',').map(s => s.trim()).filter(Boolean)};
  });
  try { const r = await api('/api/wallets', {wallets: ws}); $('#w-msg').textContent = r.webhook?.msg || 'Guardado'; refreshMeta(); }
  catch (e) { $('#w-msg').textContent = e.message; }
};
$('#helius-save').onclick = async () => {
  try { const r = await api('/api/settings', {helius_key: $('#helius').value, public_url: $('#puburl').value}); $('#helius').value = ''; $('#helius-msg').textContent = r.webhook?.msg || 'Guardado'; loadSettings(); }
  catch (e) { $('#helius-msg').textContent = e.message; }
};
$('#gen-save').onclick = async () => {
  try { await api('/api/settings', {daily_hour: +$('#dhour').value, tz: $('#tz').value, new_password: $('#newpw').value}); $('#newpw').value = ''; $('#gen-msg').textContent = 'Guardado'; }
  catch (e) { $('#gen-msg').textContent = e.message; }
};
$('#logout').onclick = async () => { await api('/api/logout', {}); showAuth(false); };

function b64u(s) { const p = '='.repeat((4 - s.length % 4) % 4); const b = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...b].map(c => c.charCodeAt(0))); }
$('#push-on').onclick = async () => {
  try {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) throw new Error('Este navegador no admite avisos. En iPhone, añade la app a la pantalla de inicio y ábrela desde el icono.');
    const perm = await Notification.requestPermission();
    if (perm !== 'granted') throw new Error('Permiso denegado. Actívalo en Ajustes del móvil → Notificaciones.');
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64u(SET.vapid)});
    await api('/api/push/subscribe', sub.toJSON());
    $('#push-msg').textContent = 'Avisos activados en este móvil.';
  } catch (e) { $('#push-msg').textContent = e.message; }
};
$('#push-test').onclick = async () => { try { const r = await api('/api/push/test', {}); $('#push-msg').textContent = r.sent ? `Enviado a ${r.sent} dispositivo(s).` : 'No hay dispositivos con avisos activos.'; } catch (e) { $('#push-msg').textContent = e.message; } };

boot();
