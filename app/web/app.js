const I = {
"home": "<path d=\"M4 14v-2a8 8 0 0 1 16 0v2\"/><rect x=\"2.5\" y=\"13\" width=\"5\" height=\"7.5\" rx=\"2\"/><rect x=\"16.5\" y=\"13\" width=\"5\" height=\"7.5\" rx=\"2\"/>",
"eq": "<path d=\"M6 4v16M12 4v16M18 4v16\"/><circle cx=\"6\" cy=\"15\" r=\"2.4\" fill=\"#0B0E14\"/><circle cx=\"12\" cy=\"8\" r=\"2.4\" fill=\"#0B0E14\"/><circle cx=\"18\" cy=\"13\" r=\"2.4\" fill=\"#0B0E14\"/>",
"game": "<rect x=\"2.5\" y=\"7\" width=\"19\" height=\"11.5\" rx=\"5.5\"/><path d=\"M7.5 10.5v4.5M5.25 12.75h4.5\"/><circle cx=\"15.5\" cy=\"11.5\" r=\"1\" fill=\"currentColor\"/><circle cx=\"18\" cy=\"14\" r=\"1\" fill=\"currentColor\"/>",
"mic": "<rect x=\"9\" y=\"3\" width=\"6\" height=\"11\" rx=\"3\"/><path d=\"M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7\"/>",
"mix": "<path d=\"M4 8h15M15 4.5 19 8l-4 3.5M20 16H5M9 12.5 5 16l4 3.5\"/>",
"fw": "<rect x=\"6\" y=\"6\" width=\"12\" height=\"12\" rx=\"2\"/><path d=\"M9 2.5V6M15 2.5V6M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5M12 15V9M9.8 11.2 12 9l2.2 2.2\"/>",
"tools": "<path d=\"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94z\"/>",
"gear": "<circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z\"/>",
"refresh": "<path d=\"M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7\"/>",
"save": "<path d=\"M5 3h11l3 3v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z\"/><path d=\"M7 3v5h8V3M7 21v-7h10v7\"/>",
"bat": "<rect x=\"2\" y=\"7\" width=\"17\" height=\"10\" rx=\"2.5\"/><path d=\"M22 10.5v3\"/><rect x=\"4.5\" y=\"9.5\" width=\"7\" height=\"5\" rx=\"1\" fill=\"currentColor\" stroke=\"none\"/>",
"bolt": "<path d=\"M13 2 4 14h7l-1 8 9-12h-7z\"/>",
"chevl": "<path d=\"m15 18-6-6 6-6\"/>",
"chevr": "<path d=\"m9 18 6-6-6-6\"/>",
"check": "<path d=\"M20 6 9 17l-5-5\"/>",
"alert": "<path d=\"M12 9v4M12 17h.01\"/><path d=\"M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z\"/>",
"file": "<path d=\"M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z\"/><path d=\"M14 3v6h6\"/>",
"play": "<path d=\"M7 4v16l13-8z\"/>",
"rec": "<circle cx=\"12\" cy=\"12\" r=\"7\"/>",
"plus": "<path d=\"M12 5v14M5 12h14\"/>",
"upload": "<path d=\"M12 15V3M7 8l5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4\"/>",
"download": "<path d=\"M12 3v12M7 10l5 5 5-5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4\"/>",
"heart": "<path d=\"M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z\"/>",
"wave": "<path d=\"M2 12h3l3-8 4 16 3-10 2 2h5\"/>",
"users": "<circle cx=\"9\" cy=\"8\" r=\"3.5\"/><path d=\"M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5\"/>",
"moon": "<path d=\"M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z\"/>",
"radio": "<circle cx=\"12\" cy=\"12\" r=\"2\"/><path d=\"M16.2 7.8a6 6 0 0 1 0 8.4M7.8 16.2a6 6 0 0 1 0-8.4M19 5a10 10 0 0 1 0 14M5 19A10 10 0 0 1 5 5\"/>",
"shield": "<path d=\"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z\"/>",
"speaker": "<path d=\"M11 5 6 9H2v6h4l5 4z\"/><path d=\"M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14\"/>",
"keyboard": "<rect x=\"2\" y=\"6\" width=\"20\" height=\"12\" rx=\"2\"/><path d=\"M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10\"/>",
"palette": "<circle cx=\"13.5\" cy=\"6.5\" r=\"1\" fill=\"currentColor\"/><circle cx=\"17.5\" cy=\"10.5\" r=\"1\" fill=\"currentColor\"/><circle cx=\"8.5\" cy=\"7.5\" r=\"1\" fill=\"currentColor\"/><circle cx=\"6.5\" cy=\"12.5\" r=\"1\" fill=\"currentColor\"/><path d=\"M12 2a10 10 0 0 0 0 20c1 0 1.7-.8 1.7-1.7 0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1 0-.9.8-1.7 1.7-1.7H17a5 5 0 0 0 5-5C22 6.5 17.5 2 12 2z\"/>",
"terminal": "<path d=\"m4 17 6-6-6-6M12 19h8\"/>",
"hdd": "<path d=\"M22 12H2M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z\"/><path d=\"M6 16h.01M10 16h.01\"/>",
"trash": "<path d=\"M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14\"/>",
"x": "<path d=\"M18 6 6 18M6 6l12 12\"/>",
"stop": "<rect x=\"6\" y=\"6\" width=\"12\" height=\"12\" rx=\"2\"/>",
"ext": "<path d=\"M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5\"/>",
"edit": "<path d=\"M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z\"/>",
"folder": "<path d=\"M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z\"/>"
};

/* A50 Control - window logic. Talks only to the local bridge (a50_web.py) on 127.0.0.1. */
'use strict';

// ======================================================================= small helpers
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ic(name, size = 20, color = 'currentColor', sw = 1.8) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none">${I[name] || ''}</svg>`;
}
function h(html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; }
const signed = g => (g > 0 ? '+' : '') + g;

