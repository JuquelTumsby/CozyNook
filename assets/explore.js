/* CozyNook "Outside": a shared park everyone can explore (unlocks at level 20).
   Open it by clicking the window in your room.
   Safety for kids: no typing. Players talk with preset phrases and emotes, and get a
   generated cute nickname, so no personal info or free text is ever shared.
   Online data: Firestore collection explore/{uid} (one small doc per player). To keep usage
   low, a player only writes when they pick a new spot, emote or say something, plus a
   heartbeat every 25 seconds; everyone animates the walking locally. */
(function () {
  'use strict';
  var LEVEL_NEEDED = 20;
  var W = 480, H = 270, SCALE = 2, SPEED = 46;           // world size (pixels) and walk speed (px/s)
  var WALK = { x0: 22, x1: 458, y0: 132, y1: 262 };        // where feet may go
  var STALE_MS = 90000, BEAT_MS = 25000;
  var ADJ = ['Sunny', 'Cozy', 'Sleepy', 'Happy', 'Fluffy', 'Starry', 'Minty', 'Peachy', 'Bouncy', 'Gentle', 'Sparkly', 'Snug', 'Breezy', 'Cheery', 'Dreamy', 'Jolly', 'Lucky', 'Mellow', 'Rosy', 'Silly', 'Sweet', 'Toasty', 'Velvet', 'Witty', 'Brave', 'Calm', 'Comfy', 'Daisy', 'Honey', 'Maple', 'Misty', 'Pebble'];
  var ANIMAL = ['Otter', 'Panda', 'Kitten', 'Bunny', 'Fox', 'Koala', 'Penguin', 'Puppy', 'Hamster', 'Owl', 'Duckling', 'Hedgehog', 'Seal', 'Lamb', 'Fawn', 'Robin', 'Turtle', 'Squirrel', 'Raccoon', 'Llama', 'Sloth', 'Bear', 'Frog', 'Whale', 'Mouse', 'Badger', 'Pony', 'Chick', 'Beaver', 'Lemur', 'Moth', 'Gecko'];
  var PHRASES = ['Hi! 👋', 'Nice outfit!', 'Want to be friends?', 'Good luck studying!', 'Let\'s take a break!', 'I love your style!', 'Yay! 🎉', 'See you later!', 'Follow me!', 'Thank you!', 'You\'re awesome!', 'Bye bye!'];
  var EMOTES = ['happy', 'love', 'excited', 'sleepy', 'cool', 'shy'];

  var $ = function (id) { return document.getElementById(id); };
  var app = function () { return window.CozyApp || {}; };
  var getData = function (k, d) { var a = app(); var v = a.getData ? a.getData(k) : undefined; return v === undefined || v === null ? d : v; };
  var toast = function (m) { var a = app(); if (a.toast) a.toast(m); };
  var level = function () { return Math.floor((getData('xp', 0) || 0) / 100) + 1; };

  var overlay, canvas, ctx, bg = null, running = false, raf = 0;
  var me = null, others = {}, unsub = null, beat = 0, resub = 0, online = false, lastWrite = 0, pendingWrite = null, writeTimer = 0;
  var keysDown = {}, keyTimer = 0;

  /* ---------------- helpers ---------------- */
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function nameOf(na, nb) { return (ADJ[na] || 'Cozy') + ' ' + (ANIMAL[nb] || 'Friend'); }
  function myNameIdx(uid) {
    var saved = getData('exploreName', null);
    if (Array.isArray(saved) && saved.length === 2) return saved;
    var h = hash(uid || 'me'); return [h % ADJ.length, (h >>> 8) % ANIMAL.length];
  }
  function cleanLook(lk) {
    var out = {}, ok = /^[a-z0-9-]{1,20}$/, col = /^#[0-9a-fA-F]{6}$/;
    lk = lk || {};
    ['gender', 'emote', 'outfitStyle', 'hairStyle', 'accessory'].forEach(function (k) { if (typeof lk[k] === 'string' && ok.test(lk[k])) out[k] = lk[k]; });
    ['skin', 'hair', 'outfit'].forEach(function (k) { if (typeof lk[k] === 'string' && col.test(lk[k])) out[k] = lk[k]; });
    return out;
  }
  function myLook() {
    return cleanLook({ gender: getData('gender', 'girl'), emote: getData('emote', 'happy'), outfitStyle: getData('outfitStyle', 'hoodie'), hairStyle: getData('hairStyle', 'default'), accessory: getData('accessory', 'none'), skin: getData('skin', undefined), hair: getData('hair', undefined), outfit: getData('outfit', undefined) });
  }
  function clampWalk(x, y) { return [Math.max(WALK.x0, Math.min(WALK.x1, x)), Math.max(WALK.y0, Math.min(WALK.y1, y))]; }
  function nightTime() { var h = new Date().getHours(); return h >= 19 || h < 6; }

  /* ---------------- park background ---------------- */
  function drawPark() {
    var c = document.createElement('canvas'); c.width = W; c.height = H;
    var g = c.getContext('2d'), night = nightTime();
    var R = function (x, y, w, h, col) { g.fillStyle = col; g.fillRect(x, y, w, h); };
    var seed = 7, rnd = function () { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    // sky
    var sky = night ? ['#1d1840', '#2b2560', '#3d3480'] : ['#8fd3f4', '#a9def7', '#c6eafa'];
    R(0, 0, W, 22, sky[0]); R(0, 22, W, 22, sky[1]); R(0, 44, W, 30, sky[2]);
    if (night) { for (var s = 0; s < 40; s++) R(Math.floor(rnd() * W), Math.floor(rnd() * 60), 1, 1, '#fff6c8'); var disc = function (cx, cy, r, col) { for (var yy = -r; yy <= r; yy++) { var ww = Math.round(Math.sqrt(r * r - yy * yy)); R(cx - ww, cy + yy, ww * 2, 1, col); } }; disc(406, 20, 8, '#fff3b0'); disc(410, 17, 7, sky[0]); }
    else { R(52, 14, 16, 16, '#ffe680'); R(54, 12, 12, 20, '#ffe680'); [[110, 20], [260, 12], [370, 26]].forEach(function (p) { R(p[0], p[1] + 4, 40, 8, '#ffffff'); R(p[0] + 8, p[1], 22, 6, '#ffffff'); R(p[0] + 4, p[1] + 10, 34, 3, '#e3f4fb'); }); }
    // far hills
    g.fillStyle = night ? '#2f4f3a' : '#79b86a';
    for (var x = 0; x < W; x++) { var hy = 58 + Math.round(Math.sin(x / 40) * 6 + Math.sin(x / 13) * 2); g.fillRect(x, hy, 1, 80 - hy); }
    // grass
    var grassA = night ? '#3e6b43' : '#7cc46b', grassB = night ? '#365f3b' : '#6db55d', grassC = night ? '#4a7a4c' : '#8fd27b';
    R(0, 74, W, H - 74, grassA);
    for (var i = 0; i < 1600; i++) { var gx = Math.floor(rnd() * W), gy = 76 + Math.floor(rnd() * (H - 76)); R(gx, gy, 1, 2, rnd() < 0.5 ? grassB : grassC); }
    // path: loop around the fountain and down to the bottom
    var pathA = night ? '#9b8a6e' : '#e3c99a', pathB = night ? '#857558' : '#cdb07c';
    R(0, 196, W, 26, pathA); R(0, 196, W, 2, pathB); R(0, 220, W, 2, pathB);
    R(222, 112, 36, 86, pathA); R(222, 112, 2, 84, pathB); R(256, 112, 2, 84, pathB);
    for (var p = 0; p < 160; p++) R(Math.floor(rnd() * W), 199 + Math.floor(rnd() * 20), 2, 1, pathB);
    // pond (left)
    var water = night ? '#2d4f8a' : '#5fb6e6', waterL = night ? '#4a6fb0' : '#9ad6f5';
    for (var py = 0; py < 30; py++) { var hw = Math.round(62 * Math.sqrt(1 - Math.pow((py - 15) / 15, 2))); R(84 - hw, 88 + py, hw * 2, 1, water); }
    R(56, 96, 18, 1, waterL); R(92, 104, 22, 1, waterL); R(70, 110, 14, 1, waterL);
    R(40, 116, 90, 2, night ? '#2a4a30' : '#5a9a4f');
    // lily pads
    [[60, 100], [100, 94], [110, 108]].forEach(function (l) { R(l[0], l[1], 6, 3, '#4f9a45'); R(l[0] + 2, l[1] - 1, 2, 1, '#f7a8c8'); });
    // fountain (centre)
    var stone = night ? '#8a8aa0' : '#c9c6d6', stoneD = night ? '#66667a' : '#9e9ab0';
    R(212, 96, 56, 18, stoneD); R(214, 94, 52, 16, stone); R(218, 98, 44, 8, water);
    R(236, 70, 8, 26, stone); R(234, 68, 12, 4, stoneD); R(239, 58, 2, 10, waterL); R(232, 60, 2, 8, waterL); R(246, 60, 2, 8, waterL);
    // trees
    function tree(tx, ty, sz) {
      R(tx - 2, ty, 5, 18, night ? '#4a3626' : '#8a5a3a');
      var leaf = night ? ['#25502f', '#2f6338', '#3b7444'] : ['#3f8f4a', '#4fa857', '#6cc46c'];
      for (var yy = -sz; yy <= sz; yy++) { var ww = Math.round(Math.sqrt(sz * sz - yy * yy)); R(tx - ww, ty - sz + yy, ww * 2, 1, leaf[yy < -sz / 3 ? 2 : yy < sz / 3 ? 1 : 0]); }
    }
    [[20, 92, 14], [168, 84, 16], [310, 86, 15], [356, 94, 12], [452, 88, 16], [400, 78, 11]].forEach(function (t) { tree(t[0], t[1], t[2]); });
    // benches
    function bench(bx, by) { var wood = night ? '#7a5638' : '#b07a4f'; R(bx, by, 30, 3, wood); R(bx, by + 5, 30, 3, wood); R(bx + 2, by + 8, 2, 6, '#5a4030'); R(bx + 26, by + 8, 2, 6, '#5a4030'); R(bx, by - 6, 30, 3, wood); }
    bench(150, 114); bench(300, 114); bench(380, 116);
    // lamp posts
    [[200, 92], [280, 92]].forEach(function (l) { R(l[0], l[1], 2, 34, '#3d3a50'); R(l[0] - 3, l[1] - 4, 8, 5, night ? '#ffe9a0' : '#f4e7b0'); if (night) { g.fillStyle = 'rgba(255,233,160,.18)'; g.fillRect(l[0] - 12, l[1] - 8, 26, 50); } });
    // flower beds
    var fl = ['#f7a8c8', '#ffe36e', '#ffffff', '#c7a6ff', '#ff8f8f'];
    for (var f = 0; f < 90; f++) { var fx = Math.floor(rnd() * W), fy = 132 + Math.floor(rnd() * 130); if (fy > 192 && fy < 226) continue; if (fx > 218 && fx < 262 && fy < 198) continue; R(fx, fy, 2, 2, fl[f % fl.length]); R(fx, fy + 2, 1, 2, grassB); }
    // fence at the very back
    for (var fx2 = 0; fx2 < W; fx2 += 8) R(fx2, 70, 2, 8, night ? '#b8b0c8' : '#fff8ec');
    R(0, 72, W, 1, night ? '#b8b0c8' : '#fff8ec');
    return c;
  }

  /* ---------------- players ---------------- */
  function newPlayer(id, data) {
    return { id: id, x: data.x || 240, y: data.y || 230, tx: data.x || 240, ty: data.y || 230, facing: 1, look: cleanLook(data.look), na: data.na | 0, nb: data.nb | 0,
      say: -1, sayUntil: 0, emo: null, emoUntil: 0, hopUntil: 0, seen: data.seen || Date.now(), sayAt: data.sayAt || 0, emoAt: data.emoAt || 0, hopAt: data.hopAt || 0, to: '' };
  }
  function applyRemote(p, d) {
    var t = clampWalk(+d.x || p.tx, +d.y || p.ty); p.tx = t[0]; p.ty = t[1];
    p.look = cleanLook(d.look); p.na = d.na | 0; p.nb = d.nb | 0; p.seen = +d.seen || p.seen;
    var now = performance.now();
    if ((+d.sayAt || 0) > p.sayAt && d.say >= 0 && d.say < PHRASES.length + 1) { p.sayAt = +d.sayAt; p.say = d.say | 0; p.to = typeof d.to === 'string' ? d.to : ''; p.sayUntil = now + 4500; }
    if ((+d.emoAt || 0) > p.emoAt && EMOTES.indexOf(d.emo) >= 0) { p.emoAt = +d.emoAt; p.emo = d.emo; p.emoUntil = now + 3500; }
    if ((+d.hopAt || 0) > p.hopAt) { p.hopAt = +d.hopAt; p.hopUntil = now + 2400; }
  }
  function phraseText(p) {
    if (p.say === PHRASES.length) { // "Hi, <name>!" aimed at another player
      var t = p.to === (me && me.id) ? me : others[p.to];
      return 'Hi, ' + (t ? nameOf(t.na, t.nb).split(' ')[1] : 'friend') + '! 👋';
    }
    return PHRASES[p.say] || '';
  }

  /* ---------------- online sync (Firestore) ---------------- */
  function docRef() { return firebase.firestore().collection('explore').doc(me.id); }
  function write(fields, now) {
    if (!online) return;
    pendingWrite = Object.assign(pendingWrite || {}, fields);
    var wait = Math.max(0, 400 - (Date.now() - lastWrite));
    clearTimeout(writeTimer);
    writeTimer = setTimeout(function () {
      var data = Object.assign({ seen: Date.now() }, pendingWrite); pendingWrite = null; lastWrite = Date.now();
      docRef().set(data, { merge: true }).catch(fail);
    }, now ? 0 : wait);
  }
  function fail(e) {
    console.warn('CozyNook explore offline', e && e.code);
    if (!online) return;
    online = false; if (unsub) { unsub(); unsub = null; }
    setStatus(e && e.code === 'permission-denied' ? 'The online park isn\'t switched on yet, so you\'re exploring on your own for now.' : 'Can\'t reach the online park right now. You\'re exploring on your own.');
  }
  function subscribe() {
    if (unsub) unsub();
    unsub = firebase.firestore().collection('explore').where('seen', '>', Date.now() - STALE_MS).orderBy('seen', 'desc').limit(40)
      .onSnapshot(function (snap) {
        snap.docChanges().forEach(function (ch) {
          var id = ch.doc.id; if (id === me.id) return;
          if (ch.type === 'removed') { delete others[id]; return; }
          var d = ch.doc.data();
          if (!others[id]) { others[id] = newPlayer(id, d); others[id].x = others[id].tx; others[id].y = others[id].ty; }
          applyRemote(others[id], d);
        });
        updateCount();
      }, fail);
  }
  function goOnline() {
    var user = window.CozyCloud && CozyCloud.user && CozyCloud.user();
    if (!user || !window.firebase || !firebase.firestore) { setStatus('Sign in to meet other players. You can still explore on your own.'); return; }
    online = true;
    docRef().set({ x: Math.round(me.x), y: Math.round(me.y), look: me.look, na: me.na, nb: me.nb, say: -1, sayAt: 0, emo: 'happy', emoAt: 0, hopAt: 0, to: '', seen: Date.now() })
      .then(function () { if (!online) return; setStatus(''); subscribe(); }).catch(fail);
    beat = setInterval(function () { write({}, true); }, BEAT_MS);
    resub = setInterval(function () { if (online) subscribe(); }, 5 * 60000);
  }
  function goOffline() {
    clearInterval(beat); clearInterval(resub); clearTimeout(writeTimer);
    if (unsub) { unsub(); unsub = null; }
    if (online && me) docRef().delete().catch(function () {});
    online = false; others = {};
  }

  /* ---------------- actions ---------------- */
  function moveTo(x, y) {
    var t = clampWalk(x, y); me.tx = t[0]; me.ty = t[1];
    write({ x: Math.round(t[0]), y: Math.round(t[1]) });
  }
  function say(i, to) {
    var now = performance.now(); me.say = i; me.to = to || ''; me.sayUntil = now + 4500; me.sayAt = Date.now();
    write({ say: i, sayAt: me.sayAt, to: me.to }, true);
  }
  function emote(e) { me.emo = e; me.emoUntil = performance.now() + 3500; me.emoAt = Date.now(); write({ emo: e, emoAt: me.emoAt }, true); }
  function dance() { me.hopUntil = performance.now() + 2400; me.hopAt = Date.now(); write({ hopAt: me.hopAt }, true); }

  /* ---------------- drawing ---------------- */
  function bubble(text, cx, top) {
    ctx.font = '700 7px Nunito, sans-serif';
    var w = Math.ceil(ctx.measureText(text).width) + 10, x = Math.round(cx - w / 2), y = Math.round(top - 14);
    x = Math.max(2, Math.min(W - w - 2, x));
    ctx.fillStyle = '#302b46'; ctx.fillRect(x - 1, y - 1, w + 2, 13); ctx.fillRect(Math.round(cx) - 2, y + 11, 4, 3);
    ctx.fillStyle = '#fffdf8'; ctx.fillRect(x, y, w, 11); ctx.fillRect(Math.round(cx) - 1, y + 11, 2, 2);
    ctx.fillStyle = '#302b46'; ctx.textBaseline = 'middle'; ctx.fillText(text, x + 5, y + 6);
  }
  function tag(text, cx, y, mine) {
    ctx.font = '800 6px Nunito, sans-serif';
    var w = Math.ceil(ctx.measureText(text).width) + 6, x = Math.round(cx - w / 2);
    ctx.fillStyle = mine ? 'rgba(35,185,133,.9)' : 'rgba(48,43,70,.75)'; ctx.fillRect(x, y, w, 9);
    ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(text, x + 3, y + 5);
  }
  function drawPlayer(p, now, mine) {
    var FIG = CozySprites.FIG, moving = Math.abs(p.tx - p.x) + Math.abs(p.ty - p.y) > 0.6;
    var step = moving ? (Math.floor(now / 150) % 2) + 1 : 0;
    var hop = now < p.hopUntil ? -Math.abs(Math.sin(now / 110)) * 6 : 0;
    var fig = CozySprites.figureCanvas(p.look, step); if (!fig) return;
    var x = Math.round(p.x - FIG[0] / 2), y = Math.round(p.y - FIG[2] + hop);
    ctx.fillStyle = 'rgba(30,40,30,.25)'; ctx.fillRect(Math.round(p.x) - 11, Math.round(p.y) - 1, 22, 3);
    if (p.facing < 0) { ctx.save(); ctx.translate(x + FIG[0], y); ctx.scale(-1, 1); ctx.drawImage(fig, 0, 0); ctx.restore(); }
    else ctx.drawImage(fig, x, y);
    var head = y + 2;
    tag(nameOf(p.na, p.nb) + (mine ? ' (you)' : ''), p.x, Math.round(p.y) + 3, mine);
    if (now < p.sayUntil) bubble(phraseText(p), p.x, head);
    else if (now < p.emoUntil && p.emo) CozySprites.emoteIcon(ctx, p.emo, Math.round(p.x) + 10, head - 6);
  }
  function step(p, dt) {
    var dx = p.tx - p.x, dy = p.ty - p.y, d = Math.sqrt(dx * dx + dy * dy);
    if (d < 0.6) { p.x = p.tx; p.y = p.ty; return; }
    if (Math.abs(dx) > 0.5) p.facing = dx > 0 ? 1 : -1;
    var s = Math.min(d, SPEED * dt); p.x += dx / d * s; p.y += dy / d * s;
  }
  var lastT = 0;
  function frame(t) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    var dt = lastT ? Math.min(0.1, (t - lastT) / 1000) : 0; lastT = t;
    // keyboard walking
    var kx = (keysDown.ArrowRight || keysDown.d ? 1 : 0) - (keysDown.ArrowLeft || keysDown.a ? 1 : 0);
    var ky = (keysDown.ArrowDown || keysDown.s ? 1 : 0) - (keysDown.ArrowUp || keysDown.w ? 1 : 0);
    if (kx || ky) { var t2 = clampWalk(me.x + kx * 30, me.y + ky * 20); me.tx = t2[0]; me.ty = t2[1]; }
    var nowMs = Date.now();
    Object.keys(others).forEach(function (id) { if (nowMs - others[id].seen > STALE_MS) delete others[id]; });
    step(me, dt); Object.keys(others).forEach(function (id) { step(others[id], dt); });
    ctx.setTransform(SCALE, 0, 0, SCALE, 0, 0); ctx.imageSmoothingEnabled = false;
    if (bg) ctx.drawImage(bg, 0, 0);
    var list = Object.keys(others).map(function (id) { return others[id]; }); list.push(me);
    list.sort(function (a, b) { return a.y - b.y; }).forEach(function (p) { drawPlayer(p, t, p === me); });
  }

  /* ---------------- UI ---------------- */
  function setStatus(msg) { var s = $('exStatus'); if (s) { s.textContent = msg; s.hidden = !msg; } }
  function updateCount() { var c = $('exCount'); if (c) { var n = Object.keys(others).length; c.textContent = online ? (n ? n + ' other player' + (n === 1 ? '' : 's') + ' here' : 'Nobody else here yet') : 'Exploring on your own'; } }
  function build() {
    overlay = document.createElement('div'); overlay.className = 'explore'; overlay.id = 'explore'; overlay.hidden = true;
    overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-label', 'Outside: the park');
    overlay.innerHTML =
      '<div class="ex-card">' +
        '<div class="ex-top"><b class="ex-title">Outside · Cozy Park</b><span class="ex-count" id="exCount"></span><button type="button" class="ex-close" id="exClose" aria-label="Go back inside">Go inside ✕</button></div>' +
        '<div class="ex-stage"><canvas id="exCanvas" width="' + (W * SCALE) + '" height="' + (H * SCALE) + '" aria-label="The park. Tap somewhere to walk there. Tap another player to say hi."></canvas><p class="ex-status" id="exStatus" hidden></p></div>' +
        '<div class="ex-bar"><div class="ex-group" id="exEmotes" aria-label="Emotes"></div><button type="button" class="ex-dance" id="exDance">Dance</button></div>' +
        '<div class="ex-phrases" id="exPhrases" aria-label="Say something"></div>' +
        '<p class="ex-hint">Tap the grass to walk (or use the arrow keys). Tap another player to walk over and say hi. Your name: <b id="exName"></b> <button type="button" class="ex-link" id="exRename">New name</button></p>' +
      '</div>' +
      '<div class="ex-lock" id="exLock" hidden><div class="panel wb-card"><h3 id="exLockTitle">Outside is locked</h3><p id="exLockText"></p><div class="wb-actions"><button class="primary-btn" type="button" id="exLockOk">OK</button></div></div></div>';
    document.body.appendChild(overlay);
    canvas = $('exCanvas'); ctx = canvas.getContext('2d');
    var em = $('exEmotes');
    EMOTES.forEach(function (e) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'ex-emote'; b.title = e; b.setAttribute('aria-label', 'Emote: ' + e);
      var c = document.createElement('canvas'); c.width = 16; c.height = 18; b.appendChild(c);
      CozySprites.whenReady(function () { CozySprites.emoteIcon(c.getContext('2d'), e, 0, 0); });
      b.addEventListener('click', function () { emote(e); }); em.appendChild(b);
    });
    var ph = $('exPhrases');
    PHRASES.forEach(function (t, i) { var b = document.createElement('button'); b.type = 'button'; b.textContent = t; b.addEventListener('click', function () { say(i); }); ph.appendChild(b); });
    $('exDance').addEventListener('click', dance);
    $('exClose').addEventListener('click', close);
    $('exLockOk').addEventListener('click', close);
    $('exRename').addEventListener('click', function () {
      me.na = Math.floor(Math.random() * ADJ.length); me.nb = Math.floor(Math.random() * ANIMAL.length);
      var a = app(); if (a.setData) a.setData('exploreName', [me.na, me.nb]);
      $('exName').textContent = nameOf(me.na, me.nb); write({ na: me.na, nb: me.nb }, true);
    });
    canvas.addEventListener('pointerdown', function (e) {
      var r = canvas.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * W, y = (e.clientY - r.top) / r.height * H;
      // tapped another player? walk next to them and say hi
      var FIG = CozySprites.FIG, hit = null;
      Object.keys(others).forEach(function (id) { var p = others[id]; if (x > p.x - 14 && x < p.x + 14 && y > p.y - FIG[2] + 14 && y < p.y + 4) hit = p; });
      if (hit) { moveTo(hit.x + (me.x < hit.x ? -26 : 26), hit.y); say(PHRASES.length, hit.id); return; }
      moveTo(x, y);
    });
    document.addEventListener('keydown', function (e) {
      if (!running) return;
      if (e.key === 'Escape') { close(); return; }
      if (/^(Arrow(Up|Down|Left|Right)|[wasd])$/.test(e.key) && !(e.target.closest && e.target.closest('input,textarea'))) { keysDown[e.key] = true; e.preventDefault(); }
    });
    document.addEventListener('keyup', function (e) {
      if (!keysDown[e.key]) return; delete keysDown[e.key];
      if (!Object.keys(keysDown).length) write({ x: Math.round(me.tx), y: Math.round(me.ty) });
    });
    setInterval(function () { if (running && Object.keys(keysDown).length) write({ x: Math.round(me.tx), y: Math.round(me.ty) }); }, 700);
    window.addEventListener('pagehide', function () { if (running) goOffline(); });
  }

  function showLock(title, text) {
    overlay.hidden = false; overlay.classList.add('locked');
    $('exLockTitle').textContent = title; $('exLockText').textContent = text; $('exLock').hidden = false;
    setTimeout(function () { $('exLockOk').focus(); }, 50);
  }
  function open() {
    if (!overlay) build();
    var lv = level();
    if (lv < LEVEL_NEEDED) {
      showLock('Outside unlocks at level ' + LEVEL_NEEDED, 'You\'re level ' + lv + '. Finish tasks, focus sessions and mini games to earn XP. When you reach level ' + LEVEL_NEEDED + ', click the window to go outside and meet other players in the park!');
      return;
    }
    overlay.classList.remove('locked'); $('exLock').hidden = true; overlay.hidden = false;
    document.body.classList.add('exploring');
    var user = window.CozyCloud && CozyCloud.user && CozyCloud.user();
    var idx = myNameIdx(user ? user.uid : 'guest');
    var start = clampWalk(200 + Math.random() * 80, 236 + Math.random() * 20);
    me = newPlayer(user ? user.uid : 'me', { x: start[0], y: start[1] }); me.look = myLook(); me.na = idx[0]; me.nb = idx[1];
    $('exName').textContent = nameOf(me.na, me.nb);
    CozySprites.whenReady(function () { bg = drawPark(); });
    others = {}; setStatus(''); updateCount();
    running = true; lastT = 0; raf = requestAnimationFrame(frame);
    goOnline(); updateCount();
  }
  function close() {
    if (overlay.classList.contains('locked')) { overlay.hidden = true; $('exLock').hidden = true; overlay.classList.remove('locked'); return; }
    running = false; cancelAnimationFrame(raf); keysDown = {};
    goOffline(); overlay.hidden = true; document.body.classList.remove('exploring');
  }

  window.CozyExplore = { open: open, close: close, LEVEL_NEEDED: LEVEL_NEEDED, _state: function () { return { me: me, others: others, online: online }; } };
})();
