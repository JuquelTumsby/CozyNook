/* CozyNook mini games for the Little Reset page:
   - Word Nook: one 5-letter word a day, 6 guesses.
   - Cozy Match: flip cards to find the pixel pairs.
   Progress lives in the main save (so it syncs with the account) via window.CozyApp. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var app = function () { return window.CozyApp || {}; };
  var get = function (k, d) { var a = app(); var v = a.getData ? a.getData(k) : undefined; return v === undefined || v === null ? d : v; };
  var set = function (k, v) { var a = app(); if (a.setData) a.setData(k, v); };
  var earn = function (c, xp, msg) { var a = app(); if (a.earn) a.earn(c, xp, msg); };
  var toast = function (m) { var a = app(); if (a.toast) a.toast(m); };
  var todayKey = function () { var d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); };
  function untilMidnight() {
    var n = new Date(), m = new Date(n); m.setHours(24, 0, 0, 0);
    var mins = Math.max(0, Math.round((m - n) / 60000));
    return Math.floor(mins / 60) + 'h ' + (mins % 60) + 'm';
  }

  /* ======================= Word Nook ======================= */
  var W = window.COZY_WORDS || { answers: '', valid: '' };
  var ANSWERS = W.answers.split(' ').filter(Boolean);
  var VALID = new Set();
  for (var i = 0; i + 5 <= W.valid.length; i += 5) VALID.add(W.valid.substr(i, 5));
  ANSWERS.forEach(function (a) { VALID.add(a); });
  var ROWS = 6, LEN = 5;
  var word = { answer: '', guesses: [], current: '', done: false, won: false };

  function dayNumber() { var d = new Date(); return Math.floor((Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) - Date.UTC(2026, 0, 1)) / 864e5); }
  function todaysAnswer() { var n = dayNumber(); return ANSWERS[((n % ANSWERS.length) + ANSWERS.length) % ANSWERS.length] || 'cozy'; }

  // Colour a guess like the classic rules: green = right spot, yellow = in the word, grey = not in it.
  function score(guess, answer) {
    var res = ['miss', 'miss', 'miss', 'miss', 'miss'], left = {};
    for (var i = 0; i < LEN; i++) { if (guess[i] === answer[i]) res[i] = 'hit'; else left[answer[i]] = (left[answer[i]] || 0) + 1; }
    for (var j = 0; j < LEN; j++) { if (res[j] !== 'hit' && left[guess[j]]) { res[j] = 'near'; left[guess[j]]--; } }
    return res;
  }

  function loadWord() {
    var saved = get('wordGame', null), today = todayKey();
    word.answer = todaysAnswer();
    if (saved && saved.day === today) { word.guesses = saved.guesses || []; word.done = !!saved.done; word.won = !!saved.won; }
    else { word.guesses = []; word.done = false; word.won = false; }
    word.current = '';
  }
  function saveWord() { set('wordGame', { day: todayKey(), guesses: word.guesses, done: word.done, won: word.won }); }

  function buildWord() {
    var host = $('wordGame'); if (!host || host._built) return;
    host._built = true;
    var grid = document.createElement('div'); grid.className = 'wn-grid'; grid.id = 'wnGrid';
    for (var r = 0; r < ROWS; r++) {
      var row = document.createElement('div'); row.className = 'wn-row';
      for (var c = 0; c < LEN; c++) { var t = document.createElement('div'); t.className = 'wn-tile'; row.appendChild(t); }
      grid.appendChild(row);
    }
    var msg = document.createElement('p'); msg.className = 'wn-msg'; msg.id = 'wnMsg'; msg.setAttribute('role', 'status');
    var kb = document.createElement('div'); kb.className = 'wn-keys'; kb.id = 'wnKeys';
    ['qwertyuiop', 'asdfghjkl', '+zxcvbnm-'].forEach(function (line) {
      var row = document.createElement('div'); row.className = 'wn-krow';
      line.split('').forEach(function (ch) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'wn-key';
        if (ch === '+') { b.textContent = 'Enter'; b.dataset.key = 'Enter'; b.classList.add('wide'); }
        else if (ch === '-') { b.textContent = '⌫'; b.dataset.key = 'Backspace'; b.classList.add('wide'); b.setAttribute('aria-label', 'Delete letter'); }
        else { b.textContent = ch; b.dataset.key = ch; }
        row.appendChild(b);
      });
      kb.appendChild(row);
    });
    host.appendChild(grid); host.appendChild(msg); host.appendChild(kb);
    kb.addEventListener('click', function (e) { var b = e.target.closest('[data-key]'); if (b) press(b.dataset.key); });
    document.addEventListener('keydown', function (e) {
      var view = $('view-reset');
      if (!view || !view.classList.contains('active') || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.target.closest && e.target.closest('input, textarea, select, [contenteditable]')) return;
      if (!document.querySelector('.welcome-back:not([hidden])') && (e.key === 'Enter' || e.key === 'Backspace' || /^[a-zA-Z]$/.test(e.key))) {
        if (e.key === 'Enter' && e.target.closest && e.target.closest('#view-reset button') && !e.target.closest('#wnKeys')) return;   // let other buttons on this page work
        e.preventDefault(); press(e.key.length === 1 ? e.key.toLowerCase() : e.key);
      }
    });
  }

  function paintWord(revealRow) {
    var grid = $('wnGrid'); if (!grid) return;
    var keyState = {};
    for (var r = 0; r < ROWS; r++) {
      var row = grid.children[r], g = word.guesses[r], marks = g ? score(g, word.answer) : null;
      var text = g || (r === word.guesses.length && !word.done ? word.current : '');
      for (var c = 0; c < LEN; c++) {
        var t = row.children[c], ch = text[c] || '';
        t.textContent = ch;
        t.className = 'wn-tile' + (ch ? ' filled' : '') + (marks ? ' ' + marks[c] : '') + (marks && r === revealRow ? ' reveal' : '');
        if (marks && r === revealRow) t.style.animationDelay = (c * 0.12) + 's'; else t.style.animationDelay = '';
        t.setAttribute('aria-label', ch ? ch.toUpperCase() + (marks ? (marks[c] === 'hit' ? ', right spot' : marks[c] === 'near' ? ', wrong spot' : ', not in word') : '') : 'empty');
        if (marks) { var rank = { miss: 1, near: 2, hit: 3 }; if (!keyState[ch] || rank[marks[c]] > rank[keyState[ch]]) keyState[ch] = marks[c]; }
      }
    }
    document.querySelectorAll('#wnKeys .wn-key').forEach(function (k) {
      var s = keyState[k.dataset.key]; k.classList.remove('hit', 'near', 'miss'); if (s) k.classList.add(s);
    });
    var msg = $('wnMsg');
    if (word.done) msg.innerHTML = word.won
      ? '<b>You got it!</b> The word was <b>' + word.answer.toUpperCase() + '</b>. New word in ' + untilMidnight() + '.'
      : 'So close! The word was <b>' + word.answer.toUpperCase() + '</b>. Try a new one in ' + untilMidnight() + '.';
    else if (!word.guesses.length && !word.current) msg.textContent = 'Guess today\'s 5-letter word. You have 6 tries!';
    var st = get('wordStats', { streak: 0, best: 0, wins: 0 });
    var info = $('wnStats'); if (info) info.textContent = 'Streak: ' + (st.streak || 0) + ' day' + (st.streak === 1 ? '' : 's') + ' · Wins: ' + (st.wins || 0);
  }

  function say(text) { var m = $('wnMsg'); if (m) m.textContent = text; }
  function shake() { var row = $('wnGrid').children[word.guesses.length]; if (!row) return; row.classList.remove('shake'); void row.offsetWidth; row.classList.add('shake'); }

  function press(key) {
    if (word.done) { say('You\'ve played today\'s word! A new one comes in ' + untilMidnight() + '.'); return; }
    if (key === 'Backspace') { word.current = word.current.slice(0, -1); paintWord(); return; }
    if (key === 'Enter') { submit(); return; }
    if (/^[a-z]$/.test(key) && word.current.length < LEN) { word.current += key; paintWord(); }
  }

  function submit() {
    var g = word.current;
    if (g.length < LEN) { say('Not enough letters. Words have 5 letters.'); shake(); return; }
    if (!VALID.has(g)) { say('"' + g.toUpperCase() + '" isn\'t in our word list. Try another word!'); shake(); return; }
    word.guesses.push(g); word.current = '';
    var row = word.guesses.length - 1;
    if (g === word.answer) {
      word.done = true; word.won = true;
      var tries = word.guesses.length, coins = 10 + (ROWS - tries) * 2;
      var st = get('wordStats', { streak: 0, best: 0, wins: 0, lastWin: '' });
      var y = new Date(); y.setDate(y.getDate() - 1);
      var yKey = y.getFullYear() + '-' + (y.getMonth() + 1) + '-' + y.getDate();
      st.streak = st.lastWin === yKey ? (st.streak || 0) + 1 : 1; st.best = Math.max(st.best || 0, st.streak); st.wins = (st.wins || 0) + 1; st.lastWin = todayKey();
      set('wordStats', st);
      saveWord(); paintWord(row);
      setTimeout(function () { earn(coins, 15, 'Word Nook solved in ' + tries + '! +' + coins + ' coins 🎉'); }, 800);
      return;
    }
    if (word.guesses.length >= ROWS) {
      word.done = true;
      var st2 = get('wordStats', { streak: 0, best: 0, wins: 0 }); st2.streak = 0; set('wordStats', st2);
      saveWord(); paintWord(row);
      setTimeout(function () { earn(3, 5, 'Nice try! +3 coins for playing 🌷'); }, 800);
      return;
    }
    saveWord(); paintWord(row); say((ROWS - word.guesses.length) + ' tries left.');
  }

  /* ======================= Cozy Match ======================= */
  var ICONS = ['i-cat', 'i-heart', 'i-star', 'i-coin', 'i-moon', 'i-sun', 'i-cup', 'i-gift'];
  var match = { cards: [], open: [], found: 0, moves: 0, lock: false };

  function newMatch() {
    var deck = ICONS.concat(ICONS);
    for (var i = deck.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = deck[i]; deck[i] = deck[j]; deck[j] = t; }
    match.cards = deck.map(function (ic) { return { icon: ic, up: false, done: false }; });
    match.open = []; match.found = 0; match.moves = 0; match.lock = false;
    paintMatch();
  }
  function paintMatch() {
    var host = $('matchGrid'); if (!host) return;
    if (host.children.length !== match.cards.length) {
      host.innerHTML = '';
      match.cards.forEach(function (_, i) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'mt-card'; b.dataset.i = i;
        b.innerHTML = '<span class="mt-back" aria-hidden="true">?</span><span class="mt-face"><span class="px-icon" aria-hidden="true"></span></span>';
        host.appendChild(b);
      });
    }
    match.cards.forEach(function (c, i) {
      var b = host.children[i];
      b.classList.toggle('up', c.up || c.done); b.classList.toggle('done', c.done);
      b.querySelector('.mt-face .px-icon').className = 'px-icon ' + c.icon;
      b.setAttribute('aria-label', c.up || c.done ? c.icon.replace('i-', '') + (c.done ? ', matched' : '') : 'Hidden card');
      b.disabled = c.done;
    });
    var best = get('matchBest', 0);
    $('matchInfo').textContent = 'Moves: ' + match.moves + ' · Pairs: ' + match.found + ' / ' + ICONS.length + (best ? ' · Best: ' + best + ' moves' : '');
  }
  function flip(i) {
    var c = match.cards[i];
    if (match.lock || !c || c.up || c.done) return;
    c.up = true; match.open.push(i); paintMatch();
    if (match.open.length < 2) return;
    match.moves++;
    var a = match.cards[match.open[0]], b = match.cards[match.open[1]];
    if (a.icon === b.icon) {
      a.done = b.done = true; a.up = b.up = false; match.open = []; match.found++;
      paintMatch();
      if (match.found === ICONS.length) finishMatch();
    } else {
      match.lock = true; paintMatch();
      setTimeout(function () { a.up = b.up = false; match.open = []; match.lock = false; paintMatch(); }, 800);
    }
  }
  function finishMatch() {
    var best = get('matchBest', 0);
    if (!best || match.moves < best) set('matchBest', match.moves);
    if (get('matchDay', '') !== todayKey()) {
      set('matchDay', todayKey());
      setTimeout(function () { earn(10, 10, 'All pairs found in ' + match.moves + ' moves! +10 coins 🐾'); }, 500);
    } else {
      setTimeout(function () { toast('All pairs found in ' + match.moves + ' moves! (Coins are once a day — this one is just for fun.)'); }, 500);
    }
    paintMatch();
  }

  /* ======================= Paw Hunt ======================= */
  // Five faint pixel paw prints hidden around a picture of the player's own room.
  var PAWS = 5, paw = { found: 0, started: 0, spots: [], hintTimer: null };
  function newPawHunt() {
    var scene = $('pawScene'); if (!scene) return;
    scene.innerHTML = '';
    if (window.CozySprites && CozySprites.roomThumb) scene.appendChild(CozySprites.roomThumb(get('wallpaper', 'rose'), get('floorTheme', 'oak')));
    var spots = [], tries = 0;
    while (spots.length < PAWS && tries++ < 500) {
      var x = 7 + Math.random() * 86, y = 12 + Math.random() * 78;
      if (spots.every(function (q) { return Math.abs(q[0] - x) + Math.abs(q[1] - y) * 0.6 > 16; })) spots.push([x, y]);
    }
    paw.spots = spots.map(function (q, i) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'paw-spot';
      b.style.left = q[0] + '%'; b.style.top = q[1] + '%';
      b.setAttribute('aria-label', 'Paw print ' + (i + 1));
      b.innerHTML = '<span class="px-icon i-paw" style="transform:rotate(' + Math.round(Math.random() * 80 - 40) + 'deg)" aria-hidden="true"></span>';
      b.addEventListener('click', function () { findPaw(b); });
      scene.appendChild(b); return b;
    });
    paw.found = 0; paw.started = Date.now();
    $('pawScore').textContent = 'Found: 0 / ' + PAWS;
    $('pawHint').hidden = true;
    clearTimeout(paw.hintTimer); paw.hintTimer = setTimeout(function () { if (paw.found < PAWS) $('pawHint').hidden = false; }, 20000);
    paintPawInfo();
  }
  function paintPawInfo() { var best = get('pawBest', 0); $('pawInfo').textContent = best ? 'Best time: ' + best + 's' : ''; }
  function findPaw(b) {
    if (b.classList.contains('found')) return;
    b.classList.remove('hint'); b.classList.add('found'); b.disabled = true; paw.found++;
    if (paw.found < PAWS) { $('pawScore').textContent = 'Found: ' + paw.found + ' / ' + PAWS; return; }
    clearTimeout(paw.hintTimer); $('pawHint').hidden = true;
    var secs = Math.max(1, Math.round((Date.now() - paw.started) / 1000)), best = get('pawBest', 0);
    if (!best || secs < best) set('pawBest', secs);
    $('pawScore').textContent = 'You found all ' + PAWS + ' in ' + secs + ' seconds. Lovely noticing! 💛';
    paintPawInfo();
    if (get('pawDay', '') !== todayKey()) { set('pawDay', todayKey()); setTimeout(function () { earn(5, 5, 'Paw Hunt complete! +5 coins 🐾'); }, 400); }
  }
  function pawHint() {
    var left = paw.spots.filter(function (b) { return !b.classList.contains('found'); });
    if (!left.length) return;
    var b = left[Math.floor(Math.random() * left.length)];
    b.classList.remove('hint'); void b.offsetWidth; b.classList.add('hint');
    setTimeout(function () { b.classList.remove('hint'); }, 1900);
  }

  /* ======================= Boot ======================= */
  function start() {
    if (!$('wordGame')) return;
    loadWord(); buildWord(); paintWord();
    $('matchGrid').addEventListener('click', function (e) { var b = e.target.closest('.mt-card'); if (b) flip(+b.dataset.i); });
    $('matchNew').addEventListener('click', newMatch);
    newMatch();
    $('pawStart').addEventListener('click', newPawHunt);
    $('pawHint').addEventListener('click', pawHint);
    newPawHunt();
    // a new day while the page is open -> new word
    setInterval(function () { if (word.answer !== todaysAnswer()) { loadWord(); paintWord(); } else if (word.done) paintWord(); }, 60000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.CozyGames = { _answer: function () { return word.answer; } };
})();