async function api(name, body = {}) {
  let r;
  try {
    r = await fetch('/api/' + name, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Token': window.A50_TOKEN }, body: JSON.stringify(body) });
  } catch (e) { throw new Error('A50 Control is not running (the window lost its connection).'); }
  const j = await r.json().catch(() => ({ ok: false, error: 'Bad answer from the app' }));
  if (!j.ok) throw new Error(j.error || 'Error');
  return j.data;
}
async function act(fn, okMsg) {
  try { const r = await fn(); if (okMsg) toast(okMsg, 'ok'); return r; }
  catch (e) { toast(e.message, 'err'); return undefined; }
}
function toast(msg, kind = '') {
  const el = h(`<div class="toast ${kind}">${ic(kind === 'err' ? 'alert' : kind === 'ok' ? 'check' : 'radio', 18, kind === 'err' ? '#FF8A95' : kind === 'ok' ? '#5BE6A9' : 'var(--acc)')}<div>${esc(msg)}</div></div>`);
  $('#toasts').appendChild(el);
  setTimeout(() => { el.style.transition = 'opacity .3s'; el.style.opacity = '0'; setTimeout(() => el.remove(), 320); }, kind === 'err' ? 6500 : 3200);
}
function modal(title, text, buttons) {
  return new Promise(res => {
    const card = $('#modal-card');
    card.innerHTML = `<div class="ct"><span class="k">${esc(title)}</span></div><div class="soft" style="white-space:pre-line;margin-bottom:20px">${text}</div><div class="row" style="justify-content:flex-end" id="mbtns"></div>`;
    buttons.forEach(([label, val, cls]) => {
      const b = h(`<button class="btn ${cls || ''}" type="button">${esc(label)}</button>`);
      b.onclick = () => { $('#modal').classList.remove('on'); res(val); };
      $('#mbtns', card).appendChild(b);
    });
    $('#modal').classList.add('on');
  });
}
const confirmBox = (title, text, ok = 'Continue', danger = false) => modal(title, text, [['Cancel', false], [ok, true, danger ? 'btn-d' : 'btn-p']]);
function prompt2(title, label, value = '') {
  return new Promise(res => {
    const card = $('#modal-card');
    card.innerHTML = `<div class="ct"><span class="k">${esc(title)}</span></div><div class="soft small" style="margin-bottom:8px">${esc(label)}</div><input class="field" style="width:100%" maxlength="40" id="mp-in"><div class="row" style="justify-content:flex-end;margin-top:20px"><button class="btn" type="button" id="mp-c">Cancel</button><button class="btn btn-p" type="button" id="mp-o">OK</button></div>`;
    const inp = $('#mp-in'); inp.value = value;
    const done = v => { $('#modal').classList.remove('on'); res(v); };
    $('#mp-c').onclick = () => done(null);
    $('#mp-o').onclick = () => done(inp.value.trim() || null);
    inp.onkeydown = e => { if (e.key === 'Enter') done(inp.value.trim() || null); if (e.key === 'Escape') done(null); };
    $('#modal').classList.add('on'); setTimeout(() => inp.select(), 30);
  });
}
function download(name, text, type = 'application/json') {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name; document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
function pickFile(accept, mode = 'text') {
  return new Promise(res => {
    const inp = $('#file-in');
    inp.value = ''; inp.accept = accept;
    inp.onchange = () => {
      const f = inp.files[0]; if (!f) return res(null);
      const rd = new FileReader();
      rd.onload = () => res({ name: f.name, data: mode === 'text' ? rd.result : String(rd.result).split(',')[1] });
      rd.onerror = () => res(null);
      mode === 'text' ? rd.readAsText(f) : rd.readAsDataURL(f);
    };
    inp.click();
  });
}

// ======================================================================= colours
function hexToRgb(hex) { const m = /^#?([0-9a-f]{6})$/i.exec(hex || ''); if (!m) return [0, 180, 255]; const n = parseInt(m[1], 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
const rgbToHex = (r, g, b) => '#' + [r, g, b].map(v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const mixHex = (a, b, t) => { const x = hexToRgb(a), y = hexToRgb(b); return rgbToHex(...x.map((v, i) => v + (y[i] - v) * t)); };
function hsvToHex(hh, s, v) {
  const f = n => { const k = (n + hh / 60) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
  return rgbToHex(f(5) * 255, f(3) * 255, f(1) * 255);
}
function hexToHsv(hex) {
  const [r, g, b] = hexToRgb(hex).map(x => x / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let hh = 0;
  if (d) hh = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(hh * 60 + 360) % 360, mx ? d / mx : 0, mx];
}
function applyColors(c) {
  const st = document.documentElement.style, a = c.app || '#00B4FF';
  st.setProperty('--acc', a);
  st.setProperty('--acc-hi', mixHex(a, '#FFFFFF', .3));
  st.setProperty('--acc-lo', mixHex(a, '#000000', .18));
  st.setProperty('--acc-tx', mixHex(a, '#FFFFFF', .5));
  st.setProperty('--accr', hexToRgb(a).join(','));
  st.setProperty('--hacc', c.hacc || a);
  st.setProperty('--shell', c.shell || '#1C2029');
  st.setProperty('--cush', c.cush || '#0D0F14');
}

// ======================================================================= components
function slider(host, o) {
  // o: {label, icon, min, max, value, suffix, fmt, onChange(v), disabled}
  const el = h(`<div class="sl"><div class="sll">${o.icon ? ic(o.icon, 18, '#8E98AA') : ''}<span>${esc(o.label)}</span></div>
    <div class="track"><div class="fill"></div><div class="thumb"></div></div><div class="slv"></div></div>`);
  host.appendChild(el);
  const tr = $('.track', el), fill = $('.fill', el), th = $('.thumb', el), lab = $('.slv', el);
  const min = o.min ?? 0, max = o.max ?? 100;
  let v = o.value ?? min, dragging = false, known = o.value !== undefined && o.value !== null;
  const fmt = o.fmt || (x => x + (o.suffix || ''));
  const draw = () => {
    const p = (v - min) / (max - min) * 100;
    fill.style.width = (o.center ? 0 : p) + '%'; th.style.left = p + '%';
    if (o.center) { const c = 50; fill.style.left = Math.min(p, c) + '%'; fill.style.width = Math.abs(p - c) + '%'; }
    lab.textContent = known ? fmt(v) : '–';
  };
  const fromX = x => { const r = tr.getBoundingClientRect(); return Math.round(min + clamp((x - r.left) / r.width, 0, 1) * (max - min)); };
  tr.addEventListener('pointerdown', e => { dragging = true; known = true; tr.classList.add('drag'); tr.setPointerCapture(e.pointerId); v = fromX(e.clientX); draw(); });
  tr.addEventListener('pointermove', e => { if (dragging) { v = fromX(e.clientX); draw(); o.onInput && o.onInput(v); } });
  const end = () => { if (!dragging) return; dragging = false; tr.classList.remove('drag'); o.onChange && o.onChange(v); };
  tr.addEventListener('pointerup', end); tr.addEventListener('pointercancel', end);
  tr.tabIndex = 0;
  tr.addEventListener('keydown', e => {
    const step = e.shiftKey ? 10 : 1;
    if (['ArrowLeft', 'ArrowDown'].includes(e.key)) v = clamp(v - step, min, max);
    else if (['ArrowRight', 'ArrowUp'].includes(e.key)) v = clamp(v + step, min, max);
    else return;
    e.preventDefault(); known = true; draw(); clearTimeout(tr._t); tr._t = setTimeout(() => o.onChange && o.onChange(v), 350);
  });
  draw();
  const api_ = {
    set(x) { if (dragging) return; if (x === null || x === undefined) { known = false; } else { known = true; v = clamp(Number(x), min, max); } draw(); },
    get: () => v, el,
    disable(d) { tr.classList.toggle('dis', !!d); }
  };
  if (o.disabled) api_.disable(true);
  return api_;
}

function eqGraph(host, o) {
  // o: {gains, labels, range, onInput(gains), onChange(gains), height, uid}
  const W = 900, H = o.height || 300, L = 56, R = W - 24, T = 30, B = H - 40, rng = o.range;
  let gains = o.gains.slice(), labels = o.labels.slice(), drag = -1;
  const n = () => gains.length;
  const X = i => L + (R - L) * (i + .5) / n();
  const Y = g => T + (rng - g) / (2 * rng) * (B - T);
  const svg = h(`<svg class="eqg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Equalizer curve: drag the points up and down"></svg>`);
  host.appendChild(svg);
  const u = o.uid || ('eq' + Math.random().toString(36).slice(2, 7));
  function path() {
    const pts = gains.map((g, i) => [X(i), Y(g)]);
    const all = [[L, pts[0][1]], ...pts, [R, pts[pts.length - 1][1]]];
    let d = `M${all[0][0].toFixed(1)},${all[0][1].toFixed(1)}`;
    for (let i = 1; i < all.length; i++) { const [x0, y0] = all[i - 1], [x1, y1] = all[i], cx = (x0 + x1) / 2; d += ` C${cx.toFixed(1)},${y0.toFixed(1)} ${cx.toFixed(1)},${y1.toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`; }
    return d;
  }
  function draw() {
    const half = Math.round(rng / 2);
    let g = '';
    for (const v of [rng, half, 0, -half, -rng]) {
      const y = Y(v);
      g += `<line x1="${L}" x2="${R}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,${v === 0 ? .12 : .05})" ${v === 0 ? '' : 'stroke-dasharray="3 6"'}/>`;
      g += `<text x="${L - 12}" y="${y + 4}" text-anchor="end" fill="#6F7A8C" font-size="11">${v ? signed(v) : 0}${Math.abs(v) === rng ? ' dB' : ''}</text>`;
    }
    gains.forEach((_, i) => { g += `<line x1="${X(i)}" x2="${X(i)}" y1="${T}" y2="${B}" stroke="rgba(255,255,255,.035)"/>`; });
    const d = path(), area = d + ` L${R},${B} L${L},${B} Z`;
    let nodes = '';
    const small = n() > 6, r = small ? 6.5 : 8;
    gains.forEach((v, i) => {
      const x = X(i), y = Y(v);
      nodes += `<g class="node${drag === i ? ' drag' : ''}" data-i="${i}"><circle cx="${x}" cy="${y}" r="${r + 14}" fill="transparent"/><circle cx="${x}" cy="${y}" r="${r + 8}" fill="url(#halo${u})"/>
        <circle class="nr" cx="${x}" cy="${y}" r="${r}" fill="#0B0F17" stroke="var(--acc-hi)" stroke-width="3"/></g>
        <text x="${x}" y="${y - 18}" text-anchor="middle" fill="#E8EAEE" font-size="12" font-weight="700" pointer-events="none">${signed(v)}</text>
        <text x="${x}" y="${B + 24}" text-anchor="middle" fill="#8E98AA" font-size="${small ? 11 : 12}" pointer-events="none">${esc(labels[i] || '')}</text>`;
    });
    svg.innerHTML = `<defs><linearGradient id="ar${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--acc)" stop-opacity=".38"/><stop offset="1" stop-color="var(--acc)" stop-opacity="0"/></linearGradient>
      <linearGradient id="ln${u}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7C5CFF"/><stop offset=".5" stop-color="var(--acc)"/><stop offset="1" stop-color="var(--acc-hi)"/></linearGradient>
      <radialGradient id="halo${u}"><stop offset="0" stop-color="var(--acc)" stop-opacity=".45"/><stop offset="1" stop-color="var(--acc)" stop-opacity="0"/></radialGradient>
      <filter id="gl${u}" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="5"/></filter></defs>
      ${g}<path d="${area}" fill="url(#ar${u})"/><path d="${d}" fill="none" stroke="url(#ln${u})" stroke-width="7" opacity=".45" filter="url(#gl${u})"/>
      <path d="${d}" fill="none" stroke="url(#ln${u})" stroke-width="3"/>${nodes}`;
  }
  const toG = e => { const r = svg.getBoundingClientRect(); const y = (e.clientY - r.top) / r.height * H; return clamp(Math.round(rng - (y - T) / (B - T) * 2 * rng), -rng, rng); };
  svg.addEventListener('pointerdown', e => {
    const nd = e.target.closest('.node');
    let i;
    if (nd) i = +nd.dataset.i;
    else { const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * W; i = clamp(Math.floor((x - L) / ((R - L) / n())), 0, n() - 1); }
    drag = i; svg.setPointerCapture(e.pointerId); gains[i] = toG(e); draw(); o.onInput && o.onInput(gains.slice());
  });
  svg.addEventListener('pointermove', e => { if (drag < 0) return; const g = toG(e); if (g !== gains[drag]) { gains[drag] = g; draw(); o.onInput && o.onInput(gains.slice()); } });
  const end = () => { if (drag < 0) return; drag = -1; draw(); o.onChange && o.onChange(gains.slice()); };
  svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end);
  draw();
  return { set(gs, ls) { if (drag >= 0) return; gains = gs.slice(); if (ls) labels = ls.slice(); draw(); }, get: () => gains.slice(), el: svg };
}

function miniCurve(gains, rng = 7, w = 160, hgt = 44) {
  const n = gains.length, X = i => 6 + (w - 12) * (i + .5) / n, Y = g => 6 + (rng - g) / (2 * rng) * (hgt - 12);
  const pts = gains.map((g, i) => [X(i), Y(g)]), all = [[0, pts[0][1]], ...pts, [w, pts[n - 1][1]]];
  let d = `M${all[0][0]},${all[0][1]}`;
  for (let i = 1; i < all.length; i++) { const [x0, y0] = all[i - 1], [x1, y1] = all[i], cx = (x0 + x1) / 2; d += ` C${cx},${y0} ${cx},${y1} ${x1},${y1}`; }
  return `<svg viewBox="0 0 ${w} ${hgt}" width="100%" height="${hgt}" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="${w}" y1="${hgt / 2}" y2="${hgt / 2}" stroke="rgba(255,255,255,.08)"/><path d="${d}" fill="none" stroke="var(--acc)" stroke-width="2.2" vector-effect="non-scaling-stroke"/></svg>`;
}

function seg(host, items, active, onPick) {
  const el = h(`<div class="seg" role="group"></div>`);
  items.forEach(([label, val]) => {
    const b = h(`<button type="button">${esc(label)}</button>`);
    b.dataset.v = String(val);
    b.onclick = () => { set(val); onPick(val); };
    el.appendChild(b);
  });
  const set = v => $$('button', el).forEach(b => b.classList.toggle('on', b.dataset.v === String(v)));
  set(active); host.appendChild(el);
  return { set, el };
}

function swBtn(on, onToggle) {
  const b = h(`<button type="button" class="sw${on ? '' : ' off'}" role="switch" aria-checked="${on}"></button>`);
  b.onclick = async () => {
    const nv = b.classList.contains('off');
    const r = await onToggle(nv);
    if (r !== false) { b.classList.toggle('off', !nv); b.setAttribute('aria-checked', String(nv)); }
  };
  b.setOn = v => { b.classList.toggle('off', !v); b.setAttribute('aria-checked', String(!!v)); };
  return b;
}

function colorPicker(host, o) {
  // o: {label, desc, value, onInput(hex), onChange(hex), quick:[hex]}
  const el = h(`<div class="cpi"><div class="row sp"><div class="col"><span style="font-weight:600">${esc(o.label)}</span><span class="small muted">${esc(o.desc || '')}</span></div>
    <span class="swatch" style="width:30px;height:30px"></span></div>
    <div class="sv"><div class="cur"></div></div><div class="hue"><div class="cur"></div></div>
    <div class="row" style="margin-top:12px;gap:8px"><input class="field" style="width:110px;height:34px;font-family:Consolas,monospace" maxlength="7" spellcheck="false"><div class="cpq"></div></div></div>`);
  host.appendChild(el);
  const sv = $('.sv', el), hue = $('.hue', el), inp = $('input', el), sw = $('.swatch', el);
  let [H_, S_, V_] = hexToHsv(o.value), t;
  const hex = () => hsvToHex(H_, S_, V_);
  function draw(skipInput) {
    sv.style.backgroundColor = hsvToHex(H_, 1, 1);
    $('.cur', sv).style.left = S_ * 100 + '%'; $('.cur', sv).style.top = (1 - V_) * 100 + '%';
    $('.cur', hue).style.left = H_ / 360 * 100 + '%';
    sw.style.background = hex(); if (!skipInput) inp.value = hex();
  }
  const emit = () => { o.onInput && o.onInput(hex()); clearTimeout(t); t = setTimeout(() => o.onChange && o.onChange(hex()), 400); };
  const dragOn = (area, fn) => {
    let on = false;
    area.addEventListener('pointerdown', e => { on = true; area.setPointerCapture(e.pointerId); fn(e); });
    area.addEventListener('pointermove', e => on && fn(e));
    area.addEventListener('pointerup', () => { on = false; });
  };
  dragOn(sv, e => { const r = sv.getBoundingClientRect(); S_ = clamp((e.clientX - r.left) / r.width, 0, 1); V_ = 1 - clamp((e.clientY - r.top) / r.height, 0, 1); draw(); emit(); });
  dragOn(hue, e => { const r = hue.getBoundingClientRect(); H_ = clamp((e.clientX - r.left) / r.width, 0, .9999) * 360; draw(); emit(); });
  inp.addEventListener('input', () => { const v = inp.value.trim(); if (/^#?[0-9a-f]{6}$/i.test(v)) { [H_, S_, V_] = hexToHsv(v.startsWith('#') ? v : '#' + v); draw(true); emit(); } });
  (o.quick || []).forEach(q => { const b = h(`<button type="button" title="${q}" style="background:${q}"></button>`); b.onclick = () => { [H_, S_, V_] = hexToHsv(q); draw(); emit(); }; $('.cpq', el).appendChild(b); });
  draw();
  return { set(v) { [H_, S_, V_] = hexToHsv(v); draw(); } };
}

// ======================================================================= app state
const S = { quick: {}, full: null, info: null, page: 'home', fullAt: 0, loadingFull: false, svg: null };
const PAGES = [
  ['home', 'Home', 'home'], ['eq', 'Equalizer', 'eq'], ['profiles', 'Profiles', 'game'], ['mic', 'Microphone', 'mic'],
  ['mix', 'Mix', 'mix'], ['firmware', 'Firmware', 'fw'], ['maint', 'Maintenance', 'tools']];
const P = {};          // page objects: {el, built, build(), update()}
const GATES = ['Streaming', 'Night', 'Home', 'Tournament'];
const EQ_DEFAULT_LABELS = ['Bass', 'Low mids', 'Mids', 'High mids', 'Treble'];

function title(icon, text, sub) {
  return `<div class="title"><div class="title-ic">${ic(icon, 26, 'currentColor', 1.9)}</div><div><h1 class="h">${esc(text)}</h1><p>${esc(sub)}</p></div></div>`;
}
const ct = (text, right = '') => `<div class="ct"><span class="k">${esc(text)}</span>${right}</div>`;
const fmtFreq = f => f == null ? null : f >= 1000 ? (f / 1000).toFixed(f % 1000 ? 1 : 0) + ' kHz' : f + ' Hz';
const connected = () => !!S.quick.connected && !S.quick.busy;
function needDev() { if (!connected()) { toast(S.quick.busy ? 'Wait: a firmware or repair job is running.' : 'Base station not connected.', 'err'); return false; } return true; }
function eqLabels() { const f = S.full && S.full.freqs; return EQ_DEFAULT_LABELS.map((d, i) => (f && fmtFreq(f[i])) || d); }

function show(id) {
  if (!P[id]) id = 'home';
  S.page = id;
  $$('.nav a').forEach(a => a.classList.toggle('on', a.dataset.p === id));
  $$('.page').forEach(p => p.classList.toggle('on', p.id === 'pg-' + id));
  const pg = P[id];
  if (!pg.built) { pg.built = true; pg.build(); }
  pg.update && pg.update();
  pg.enter && pg.enter();
  $('#main').scrollTop = 0;
}

async function loadFull(quiet) {
  if (S.loadingFull) return;
  S.loadingFull = true;
  try {
    S.full = await api('full'); S.fullAt = Date.now();
    Object.values(P).forEach(p => p.built && p.update && p.update());
  } catch (e) { if (!quiet) toast(e.message, 'err'); }
  finally { S.loadingFull = false; }
}

// ======================================================================= chrome (sidebar, header, banner)
function updateChrome() {
  const q = S.quick, chip = $('#conn-chip'), bat = $('#bat-chip');
  let txt, dot;
  if (q.busy) { txt = 'Job running'; dot = 'warn'; }
  else if (q.connected) { txt = q.on === false ? 'Base connected · headset off' : 'Connected'; dot = q.on === false ? 'warn' : ''; }
  else { txt = 'Not connected'; dot = 'off'; }
  chip.innerHTML = `<span class="dot ${dot}"></span><span style="color:${dot === '' ? '#7FEBBE' : dot === 'warn' ? '#FFC170' : 'var(--muted)'}">${txt}</span>`;
  const has = q.battery != null && q.on !== false;
  bat.hidden = !has;
  if (has) bat.innerHTML = `${ic(q.charging ? 'bolt' : 'bat', 18, q.battery <= 15 && !q.charging ? '#FF8A95' : 'var(--acc-tx)')}<span>${q.battery}%</span>`;
  const auto = q.auto || {};
  $('#auto-chip').hidden = !(auto.on && auto.active);
  if (auto.on && auto.active) $('#auto-chip').innerHTML = `${ic('game', 18, 'var(--acc-tx)')}<span>${esc(auto.active)}</span>`;
  $('#mini-dot').className = 'dot ' + (has ? (q.battery <= 15 && !q.charging ? 'warn' : '') : 'off');
  $('#mini-pct').textContent = has ? q.battery + '%' : '–';
  $('#mini-fill').style.width = (has ? q.battery : 0) + '%';
  $('#mini-txt').textContent = !q.connected ? (q.busy ? 'Job running…' : 'Not connected')
    : !has ? 'Headset off' : (q.charging ? 'Charging' : (q.docked ? 'On the base' : 'Wireless')) + (q.estimate ? ' · ' + q.estimate.replace('≈ ', '≈ ') : '');
  const bn = $('#banner');
  if (!q.connected && !q.busy) {
    bn.classList.remove('hide');
    bn.innerHTML = q.acc
      ? `${ic('alert', 22, '#FFC170')}<div class="grow"><b>ASTRO Command Center is open.</b><div class="small soft">It keeps the base station busy. Close it (also from the tray), then press Reconnect.</div></div><button class="btn sm" id="bn-r">${ic('refresh', 14)}Reconnect</button>`
      : `${ic('radio', 22, '#FFC170')}<div class="grow"><b>Base station not found.</b><div class="small soft">Connect the base to the PC with the USB cable (PC mode). The app keeps looking every few seconds.</div></div><button class="btn sm" id="bn-r">${ic('refresh', 14)}Reconnect</button>`;
    $('#bn-r').onclick = reconnect;
  } else bn.classList.add('hide');
  $('#btn-save').disabled = !connected();
}

async function reconnect() {
  const q = await act(() => api('reconnect'));
  if (q) { S.quick = q; updateChrome(); if (q.connected) { await loadFull(); toast('Connected', 'ok'); } else toast('Base station not found', 'err'); }
}

let pollN = 0, wasConnected = false;
async function poll() {
  try {
    S.quick = await api('state');
    updateChrome();
    if (connected() && (!wasConnected || !S.full || Date.now() - S.fullAt > 30000)) await loadFull(true);
    if (!S.quick.connected && wasConnected) Object.values(P).forEach(p => p.built && p.update && p.update());
    wasConnected = connected();
    if (S.full) {
      if (S.quick.preset && S.full.active !== S.quick.preset) await loadFull(true);
      Object.assign(S.full, { battery: S.quick.battery, charging: S.quick.charging, estimate: S.quick.estimate, docked: S.quick.docked, on: S.quick.on });
    }
    P.home.built && P.home.update();
    if (S.page === 'home' && pollN++ % 12 === 0) P.home.history();
  } catch (e) {
    $('#conn-chip').innerHTML = `<span class="dot off"></span><span class="muted">App closed</span>`;
  }
  setTimeout(poll, S.quick.busy ? 1500 : 2500);
}

// ======================================================================= HOME
P.home = {
  build() {
    const el = this.el;
    el.innerHTML = title('home', 'Home', 'Status of your headset at a glance.') + `
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
      <section class="card hero">
        <div class="halo"></div><div class="ring"></div>
        <div class="row sp wrap" style="position:relative">
          <span class="badge acc" id="h-where">${ic('radio', 14)}Wireless</span>
          <span class="badge" id="h-mic" title="Click the headset to preview the boom up / down">${ic('mic', 13)}Mic boom</span>
          <span class="badge" id="h-health">${ic('check', 14)}Radio chips</span></div>
        <div class="hs-wrap" id="h-svg" title="Click to preview the microphone boom raised (muted) or lowered (live)"></div>
        <div class="row wrap" style="justify-content:center;gap:14px;position:relative">
          <div class="row" style="gap:8px"><span class="swatch" title="Shell" style="background:var(--shell)"></span><span class="swatch" title="Lights" style="background:var(--hacc);box-shadow:0 0 10px var(--hacc)"></span><span class="swatch" title="Cushions" style="background:var(--cush)"></span></div>
          <div><div class="h" style="font-size:16px;font-weight:700">Your colours</div><div class="small muted">Shell · lights · cushions</div></div>
          <button class="btn" type="button" id="h-cust">${ic('palette', 16)}Customize</button></div>
      </section>
      <div class="col" style="gap:22px">
        <section class="card" style="margin:0">${ct('Battery', '<span class="badge" id="h-chg"></span>')}
          <div class="row" style="gap:20px">
            <svg width="118" height="118" viewBox="0 0 120 120" class="ring-bat" role="img" aria-label="Battery">
              <defs><linearGradient id="ringg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="var(--acc-hi)"/><stop offset="1" stop-color="var(--acc-lo)"/></linearGradient><filter id="rgf"><feGaussianBlur stdDeviation="3"/></filter></defs>
              <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="10"/>
              <circle class="fg" cx="60" cy="60" r="48" fill="none" stroke="var(--acc)" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 302" transform="rotate(-90 60 60)" opacity=".6" filter="url(#rgf)"/>
              <circle class="fg" cx="60" cy="60" r="48" fill="none" stroke="url(#ringg)" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 302" transform="rotate(-90 60 60)"/>
              <text x="60" y="68" text-anchor="middle" fill="#fff" font-family="Bahnschrift,Segoe UI" font-size="28" font-weight="700" id="h-pct">–</text></svg>
            <div class="col" style="gap:4px"><div class="h" style="font-size:20px;font-weight:700" id="h-est">–</div><div class="small soft" id="h-est2"></div><div class="small muted" style="margin-top:6px" id="h-typ"></div></div>
          </div></section>
        <section class="card" style="margin:0">${ct('Headset')}
          <div class="row" style="gap:12px;align-items:stretch">
            <div class="tile static grow">${ic('radio', 20, 'var(--acc)')}<span class="tn" id="h-t1">–</span><span class="td" id="h-t1d"></span></div>
            <div class="tile static grow">${ic('speaker', 20, '#3DDC97')}<span class="tn" id="h-t2">–</span><span class="td" id="h-t2d">Power</span></div></div></section>
        <section class="card" style="margin:0">${ct('Base station', '<a href="#" class="small" id="h-toeq" style="font-weight:600;text-decoration:none">Open equalizer</a>')}
          <div class="row" style="gap:12px;align-items:stretch">
            <div class="tile static grow">${ic('eq', 20, 'var(--acc)')}<span class="tn" id="h-pn">–</span><span class="td" id="h-pi">EQ preset</span></div>
            <div class="tile static grow">${ic('speaker', 20, '#C9CFD9')}<span class="tn">Dolby</span><span class="td">Not readable yet (LED left off)</span></div></div></section>
      <section class="card" style="margin:0">${ct('Firmware', '<a href="#" class="small" id="h-tofw" style="font-weight:600;text-decoration:none">Check for update</a>')}
        <div style="display:grid;grid-template-columns:1fr auto;gap:10px;font-size:13px" id="h-fw"></div></section>
      </div>

      <section class="card" style="grid-column:1/-1">${ct('Battery history · 24 h', '<span class="legend"><span><i style="background:var(--acc)"></i>In use</span><span><i style="background:var(--ok)"></i>Charging</span></span>')}
        <div id="h-chart"></div></section>
    </div>`;
    fetch('headset.svg').then(r => r.text()).then(t => { $('#h-svg').innerHTML = t; S.svg = $('#h-svg svg'); this.update(); });
    $('#h-svg').onclick = () => { if (S.svg) { S.svg.classList.toggle('muted'); this.update(); } };
    $('#h-cust').onclick = () => show('settings');
    $('#h-toeq').onclick = e => { e.preventDefault(); show('eq'); };
    $('#h-tofw').onclick = e => { e.preventDefault(); show('firmware'); };
    this.history();
  },
  update() {
    if (!this.built) return;
    const q = S.quick, f = S.full || {}, has = q.connected && q.battery != null && q.on !== false;
    const pct = has ? q.battery : 0, dash = (pct / 100 * 301.6).toFixed(1);
    $$('.ring-bat .fg', this.el).forEach(c => c.setAttribute('stroke-dasharray', `${dash} 302`));
    $('#h-pct').textContent = has ? pct + '%' : '–';
    $('#h-chg').className = 'badge ' + (has ? (q.charging ? 'ok' : pct <= 15 ? 'bad' : '') : '');
    $('#h-chg').innerHTML = has ? (q.charging ? ic('bolt', 13) + 'Charging' : 'Not charging') : 'Unknown';
    $('#h-est').textContent = has ? (q.estimate ? q.estimate.replace(/^≈ /, '≈ ').replace(/ (left|to full)$/, '') : (q.charging ? 'Charging' : pct + '% left')) : (q.connected ? 'Headset off' : 'Not connected');
    $('#h-est2').textContent = has && q.estimate ? (q.charging ? 'to full charge' : 'left at this pace') : (has ? 'Estimate after ~15 minutes of use' : '');
    $('#h-typ').textContent = this.typ ? `Typical full charge ≈ ${Math.round(this.typ)} h` : '';
    $('#h-t1').textContent = !q.connected ? '–' : q.docked ? 'On the base' : 'Wireless';
    $('#h-t1d').textContent = !q.connected ? 'Not connected' : q.docked ? 'Docked and charging' : 'Off the base';
    $('#h-t2').textContent = !q.connected ? '–' : q.on ? 'On' : 'Off';
    $('#h-t2d').textContent = q.connected && q.on === false ? 'Turn it on to change settings' : 'Power';
    const pr = f.presets && f.presets[(f.active || 1) - 1];
    $('#h-pn').textContent = q.connected && pr ? pr.name : '–';
    $('#h-pi').textContent = q.connected && f.active ? `EQ preset ${f.active} of 3` : 'EQ preset';
    const w = $('#h-where');
    w.innerHTML = ic(q.docked ? 'bolt' : 'radio', 14) + (!q.connected ? 'Not connected' : q.docked ? 'On the base' : 'Wireless · 2.4 GHz');
    const hl = $('#h-health');
    if (q.connected && S.full) { hl.className = 'badge ' + (f.healthy ? 'ok' : 'warn'); hl.innerHTML = f.healthy ? ic('check', 14, 'currentColor', 2.4) + 'Radio chips healthy' : ic('alert', 14) + 'Radio chip needs repair'; }
    else { hl.className = 'badge'; hl.innerHTML = ic('radio', 14) + 'Waiting for the base'; }
    const muted = S.svg && S.svg.classList.contains('muted'), mb = $('#h-mic');
    mb.style.color = muted ? '#FF8A93' : '#7FEBBE';
    mb.innerHTML = ic('mic', 13) + (muted ? 'Boom up · muted (preview)' : 'Boom down · live (preview)');
    const fw = $('#h-fw');
    if (q.connected && S.full) {
      fw.innerHTML = `<div class="muted">Base processor</div><div class="h" style="text-align:right;font-weight:600">${f.base.major ?? '–'}</div>
        <div class="muted">Base radio chip</div><div class="h" style="text-align:right;font-weight:600">${f.base.radio ?? '–'}</div>
        <div class="muted">Headset processor</div><div class="h" style="text-align:right;font-weight:600">${f.headset.mcu ?? '–'}</div>
        <div class="muted">Headset radio chip</div><div class="h" style="text-align:right;font-weight:600">${f.headset.radio ?? '–'}</div>`;
    } else fw.innerHTML = `<div class="muted">Connect the base station to read the versions.</div><div></div>`;
    if (S.svg) {
      $$('.led', S.svg).forEach(l => l.classList.remove('on', 'low'));
      if (q.connected) {
        const a = f.active || q.preset; if (a) $(`[data-led="p${a}"]`, S.svg)?.classList.add('on');
        if (has) [12, 37, 62, 87].forEach((t, i) => { const b = $(`[data-led="b${i + 1}"]`, S.svg); if (pct >= t || (i === 0 && pct > 0)) b.classList.add(pct <= 15 && !q.charging ? 'low' : 'on'); });
      }
    }
  },
  async history() {
    const d = await api('battery_history').catch(() => null);
    if (!d || !this.built) return;
    this.typ = d.typical;
    const W = 1000, H = 190, L = 40, R = W - 10, T = 12, B = H - 28, t0 = d.now - 86400;
    const X = t => L + (t - t0) / 86400 * (R - L), Y = p => T + (100 - p) / 100 * (B - T);
    let g = '';
    for (const p of [0, 50, 100]) g += `<line x1="${L}" x2="${R}" y1="${Y(p)}" y2="${Y(p)}" stroke="rgba(255,255,255,.06)" ${p ? 'stroke-dasharray="3 6"' : ''}/><text x="${L - 8}" y="${Y(p) + 4}" fill="#6F7A8C" font-size="11" text-anchor="end">${p}%</text>`;
    for (let i = 0; i <= 6; i++) { const t = t0 + i * 14400, dt = new Date(t * 1000); g += `<text x="${X(t)}" y="${H - 6}" fill="#6F7A8C" font-size="11" text-anchor="middle">${i === 6 ? 'now' : String(dt.getHours()).padStart(2, '0') + ':00'}</text>`; }
    let body = '';
    const rows = d.rows.slice();
    if (!rows.length && S.quick.battery != null) rows.push([d.now - 60, S.quick.battery, !!S.quick.charging]);
    if (rows.length) {
      // the reading before the window starts holds until the first change
      const pts = rows.map(r => [Math.max(r[0], t0), r[1], r[2]]);
      pts.push([d.now, pts[pts.length - 1][1], pts[pts.length - 1][2]]);
      let area = `M${X(pts[0][0])},${B}`;
      for (let i = 0; i < pts.length; i++) {
        const [t, p, ch] = pts[i];
        area += ` L${X(t)},${Y(p)}`;
        if (i + 1 < pts.length) {
          const nx = pts[i + 1][0];
          area += ` L${X(nx)},${Y(p)}`;
          body += `<path d="M${X(t)},${Y(p)} L${X(nx)},${Y(p)}" stroke="${ch ? 'var(--ok)' : 'var(--acc)'}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
          if (pts[i + 1][1] !== p) body += `<path d="M${X(nx)},${Y(p)} L${X(nx)},${Y(pts[i + 1][1])}" stroke="${pts[i + 1][2] ? 'var(--ok)' : 'var(--acc)'}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
        }
      }
      area += ` L${X(d.now)},${B} Z`;
      body = `<path d="${area}" fill="url(#bhg)"/>` + body;
      const last = pts[pts.length - 1];
      body += `<circle cx="${X(last[0])}" cy="${Y(last[1])}" r="5" fill="#0B0F17" stroke="${last[2] ? 'var(--ok)' : 'var(--acc)'}" stroke-width="3"/>`;
    } else body = `<text x="${(L + R) / 2}" y="${(T + B) / 2}" fill="#6F7A8C" font-size="13" text-anchor="middle">No readings yet: the history fills in while the app runs.</text>`;
    $('#h-chart').innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Battery level over the last 24 hours"><defs><linearGradient id="bhg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--acc)" stop-opacity=".25"/><stop offset="1" stop-color="var(--acc)" stop-opacity="0"/></linearGradient></defs>${g}${body}</svg>`;
    this.update();
  }
};

// ======================================================================= EQUALIZER
P.eq = {
  build() {
    this.el.innerHTML = title('eq', 'Equalizer', 'Shape the sound of the three presets stored in the base station.') + `
    <section class="card">
      <div class="row sp wrap" style="margin-bottom:18px"><div id="eq-seg"></div>
        <div class="row" style="gap:8px"><input class="field" id="eq-name" maxlength="20" style="width:200px" placeholder="Preset name"><button class="btn" id="eq-ren">${ic('edit', 16)}Rename</button></div></div>
      <div id="eq-g"></div>
      <div class="eqvals" id="eq-vals" style="grid-template-columns:repeat(5,1fr);padding:0 24px 0 56px"></div>
      <div class="row sp wrap" style="margin-top:18px">
        <div class="small muted" style="max-width:520px">Drag the points: the headset changes as soon as you let go. Press <b>Save to headset</b> (top right) to keep the change after the headset is turned off.</div>
        <div class="row"><button class="btn" id="eq-undo">${ic('refresh', 16)}Undo changes</button><button class="btn" id="eq-flat">Flat</button></div></div>
    </section>
    <section class="card">${ct('Quick shapes')}<div class="g3" id="eq-quick"></div></section>`;
    this.cur = 1;
    this.seg = seg($('#eq-seg'), [['Preset 1', 1], ['Preset 2', 2], ['Preset 3', 3]], 1, p => this.pick(p));
    this.g = eqGraph($('#eq-g'), { gains: [0, 0, 0, 0, 0], labels: eqLabels(), range: 7, onInput: g => this.vals(g), onChange: g => this.write(g) });
    const vh = $('#eq-vals');
    for (let i = 0; i < 5; i++) {
      const inp = h(`<input class="field" type="number" min="-7" max="7" step="1" aria-label="Band ${i + 1} gain">`);
      inp.onchange = () => { const g = this.g.get(); g[i] = clamp(parseInt(inp.value || '0', 10), -7, 7); this.g.set(g); this.vals(g); this.write(g); };
      vh.appendChild(inp);
    }
    $('#eq-ren').onclick = () => this.rename();
    $('#eq-name').onkeydown = e => { if (e.key === 'Enter') this.rename(); };
    $('#eq-flat').onclick = () => { const g = [0, 0, 0, 0, 0]; this.g.set(g); this.vals(g); this.write(g); };
    $('#eq-undo').onclick = () => { if (this.orig) { this.g.set(this.orig); this.vals(this.orig); this.write(this.orig); } };
    const Q = [['Bass boost', [5, 3, 0, 0, 0]], ['Footsteps', [-4, -2, 2, 4, 2]], ['Voice / dialogue', [-2, 0, 3, 2, 0]], ['V-shape (music)', [4, 1, -2, 1, 4]], ['Bright', [0, 0, 0, 2, 4]], ['Warm', [3, 2, 0, -1, -2]]];
    Q.forEach(([n, g]) => {
      const t = h(`<button class="tile" type="button"><span class="tn">${esc(n)}</span>${miniCurve(g)}<span class="td">${g.map(signed).join(' · ')}</span></button>`);
      t.onclick = () => { this.g.set(g); this.vals(g); this.write(g); };
      $('#eq-quick').appendChild(t);
    });
  },
  vals(g) { $$('#eq-vals input').forEach((x, i) => { if (document.activeElement !== x) x.value = g[i]; }); },
  update() {
    const f = S.full;
    if (!f || !connected()) return;
    if (!this.userPick) this.cur = f.active || 1;
    this.seg.el.querySelectorAll('button').forEach((b, i) => { b.textContent = f.presets[i].name; });
    this.seg.set(this.cur);
    const pr = f.presets[this.cur - 1];
    if (document.activeElement !== $('#eq-name')) $('#eq-name').value = pr.name;
    this.g.set(pr.gains, eqLabels()); this.vals(pr.gains);
    if (!this.orig || this.origP !== this.cur) { this.orig = pr.gains.slice(); this.origP = this.cur; }
  },
  async pick(p) {
    if (!needDev()) return;
    this.cur = p; this.userPick = false;
    const r = await act(() => api('set_preset', { p }));
    if (r) { S.full = r; this.orig = null; Object.values(P).forEach(x => x.built && x.update && x.update()); toast(`EQ preset ${p}: ${r.presets[p - 1].name}`); }
  },
  async write(g) {
    if (!needDev()) return;
    const ok = await act(() => api('set_gains', { p: this.cur, gains: g }));
    if (ok && S.full) S.full.presets[this.cur - 1].gains = g.slice();
  },
  async rename() {
    if (!needDev()) return;
    const name = $('#eq-name').value.trim();
    if (!name) return;
    if (await act(() => api('rename', { p: this.cur, name }), 'Preset renamed')) { S.full.presets[this.cur - 1].name = name; this.update(); P.home.update(); }
  }
};

// ======================================================================= PROFILES
P.profiles = {
  build() {
    this.el.innerHTML = title('game', 'Game profiles', 'Ready-made EQ curves for popular games. Apply one, edit it, or let the app switch automatically.') + `
    <section class="card"><div class="row sp wrap">
      <div class="row grow" style="min-width:280px">${ic('radio', 22, 'var(--acc)')}<div class="col"><span style="font-weight:600">Automatic switching</span><span class="small muted" id="pf-auto-t">When a game in a profile starts, its EQ and mic setup are applied; your EQ comes back when it closes.</span></div></div>
      <div id="pf-auto-sw"></div></div></section>
    <div class="g2">
      <div><section class="card"><div class="row sp wrap" style="margin-bottom:16px"><div id="pf-cats" class="row wrap" style="gap:6px"></div>
        <div class="row"><button class="btn sm" id="pf-new">${ic('plus', 14)}From current EQ</button><button class="btn sm" id="pf-imp">${ic('upload', 14)}Import</button><button class="btn sm" id="pf-exp">${ic('download', 14)}Export mine</button></div></div>
        <div class="g3" id="pf-list"></div></section></div>
      <div><section class="card" id="pf-ed"></section></div>
    </div>`;
    this.cat = 'all'; this.sel = null;
    this.autoSw = swBtn(false, async on => { const r = await act(() => api('auto_switch', { on })); if (!r) return false; this.data.auto = r; this.autoText(); });
    $('#pf-auto-sw').appendChild(this.autoSw);
    $('#pf-new').onclick = () => this.newFromEq();
    $('#pf-imp').onclick = () => this.importF();
    $('#pf-exp').onclick = () => this.exportF();
    this.load();
  },
  enter() { if (this.data) this.load(); },
  async load() {
    const d = await act(() => api('profiles'));
    if (!d) return;
    this.data = d;
    this.autoSw.setOn(d.auto.on); this.autoText();
    const cats = $('#pf-cats'); cats.innerHTML = '';
    [['All', 'all'], ...d.categories.map(c => [c, c])].forEach(([l, v]) => {
      const b = h(`<button class="btn sm${this.cat === v ? ' btn-p' : ''}" type="button">${esc(l)}</button>`);
      b.onclick = () => { this.cat = v; this.load(); };
      cats.appendChild(b);
    });
    this.list();
    if (!this.sel || !d.profiles.find(p => p.id === this.sel)) this.sel = (d.profiles[0] || {}).id;
    this.editor();
  },
  autoText() {
    const a = this.data.auto;
    $('#pf-auto-t').textContent = !a.on ? 'Off. When a game in a profile starts, its EQ and mic setup are applied; your EQ comes back when it closes.'
      : a.active ? `On · now active: ${a.active} (${a.exe})` : 'On · waiting for a game from your profiles to start.';
  },
  list() {
    const L = $('#pf-list'); L.innerHTML = '';
    const items = this.data.profiles.filter(p => this.cat === 'all' || p.category === this.cat);
    if (!items.length) L.innerHTML = '<div class="empty">No profiles here yet.</div>';
    items.forEach(p => {
      const t = h(`<button class="tile${p.id === this.sel ? ' on' : ''}" type="button"><div class="row sp"><span class="tn">${esc(p.name)}</span>${p.kind !== 'builtin' ? `<span class="badge acc" style="height:20px">${p.kind === 'mine' ? 'Mine' : 'Edited'}</span>` : ''}</div>${miniCurve(p.gains)}<span class="td">${esc(p.games.length ? p.games.slice(0, 3).join(', ') + (p.games.length > 3 ? ' …' : '') : p.category)}</span></button>`);
      t.onclick = () => { this.sel = p.id; this.list(); this.editor(); };
      L.appendChild(t);
    });
  },
  editor() {
    const ed = $('#pf-ed'), p = this.data.profiles.find(x => x.id === this.sel);
    if (!p) { ed.innerHTML = '<div class="empty">Choose a profile.</div>'; return; }
    const mics = this.data.mics;
    ed.innerHTML = ct(p.kind === 'builtin' ? 'Built-in profile' : p.kind === 'edited' ? 'Built-in profile · your edit' : 'Your profile') + `
      <input class="field" id="pe-name" maxlength="40" style="width:100%;font-weight:600;font-size:16px" value="${esc(p.name)}">
      <div class="small muted" style="margin:8px 0 4px">${esc(p.note || '')}</div>
      <div id="pe-g"></div>
      <div class="k" style="margin:10px 0 6px">Games (.exe names, comma separated)</div>
      <textarea class="field" id="pe-games" rows="2" style="width:100%" placeholder="e.g. cs2.exe, valorant.exe">${esc(p.games.join(', '))}</textarea>
      <div class="k" style="margin:14px 0 6px">Microphone setup with this profile</div>
      <select class="field" id="pe-mic" style="width:100%"><option value="">Leave the mic as it is</option>${mics.map(m => `<option value="${esc(m.id)}"${m.id === p.mic ? ' selected' : ''}>${esc(m.name)}</option>`).join('')}</select>
      <div class="row wrap" style="margin-top:18px"><button class="btn btn-p" id="pe-apply">${ic('play', 15, 'currentColor', 2)}Apply now</button><button class="btn" id="pe-save">${ic('save', 15)}${p.kind === 'builtin' ? 'Save my version' : 'Save'}</button>
      ${p.kind !== 'builtin' ? `<button class="btn btn-d" id="pe-del">${ic('trash', 15)}${p.kind === 'edited' ? 'Back to original' : 'Delete'}</button>` : ''}</div>
      <div class="small muted" style="margin-top:10px">Apply writes the curve into the EQ preset that is active now.</div>`;
    this.g = eqGraph($('#pe-g'), { gains: p.gains, labels: eqLabels(), range: 7, height: 240 });
    const cur = () => ({ ...p, name: $('#pe-name').value.trim() || p.name, gains: this.g.get(), mic: $('#pe-mic').value || null,
      games: $('#pe-games').value.split(/[,;\n]/).map(s => s.trim().toLowerCase()).filter(Boolean) });
    $('#pe-apply').onclick = async () => {
      if (!needDev()) return;
      const r = await act(() => api('profile_apply', cur()));
      if (r) { toast(`${cur().name} applied to preset ${r.slot}` + (r.mic ? ` · mic: ${r.mic}` : ''), 'ok'); loadFull(true); }
    };
    $('#pe-save').onclick = async () => { const r = await act(() => api('profile_save', cur()), 'Profile saved'); if (r) { this.sel = r.id; this.load(); } };
    const del = $('#pe-del');
    if (del) del.onclick = async () => {
      if (!await confirmBox('Delete profile', p.kind === 'edited' ? `Go back to the original "${esc(p.name)}"?` : `Delete "${esc(p.name)}"?`, 'Delete', true)) return;
      if (await act(() => api('profile_remove', { id: p.id }))) { this.sel = p.overrides || null; this.load(); }
    };
  },
  async newFromEq() {
    const f = S.full;
    const gains = f ? f.presets[(f.active || 1) - 1].gains : [0, 0, 0, 0, 0];
    const name = await prompt2('New profile', 'Name for the new profile (it starts from the EQ preset active now)', 'My profile');
    if (!name) return;
    const r = await act(() => api('profile_new', { name, gains }), 'Profile created');
    if (r) { this.sel = r.id; this.cat = 'all'; this.load(); }
  },
  async importF() {
    const f = await pickFile('.json,application/json');
    if (!f) return;
    const r = await act(() => api('profile_import', { text: f.data }));
    if (r) { toast(`${r.count} profile(s) imported`, 'ok'); this.sel = r.id; this.cat = 'all'; this.load(); }
  },
  exportF() {
    const mine = this.data.profiles.filter(p => p.kind !== 'builtin');
    if (!mine.length) return toast('You have no profiles of your own yet.', 'err');
    const out = { a50control_profiles: 1, profiles: mine.map(p => ({ name: p.name, category: p.category, gains: p.gains, games: p.games, note: p.note, mic: p.mic })) };
    download('A50_profiles.json', JSON.stringify(out, null, 2));
  }
};

// ======================================================================= MICROPHONE
P.mic = {
  build() {
    this.el.innerHTML = title('mic', 'Microphone', 'Level, sidetone, noise gate, ready-made setups, a tester and an advanced PC equalizer.') + `
    <div class="g2">
      <div>
        <section class="card">${ct('Headset microphone')}<div id="mc-sl"></div>
          <div class="opt"><div class="grow"><div class="ot">Noise gate</div><div class="od">Streaming = most open · Night = soft voices · Home = balanced · Tournament = strongest</div></div></div><div id="mc-gate"></div>
          <div class="opt" style="margin-top:8px"><div class="grow"><div class="ot">Headset mic EQ</div><div class="od">Three tone presets built into the headset. Use "Compare" in the tester to hear them.</div></div><div id="mc-meq"></div></div>
        </section>
        <section class="card">${ct('Mic setups', '<button class="btn sm" id="mc-new">' + ic('plus', 14) + 'Save current</button>')}<div class="g3" id="mc-list"></div></section>
      </div>
      <div>
        <section class="card">${ct('Mic tester', '<span class="badge" id="mt-dev">Windows default mic</span>')}
          <div class="row wrap" style="margin-bottom:16px"><button class="btn btn-p" id="mt-live">${ic('wave', 16, 'currentColor', 2)}Live level</button><button class="btn" id="mt-rec">${ic('rec', 16)}Record 5 s and play back</button><button class="btn" id="mt-stop" disabled>${ic('stop', 16)}Stop</button></div>
          <div class="row sp small muted" style="margin-bottom:6px"><span>Level</span><span id="mt-db">–</span></div>
          <div class="meter"><div class="mf" id="mt-f"></div><div class="mp" id="mt-p"></div></div>
          <div class="spec" id="mt-spec">${'<i></i>'.repeat(20)}</div>
          <div class="row sp small muted"><span>100 Hz</span><span>1 kHz</span><span>7 kHz</span></div>
          <div class="small soft" id="mt-msg" style="margin-top:12px;min-height:20px">Talk normally: green is good, yellow is loud, red clips.</div>
          <div class="row wrap" style="margin-top:12px"><button class="btn" id="mt-cmp">${ic('users', 16)}Compare headset mic EQ presets</button><button class="btn sm" id="mt-folder">${ic('folder', 14)}Recordings</button></div>
        </section>
      </div>
    </div>
    <section class="card" id="apo" style="margin-top:22px">${ct('PC mic equalizer (Equalizer APO)', '<span class="badge" id="apo-st">Checking…</span>')}<div id="apo-body"></div></section>`;
    const sl = $('#mc-sl');
    this.mic = slider(sl, { label: 'Mic level', icon: 'mic', onChange: v => this.set('mic', v) });
    this.side = slider(sl, { label: 'Sidetone (hear yourself)', icon: 'speaker', onChange: v => this.set('sidetone', v) });
    this.gate = seg($('#mc-gate'), GATES.map((g, i) => [g, i]), -1, v => needDev() && act(() => api('set_gate', { v })));
    this.meq = seg($('#mc-meq'), [['Preset 0', 0], ['Preset 1', 1], ['Preset 2', 2]], -1, v => needDev() && act(() => api('set_miceq', { v })));
    $('#mc-new').onclick = () => this.saveSetup();
    $('#mt-live').onclick = () => this.test('live');
    $('#mt-rec').onclick = () => this.test('record');
    $('#mt-stop').onclick = () => act(() => api('mic_test', { stop: true }));
    $('#mt-cmp').onclick = async () => {
      if (!needDev()) return;
      if (!await confirmBox('Compare headset mic presets', 'The app records you 4 seconds with each of the 3 headset mic EQ presets, then plays the three recordings back.\nKeep talking the same way during all three. Your setting is put back at the end.', 'Start')) return;
      if (await act(() => api('mic_compare'))) this.watch();
    };
    $('#mt-folder').onclick = () => api('open', { what: 'mic_compare' }).catch(() => toast('No recordings yet', 'err'));
    this.loadSetups(); this.apoLoad();
  },
  async set(name, value) { if (needDev()) await act(() => api('set_slider', { name, value })); },
  update() {
    const f = S.full, ok = connected() && f;
    this.mic.set(ok ? f.sliders.mic : null); this.side.set(ok ? f.sliders.sidetone : null);
    this.gate.set(ok ? f.gate : -1); this.meq.set(ok ? f.miceq : -1);
  },
  async loadSetups() {
    const d = await act(() => api('profiles'));
    if (!d) return;
    const L = $('#mc-list'); L.innerHTML = '';
    d.mics.forEach(m => {
      const t = h(`<div class="tile" role="button" tabindex="0"><div class="row sp"><span class="tn">${esc(m.name)}</span>${m.kind === 'mine' ? `<button class="btn sm btn-d" style="height:24px;padding:0 6px" title="Delete">${ic('trash', 13)}</button>` : ''}</div>
        <span class="td">Level ${m.mic} · Sidetone ${m.sidetone} · ${GATES[m.gate]}</span><span class="td" style="color:#7D8798">${esc(m.note || '')}</span></div>`);
      t.onclick = async e => {
        if (e.target.closest('.btn-d')) {
          if (await confirmBox('Delete mic setup', `Delete "${esc(m.name)}"?`, 'Delete', true) && await act(() => api('mic_remove', { id: m.id }))) this.loadSetups();
          return;
        }
        if (!needDev()) return;
        if (await act(() => api('mic_apply', m), `Mic: ${m.name}`)) {
          $$('.tile', L).forEach(x => x.classList.remove('on')); t.classList.add('on');
          if (S.full) Object.assign(S.full, { gate: m.gate, sliders: { ...S.full.sliders, mic: m.mic, sidetone: m.sidetone } });
          this.update();
        }
      };
      L.appendChild(t);
    });
  },
  async saveSetup() {
    const f = S.full;
    if (!f || !connected()) return needDev();
    const name = await prompt2('Save mic setup', 'Name for your current level, sidetone and noise gate', 'My mic setup');
    if (!name) return;
    if (await act(() => api('mic_save', { name, mic: this.mic.get(), sidetone: this.side.get(), gate: f.gate ?? 2, note: 'Your setup.' }), 'Mic setup saved')) this.loadSetups();
  },
  async test(mode) {
    const r = await act(() => api('mic_test', { mode }));
    if (r) this.watch();
  },
  async watch() {
    if (this.watching) return;
    this.watching = true;
    $('#mt-stop').disabled = false; $('#mt-live').disabled = $('#mt-rec').disabled = $('#mt-cmp').disabled = true;
    const bars = $$('#mt-spec i');
    let m;
    try {
      do {
        m = await api('mic_state');
        const lv = clamp((m.rms + 60) / 60, 0, 1), pk = clamp((m.peak + 60) / 60, 0, 1);
        $('#mt-f').style.width = lv * 100 + '%'; $('#mt-p').style.left = `calc(${pk * 100}% - 3px)`;
        $('#mt-db').textContent = m.rms > -89 ? `${m.rms.toFixed(0)} dB` : '–';
        m.spec.forEach((v, i) => { if (bars[i]) bars[i].style.height = clamp((v + 80) / 70, 0.02, 1) * 100 + '%'; });
        $('#mt-msg').textContent = m.err || (m.phase === 'record' ? 'Recording… talk now' : m.phase === 'playing' ? 'Playing back…' : m.phase === 'live' ? (m.peak > -3 ? 'Too loud: lower the mic level.' : m.rms < -50 ? 'Very quiet: is the boom down and the mic unmuted?' : 'Good level.') : m.phase || '');
        if (m.running || m.phase === 'playing') await sleep(90);
      } while (m.running || m.phase === 'playing');
    } catch (e) { toast(e.message, 'err'); }
    this.watching = false;
    $('#mt-stop').disabled = true; $('#mt-live').disabled = $('#mt-rec').disabled = $('#mt-cmp').disabled = false;
    $('#mt-f').style.width = '0'; $('#mt-p').style.left = '0'; bars.forEach(b => b.style.height = '2%');
    if (m && m.err) $('#mt-msg').textContent = m.err;
  },
  // ---------------- Equalizer APO
  async apoLoad() {
    const d = await act(() => api('apo'));
    if (!d) return;
    this.apo = d;
    const st = $('#apo-st');
    st.className = 'badge ' + (d.installed ? (d.enabled ? 'ok' : 'acc') : 'warn');
    st.textContent = d.installed ? (d.enabled ? 'Active on the A50 mic' : 'Installed · off') : 'Equalizer APO not installed';
    const B = $('#apo-body');
    if (!d.installed) {
      B.innerHTML = `<div class="row wrap" style="gap:18px"><div class="grow soft" style="min-width:300px">A 10-band equalizer for your voice, applied by Windows to the A50 microphone before Discord, OBS or the game hear it.
        It needs the free <b>Equalizer APO</b> (open source). Install it, tick the <b>ASTRO A50 Voice</b> device in its Configurator under <i>Capture devices</i>, restart the PC, then come back here.</div>
        <div class="row"><button class="btn btn-p" id="apo-get">${ic('ext', 16, 'currentColor', 2)}Get Equalizer APO</button><button class="btn" id="apo-re">${ic('refresh', 16)}Check again</button></div></div>`;
      $('#apo-get').onclick = () => api('open', { what: 'apo' });
      $('#apo-re').onclick = () => this.apoLoad();
      return;
    }
    const all = [...d.presets.map(p => ({ ...p, kind: 'builtin' })), ...d.custom.map(p => ({ ...p, kind: 'mine' }))];
    B.innerHTML = `<div class="row sp wrap" style="margin-bottom:16px"><div class="row"><span id="apo-sw"></span><div class="col"><span style="font-weight:600">Use on the A50 microphone</span><span class="small muted">Turn off to send your voice unchanged.</span></div></div>
      <div class="row"><button class="btn sm" id="apo-save">${ic('save', 14)}Save as…</button><button class="btn sm" id="apo-cfg">${ic('gear', 14)}APO Configurator</button></div></div>
      <div class="g3" id="apo-list" style="margin-bottom:18px"></div>
      <div id="apo-g"></div>
      <div id="apo-sl" style="margin-top:6px"></div>
      <div class="opt"><div class="grow"><div class="ot">Low cut (high-pass)</div><div class="od">Removes rumble from desk, fans and breathing below this frequency.</div></div><div id="apo-hp"></div></div>`;
    const sw = swBtn(d.enabled, async on => { if (!await this.apoWrite({ enabled: on })) return false; this.apo.enabled = on; st.className = 'badge ' + (on ? 'ok' : 'acc'); st.textContent = on ? 'Active on the A50 mic' : 'Installed · off'; });
    $('#apo-sw').appendChild(sw);
    const L = $('#apo-list');
    all.forEach(p => {
      const t = h(`<div class="tile${p.id === d.current.id ? ' on' : ''}" role="button" tabindex="0"><div class="row sp"><span class="tn">${esc(p.name)}</span>${p.kind === 'mine' ? `<button class="btn sm btn-d" style="height:24px;padding:0 6px" title="Delete">${ic('trash', 13)}</button>` : ''}</div>${miniCurve(p.gains, 12)}<span class="td">${esc(p.note || '')}</span></div>`);
      t.onclick = async e => {
        if (e.target.closest('.btn-d')) { if (await confirmBox('Delete mic EQ', `Delete "${esc(p.name)}"?`, 'Delete', true) && await act(() => api('apo_remove', { id: p.id }))) this.apoLoad(); return; }
        this.apo.current = { ...p }; if (await this.apoWrite({ current: this.apo.current })) { $$('.tile', L).forEach(x => x.classList.remove('on')); t.classList.add('on'); this.apoUi(); toast(`Mic EQ: ${p.name}`, 'ok'); }
      };
      L.appendChild(t);
    });
    const labels = d.bands.map(b => b >= 1000 ? b / 1000 + 'k' : String(b));
    this.apoG = eqGraph($('#apo-g'), { gains: d.current.gains, labels, range: 12, height: 260, onChange: g => { this.apo.current.gains = g; this.apoWrite({ current: this.apo.current }); } });
    this.pre = slider($('#apo-sl'), { label: 'Volume (preamp)', icon: 'speaker', min: -12, max: 12, value: d.current.preamp, fmt: v => signed(v) + ' dB', center: true, onChange: v => { this.apo.current.preamp = v; this.apoWrite({ current: this.apo.current }); } });
    this.hp = seg($('#apo-hp'), [[ 'Off', 0], ['60 Hz', 60], ['80 Hz', 80], ['100 Hz', 100], ['120 Hz', 120]], d.current.hp, v => { this.apo.current.hp = v; this.apoWrite({ current: this.apo.current }); });
    $('#apo-save').onclick = async () => {
      const name = await prompt2('Save mic EQ', 'Name for this mic EQ', 'My mic EQ');
      if (name && await act(() => api('apo_save', { name, current: this.apo.current }), 'Mic EQ saved')) this.apoLoad();
    };
    $('#apo-cfg').onclick = async () => { const r = await act(() => api('apo_configurator')); if (r && !r.ok) toast('Configurator not found', 'err'); };
  },
  apoUi() { const c = this.apo.current; this.apoG.set(c.gains); this.pre.set(c.preamp); this.hp.set(c.hp); },
  async apoWrite(body) { return !!(await act(() => api('apo_set', body))); }
};

// ======================================================================= MIX
P.mix = {
  build() {
    this.el.innerHTML = title('mix', 'Mix and alerts', 'Game/voice balance, alert volume and the stream port output mix.') + `
    <div class="grid">
      <section class="card">${ct('Balance')}<div id="mx-bal"></div><div class="small muted" id="mx-cur" style="margin-top:4px"></div><div class="small muted">Lower = more game, higher = more voice chat.</div></section>
      <section class="card">${ct('Alerts')}<div id="mx-al"></div><div class="small muted" style="margin-top:6px">Volume of the beeps and voice prompts (power, mute, low battery).</div></section>
    </div>
    <section class="card" style="margin-top:22px">${ct('Stream port mix')}<div class="small muted" style="margin:-6px 0 8px">What goes out of the base station's stream port (to a capture card or a second PC).</div><div id="mx-st"></div></section>`;
    this.bal = slider($('#mx-bal'), { label: 'Default balance', icon: 'mix', max: 255, fmt: v => v === 128 ? 'center' : String(v), onChange: v => needDev() && act(() => api('set_default_balance', { v })) });
    this.al = slider($('#mx-al'), { label: 'Alert volume', icon: 'speaker', onChange: v => needDev() && act(() => api('set_alert', { v })) });
    this.st = {};
    [['stream_game', 'Game', 'game'], ['stream_chat', 'Chat', 'users'], ['stream_mic', 'Mic', 'mic'], ['stream_aux', 'Aux', 'speaker']].forEach(([k, l, i]) => {
      this.st[k] = slider($('#mx-st'), { label: l, icon: i, onChange: value => needDev() && act(() => api('set_slider', { name: k, value })) });
    });
  },
  update() {
    const f = S.full, ok = connected() && f;
    this.bal.set(ok ? f.default_balance : null); this.al.set(ok ? f.alert : null);
    Object.entries(this.st).forEach(([k, s]) => s.set(ok ? f.sliders[k] : null));
    $('#mx-cur').textContent = ok && f.balance != null ? `Current balance: ${f.balance} (changes with the buttons on the headset)` : '';
  }
};

// ======================================================================= JOBS (shared by Firmware and Maintenance)
const JOB = { next: 0, polling: false };
async function jobWatch() {
  if (JOB.polling) return;
  JOB.polling = true;
  JOB.next = 0;
  $$('.joblog').forEach(l => { l.textContent = ''; });
  let j;
  try {
    do {
      j = await api('job', { from: JOB.next });
      JOB.next = j.next;
      $$('.joblog').forEach(l => { if (j.log) { l.textContent += j.log; l.scrollTop = l.scrollHeight; } });
      $$('.jobst').forEach(s => { s.className = 'badge jobst ' + (j.running ? 'acc' : j.ok ? 'ok' : 'bad'); s.textContent = j.running ? (j.name + '…') : (j.name + (j.ok ? ': done' : ': check the log')); });
      P.firmware.progress(j.progress || {});
      if (j.running) await sleep(600);
    } while (j.running);
  } catch (e) { toast(e.message, 'err'); }
  JOB.polling = false;
  if (j && !j.running) { toast(j.name + (j.verified === true ? ': done and verified' : j.verified === false ? ': the version read back is wrong, read the log' : j.ok ? ' finished' : ' finished with problems: read the log'), j.ok ? 'ok' : 'err'); await sleep(1500); loadFull(true); P.firmware.built && P.firmware.refresh(); }
}

// ======================================================================= FIRMWARE
const FW_LABEL = { tx_mcu: 'Base processor', tx_radio: 'Base radio chip', rx_mcu: 'Headset processor', rx_radio: 'Headset radio chip' };
const FW_TIME = { tx_radio: 'about 1 minute', rx_radio: 'about 2 minutes', tx_mcu: 'a few minutes', rx_mcu: 'a few minutes' };
P.firmware = {
  build() {
    this.el.innerHTML = title('fw', 'Firmware', 'A safe, guided update: one chip at a time, with checks before and after each step.') + `
    <section class="card">${ct('1 · Firmware file', '<span class="small muted" id="fw-file">No file loaded</span>')}
      <div class="row wrap"><button class="btn" id="fw-pick">${ic('file', 16)}Choose .afw file</button><button class="btn" id="fw-auto">${ic('refresh', 16)}Find ASTRO Command Center's file</button></div>
      <div class="small muted" id="fw-notes" style="margin-top:10px"></div></section>
    <section class="card">${ct('2 · Safety checks', '<button class="btn sm" id="fw-recheck">' + ic('refresh', 14) + 'Check again</button>')}
      <div id="fw-checks"></div></section>
    <section class="card">${ct('3 · Update one chip at a time', '<span class="badge jobst" hidden></span>')}
      <div class="small soft" style="margin:-4px 0 14px">Radio chips first (tested), processors last (experimental). Each step is verified by reading the version back before the next one unlocks. A settings backup is made before every step.</div>
      <div class="col" style="gap:12px" id="fw-steps"></div>
      <div class="opt" style="margin-top:14px"><div class="grow"><div class="ot">Include processors (experimental)</div><div class="od">The processor steps have not been tested on real units. Leave this off unless a processor really needs it.</div></div><span id="fw-exp"></span></div>
    </section>
    <section class="card">${ct('Log')}<div class="log joblog"></div></section>`;
    this.exp = false;
    $('#fw-exp').appendChild(swBtn(false, v => { this.exp = v; this.refresh(); }));
    $('#fw-pick').onclick = async () => {
      const f = await pickFile('.afw', 'b64');
      if (!f) return;
      if (await act(() => api('fw_upload', { name: f.name, data: f.data }), 'Firmware file loaded')) this.refresh();
    };
    $('#fw-auto').onclick = () => this.refresh(true);
    $('#fw-recheck').onclick = () => this.refresh();
    this.refresh();
  },
  enter() { this.refresh(); },
  async refresh(say) {
    if (JOB.polling) return;
    const r = await act(() => api('fw_steps', { exp: this.exp }));
    if (!r) return;
    this.st = r;
    if (say && !r.file) toast("ASTRO Command Center's firmware file was not found. Choose the .afw file yourself.", 'err');
    $('#fw-file').textContent = r.file || 'No file loaded';
    $('#fw-notes').textContent = r.notes ? 'Notes: ' + r.notes : '';
    this.blocking = r.checks.filter(c => c.level === 'block' && !c.ok);
    $('#fw-checks').innerHTML = r.checks.map(c => {
      const col = c.ok ? '#5BE6A9' : c.level === 'warn' ? '#FFC170' : '#FF8A95';
      return `<div class="opt">${ic(c.ok ? 'check' : 'alert', 18, col, c.ok ? 2.4 : 1.8)}<div class="grow"><div class="ot">${esc(c.label)}</div><div class="od">${esc(c.detail)}</div></div>
        <span class="badge ${c.ok ? 'ok' : c.level === 'warn' ? 'warn' : 'bad'}">${c.ok ? 'OK' : c.level === 'warn' ? 'Warning' : 'Fix first'}</span></div>`;
    }).join('');
    this.draw();
  },
  draw() {
    const r = this.st, host = $('#fw-steps');
    host.innerHTML = '';
    const firstPending = r.steps.find(x => x.state === 'update');
    const intLab = { verified: ['ok', 'image verified'], ok: ['', 'image ok'], mismatch: ['bad', 'image damaged'], bad: ['bad', 'image damaged'] };
    r.steps.forEach((x, i) => {
      const st = { ok: ['ok', 'Up to date'], update: ['acc', 'Needs update'], experimental: ['warn', 'Experimental: off'], unreachable: ['warn', 'Headset not answering'], nofile: ['', 'Not in file'], blocked: ['', 'Waiting for the base'] }[x.state] || ['', x.state];
      const il = x.integrity && intLab[x.integrity];
      const row = h(`<div class="tile static" style="flex-direction:row;align-items:center;gap:16px;${firstPending === x ? 'border-color:rgba(var(--accr),.45)' : ''}">
        <div class="title-ic" style="width:40px;height:40px;border-radius:12px;font-weight:700;font-family:var(--display)">${i + 1}</div>
        <div class="grow"><div class="row wrap" style="gap:8px"><span class="tn">${esc(x.label)}</span>${x.tested ? '' : '<span class="badge warn" style="height:20px">experimental</span>'}${il ? `<span class="badge ${il[0]}" style="height:20px">${il[1]}</span>` : ''}</div>
          <div class="td">Installed <b>${x.installed ?? '–'}</b> · in the file <b>${x.file ?? '–'}</b> · takes ${FW_TIME[x.key]}</div>
          <div class="pbar" style="margin-top:8px"><i data-pb="${x.key}"></i></div><div class="small muted" data-pt="${x.key}"></div></div>
        <span class="badge ${st[0]}">${st[1]}</span><span class="act"></span></div>`);
      const actEl = $('.act', row);
      if (x.state === 'update') {
        const b = h(`<button class="btn ${firstPending === x ? 'btn-p' : ''}" type="button">${ic('upload', 15, 'currentColor', 2)}Update</button>`);
        b.disabled = firstPending !== x || this.blocked(x.key) || r.busy;
        if (firstPending !== x) b.title = 'Do the steps in order';
        b.onclick = () => this.go(x, false);
        actEl.appendChild(b);
      } else if (x.state === 'ok') {
        const b = h(`<button class="btn sm" type="button">Reinstall</button>`);
        b.disabled = !!firstPending || this.blocked(x.key) || r.busy || (!x.tested && !this.exp);
        b.onclick = () => this.go(x, true);
        actEl.appendChild(b);
      } else if (x.state === 'unreachable') {
        const b = h(`<button class="btn sm" type="button">Help</button>`);
        b.onclick = () => modal('Headset not answering', "The base can't reach the headset, so its chips can't be read or written.\n\n1. Turn the headset on and put it on the base.\n2. If it's flat, leave it charging for an hour.\n3. If it still never answers after a failed update, use Maintenance > Recover headset processor (experimental).", [['OK', 1, 'btn-p']]);
        actEl.appendChild(b);
      }
      host.appendChild(row);
    });
    if (!r.steps.some(x => x.state === 'update') && r.file && !r.steps.some(x => x.state === 'unreachable'))
      host.appendChild(h(`<div class="small" style="color:#5BE6A9">${ic('check', 14, '#5BE6A9', 2.4)} The radio chips are up to date. Nothing to do.</div>`));
    const newer = r.steps.filter(x => x.state === 'experimental' && x.file != null && x.installed != null && x.file !== x.installed);
    if (newer.length) host.appendChild(h(`<div class="small soft">${ic('alert', 14, '#FFC170')} The file has a different version for: ${newer.map(x => esc(x.label.toLowerCase())).join(', ')}. If everything works, you don't need it.</div>`));
  },
  blocked(key) {
    return this.blocking.some(c => {
      if (key.startsWith('tx_') && ['docked', 'reach', 'battery'].includes(c.id)) return false;
      if (c.id === 'integrity') { const st = this.st.steps.find(x => x.key === key); return st && ['mismatch', 'bad'].includes(st.integrity); }
      if (c.id === 'base' && key === 'tx_mcu' && this.st.stuck) return false;
      return true;
    });
  },
  progress(p) {
    Object.entries(p).forEach(([k, [d, t]]) => {
      const key = Object.keys(FW_LABEL).find(x => k.includes(x)) || k;
      const b = $(`[data-pb="${key}"]`), tx = $(`[data-pt="${key}"]`);
      if (b) b.style.width = (t ? d / t * 100 : 0) + '%';
      if (tx) tx.textContent = t ? `${Math.round(d / t * 100)}% written` : '';
    });
  },
  async go(x, reinstall) {
    const warn = x.tested ? '' : '\n\n⚠ This is an EXPERIMENTAL step: it has never been tested on a real unit.';
    const text = `${reinstall ? 'Reinstall' : 'Update'} the ${esc(x.label.toLowerCase())}: ${x.installed ?? '?'} → ${x.file}\nIt takes ${FW_TIME[x.key]}.\n\nUntil it says done:\n• don't unplug the base or move the headset off it\n• don't close A50 Control or turn off the PC\n\nA backup of your settings is made first, and the version is read back at the end to check it worked.${warn}`;
    if (!await confirmBox(reinstall ? 'Reinstall chip' : 'Update chip', text, reinstall ? 'Reinstall now' : 'Update now', !x.tested)) return;
    const r = await act(() => api('fw_step', { key: x.key, reinstall, exp: this.exp }));
    if (r) { $$('.jobst').forEach(s => s.hidden = false); $$('#fw-steps .btn').forEach(b => b.disabled = true); jobWatch(); }
  }
};

// ======================================================================= MAINTENANCE
P.maint = {
  build() {
    this.el.innerHTML = title('tools', 'Maintenance', 'Diagnose and repair the radio chips, back up your settings, make a report.') + `
    <div class="grid">
      <section class="card">${ct('Repair', '<span class="badge jobst" hidden></span>')}
        <div class="col" style="gap:10px">
          <button class="tile" id="mt-info">${ic('radio', 20, 'var(--acc)')}<span class="tn">Diagnose</span><span class="td">Reads every chip and says what's wrong. Changes nothing.</span></button>
          <button class="tile" id="mt-fb">${ic('tools', 20, 'var(--acc)')}<span class="tn">Fix base radio chip</span><span class="td">Reinstalls the base station's radio firmware.</span></button>
          <button class="tile" id="mt-fh">${ic('tools', 20, 'var(--acc)')}<span class="tn">Fix headset radio chip</span><span class="td">Reinstalls the headset's radio firmware. Headset on the base.</span></button>
          <button class="tile" id="mt-rh">${ic('alert', 20, '#FFC170')}<span class="tn">Recover headset processor <span class="badge warn" style="height:20px">experimental</span></span><span class="td">Only if Diagnose says the headset is unreachable after a failed update.</span></button>
        </div><div class="small muted" style="margin-top:12px">Pairing is never touched.</div></section>
      <section class="card">${ct('Settings backup')}
        <div class="soft small" style="margin-bottom:14px">Saves the 3 EQ presets with names, mic, sidetone, noise gate, balance and stream mix to a file. A backup is also made automatically before every firmware update or repair.</div>
        <div class="row wrap"><button class="btn btn-p" id="bk-save">${ic('download', 16, 'currentColor', 2)}Back up</button><button class="btn" id="bk-load">${ic('upload', 16)}Restore…</button><button class="btn sm" id="bk-dir">${ic('folder', 14)}Backups folder</button></div></section>
      <section class="card">${ct('Diagnostic report')}
        <div class="soft small" style="margin-bottom:14px">Versions, USB state and the errors from ASTRO Command Center's log, ready to attach to a GitHub issue. Your user name is removed.</div>
        <div class="row wrap"><button class="btn btn-p" id="rp-save">${ic('file', 16, 'currentColor', 2)}Save report</button><button class="btn" id="rp-copy">Copy</button><button class="btn sm" id="rp-iss">${ic('ext', 14)}Open issues</button></div></section>
      <section class="card">${ct('Connection')}
        <div class="soft small" style="margin-bottom:14px">If the base was unplugged or ASTRO Command Center was using it, reconnect here.</div>
        <button class="btn" id="mt-rc">${ic('refresh', 16)}Reconnect</button></section>
    </div>
    <section class="card" style="margin-top:22px">${ct('Log')}<div class="log joblog"></div></section>`;
    const run = async (action, name, warn) => {
      if (!connected() && action !== 'info') return needDev();
      if (warn && !await confirmBox(name, warn, 'Start')) return;
      if (await act(() => api('tool', { action }))) { $$('.jobst').forEach(s => s.hidden = false); jobWatch(); }
    };
    $('#mt-info').onclick = () => run('info', 'Diagnose');
    $('#mt-rh').onclick = async () => {
      if (!connected()) return needDev();
      if (!await confirmBox('Recover headset processor (experimental)', 'Use this only when Diagnose says the headset is UNREACHABLE after a failed firmware update.\n\nIt reinstalls the headset processor firmware from the .afw file (load it on the Firmware page). If the headset doesn\'t answer, the start is refused and nothing is written.\n\nThis path has never been tested on a real unit. Keep the headset on the base and don\'t unplug anything.', 'I understand, start', true)) return;
      if (await act(() => api('recover_headset_mcu'))) { $$('.jobst').forEach(s => s.hidden = false); jobWatch(); }
    };
    $('#mt-fb').onclick = () => run('fix-base', 'Fix base radio chip', "The base station's radio chip firmware is reinstalled. Takes about a minute. Don't unplug the base.");
    $('#mt-fh').onclick = () => run('fix-headset', 'Fix headset radio chip', "Put the headset on the base and keep it there. The headset's radio chip firmware is reinstalled over the air, about 2 minutes.");
    $('#bk-save').onclick = async () => {
      if (!needDev()) return;
      const r = await act(() => api('backup'));
      if (r) { download('A50_settings_' + r.created.replace(/[: ]/g, '-').slice(0, 16) + '.json', JSON.stringify(r, null, 2)); toast('Backup saved (also in the backups folder)', 'ok'); }
    };
    $('#bk-load').onclick = async () => {
      if (!needDev()) return;
      const f = await pickFile('.json,application/json');
      if (!f) return;
      const choice = await modal('Restore settings', `Restore the settings from "${esc(f.name)}"?\nThey are applied now. "Restore and save" also makes them permanent.`, [['Cancel', 0], ['Restore', 1], ['Restore and save', 2, 'btn-p']]);
      if (!choice) return;
      const r = await act(() => api('restore', { text: f.data, save: choice === 2 }));
      if (r) { toast(r.failed && r.failed.length ? `Restored, except: ${r.failed.join(', ')}` : 'Settings restored', r.failed && r.failed.length ? 'err' : 'ok'); loadFull(true); }
    };
    $('#bk-dir').onclick = () => api('open', { what: 'backups' });
    $('#rp-save').onclick = async () => { const r = await act(() => api('report')); if (r) download(r.name, r.text, 'text/plain'); };
    $('#rp-copy').onclick = async () => { const r = await act(() => api('report')); if (r) { await navigator.clipboard.writeText(r.text).then(() => toast('Report copied', 'ok'), () => toast('Copy failed', 'err')); } };
    $('#rp-iss').onclick = () => api('open', { what: 'issues' });
    $('#mt-rc').onclick = reconnect;
  }
};

// ======================================================================= SETTINGS
P.settings = {
  build() {
    const s = S.info.settings;
    this.el.innerHTML = title('gear', 'Settings', 'Colours, behaviour and shortcuts.') + `
    <section class="card">${ct('Colours', '<button class="btn sm" id="st-reset">Reset colours</button>')}
      <div class="row" style="gap:22px;align-items:flex-start;flex-wrap:wrap">
        <div class="cp grow" id="st-cp"></div>
        <div style="width:220px;flex:none" id="st-prev"></div></div></section>
    <div class="grid">
      <section class="card">${ct('Behaviour')}
        <div class="opt"><div class="grow"><div class="ot">Start with Windows</div><div class="od">Starts in the tray, ready for hotkeys and game switching.</div></div><span id="st-auto"></span></div>
        <div class="opt"><div class="grow"><div class="ot">Closing the window keeps the app in the tray</div><div class="od">Battery icon, notifications, hotkeys and auto-switch keep working.</div></div><span id="st-tray"></span></div>
        <div class="opt"><div class="grow"><div class="ot">Low battery alert</div><div class="od">Windows notification when the headset gets low.</div></div></div><div id="st-low"></div>
      </section>
      <section class="card">${ct('Keyboard shortcuts', '<span id="st-hk"></span>')}<div id="st-keys"></div></section>
    </div>
    <section class="card" style="margin-top:22px">${ct('About')}
      <div class="row sp wrap"><div class="col"><span class="h" style="font-size:20px;font-weight:700">A50 Control ${esc(S.info.version)}</span><span class="small muted">Open source replacement for ASTRO Command Center (A50 Gen 4). Not affiliated with Logitech or ASTRO Gaming.</span></div>
      <div class="row wrap"><button class="btn" id="st-gh">${ic('ext', 16)}GitHub</button><button class="btn" id="st-don">${ic('heart', 16, '#FF8A95')}Donate</button><button class="btn btn-d" id="st-quit">${ic('x', 16)}Quit A50 Control</button></div></div></section>`;
    const C = s.colors;
    const save = () => act(() => api('settings', { colors: C }));
    const quick = ['#00B4FF', '#7C5CFF', '#FF3B6B', '#FF8A00', '#3DDC97', '#FFD400', '#FFFFFF'];
    const shellQ = ['#1C2029', '#0B0C0F', '#3A3F4A', '#E9ECF1', '#1B2A44', '#3B1F2B', '#1F3326'];
    const items = [['app', 'App colour', 'Buttons, highlights, glows', quick], ['hacc', 'Headset lights', 'LED strips and base lights', quick], ['shell', 'Shell', 'Ear cups and base', shellQ], ['cush', 'Cushions', 'Ear pads and headband', ['#0D0F14', '#2A2D35', '#4A3B30', '#E3E6EB', '#202A3A']]];
    this.pk = {};
    items.forEach(([k, l, d, q]) => { this.pk[k] = colorPicker($('#st-cp'), { label: l, desc: d, value: C[k], quick: q, onInput: v => { C[k] = v; applyColors(C); }, onChange: save }); });
    $('#st-reset').onclick = () => { Object.assign(C, { app: '#00B4FF', shell: '#1C2029', hacc: '#00B4FF', cush: '#0D0F14' }); Object.entries(this.pk).forEach(([k, p]) => p.set(C[k])); applyColors(C); save(); };
    fetch('headset.svg').then(r => r.text()).then(t => { $('#st-prev').innerHTML = t; const sv = $('#st-prev svg'); sv.style.animation = 'none'; sv.style.maxWidth = '220px'; $$('.led', sv).forEach((l, i) => i === 0 && l.classList.add('on')); });
    $('#st-auto').appendChild(swBtn(S.info.autostart, async on => { const r = await act(() => api('autostart', { on })); return r ? r.on === on : false; }));
    $('#st-tray').appendChild(swBtn(s.close_to_tray, async on => !!(await act(() => api('settings', { close_to_tray: on })))));
    seg($('#st-low'), [['Off', 0], ['10%', 10], ['15%', 15], ['20%', 20], ['30%', 30]], s.low_battery, v => act(() => api('settings', { low_battery: v })));
    $('#st-hk').appendChild(swBtn(s.hotkeys, async on => !!(await act(() => api('settings', { hotkeys: on })))));
    $('#st-keys').innerHTML = S.info.hotkeys.map(k => `<div class="opt"><div class="row" style="gap:4px">${k.key.split(' + ').map(x => `<span class="kbd">${esc(x)}</span>`).join('<span class="muted">+</span>')}</div><div class="grow" style="text-align:right">${esc(k.desc)}${k.taken ? ' <span class="badge warn">used by another app</span>' : ''}</div></div>`).join('');
    $('#st-gh').onclick = () => api('open', { what: 'repo' });
    $('#st-don').onclick = () => api('open', { what: 'donate' });
    $('#st-quit').onclick = async () => {
      if (!await confirmBox('Quit', 'Close A50 Control completely? Hotkeys, game switching and the tray icon stop until you open it again.', 'Quit', true)) return;
      await api('quit').catch(() => { });
      document.body.innerHTML = '<div style="display:flex;height:100vh;align-items:center;justify-content:center;color:#8E98AA;font:15px Segoe UI">A50 Control is closed. You can close this window.</div>';
      setTimeout(() => window.close(), 300);
    };
  }
};

// ======================================================================= start
async function start() {
  const nav = $('#nav');
  PAGES.forEach(([id, label, icon]) => nav.appendChild(h(`<a data-p="${id}" tabindex="0">${ic(icon)}<span>${label}</span></a>`)));
  $('#nav2').appendChild(h(`<a data-p="settings" tabindex="0">${ic('gear')}<span>Settings</span></a>`));
  $$('.nav a').forEach(a => { a.onclick = () => show(a.dataset.p); a.onkeydown = e => { if (e.key === 'Enter') show(a.dataset.p); }; });
  $$('[data-ic]').forEach(e => { e.innerHTML = ic(e.dataset.ic, +e.dataset.icSize || 20, 'currentColor', +e.dataset.icSw || 1.8); });
  $('#btn-reload').innerHTML = ic('refresh', 16) + 'Reload';
  $('#btn-save').innerHTML = ic('save', 16, 'currentColor', 2) + 'Save to headset';
  $('#btn-reload').onclick = async () => { if (connected()) { await loadFull(); toast('Values read from the headset'); } else reconnect(); };
  $('#btn-save').onclick = () => needDev() && act(() => api('save'), 'Saved to the headset: kept after power off');
  const pages = $('#pages');
  [...PAGES.map(p => p[0]), 'settings'].forEach(id => { const el = h(`<section class="page" id="pg-${id}"></section>`); pages.appendChild(el); P[id].el = el; });
  try { S.info = await api('info'); } catch (e) { toast(e.message, 'err'); return; }
  applyColors(S.info.settings.colors);
  $('#ver').textContent = `v${S.info.version} · open source`;
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && $('#modal').classList.contains('on')) $('#modal').classList.remove('on');
    if (e.key === 'F5') { e.preventDefault(); $('#btn-reload').click(); }
  });
  document.addEventListener('contextmenu', e => { if (!e.target.closest('input,textarea,.log')) e.preventDefault(); });
  show(location.hash.slice(1) || 'home');
  poll();
}
start();
