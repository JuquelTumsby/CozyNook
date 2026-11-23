/* CozyNook gifts: the game owner can send coins, XP or decorations to one player
   (found by Player ID or email) or to everyone. Players see a popup and collect each
   gift once. Who may send is decided by the Firestore rules (isAdmin), not by this file. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var app = function () { return window.CozyApp || {}; };
  var db = function () { return firebase.firestore(); };
  var current = null, isAdmin = false, queue = [], showing = false, recheck = 0;

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function playerId(uid) { return uid.slice(0, 8).toUpperCase(); }
  function describe(g) {
    var parts = [];
    if (g.coins) parts.push('+' + g.coins + ' coins');
    if (g.xp) parts.push('+' + g.xp + ' XP');
    if (g.decor) parts.push(g.decor);
    return parts.join(' · ') || 'A little surprise';
  }

  /* ---------- player side ---------- */
  function checkGifts() {
    if (!current) return;
    db().collection('gifts').where('to', 'in', [current.uid, 'all']).get().then(function (snap) {
      var claimed = (app().getData && app().getData('claimedGifts')) || [];
      snap.forEach(function (d) {
        if (claimed.indexOf(d.id) < 0 && !queue.some(function (q) { return q.id === d.id; })) queue.push({ id: d.id, g: d.data() });
      });
      queue.sort(function (a, b) { return (a.g.at || 0) - (b.g.at || 0); });
      showNext();
    }).catch(function (e) { console.warn('CozyNook gifts unavailable', e && e.code); });
  }
  function showNext() {
    if (showing || !queue.length) return;
    if (!document.querySelector('#accountModal[hidden]') || !document.querySelector('#welcomeBack[hidden]')) { setTimeout(showNext, 1500); return; }
    showing = true;
    var item = queue[0];
    $('giftMsg').textContent = item.g.msg || 'A little something from CozyNook!';
    $('giftWhat').textContent = describe(item.g);
    $('giftPopup').hidden = false;
    setTimeout(function () { $('giftCollect').focus(); }, 50);
  }
  function collect() {
    var item = queue.shift(); if (!item) return;
    if (app().claimGift) app().claimGift(item.id, item.g);
    $('giftPopup').hidden = true; showing = false;
    setTimeout(showNext, 600);
  }

  /* ---------- owner (admin) side ---------- */
  var found = null;
  function setAdminMsg(t, ok) { var m = $('gaMsg'); m.textContent = t || ''; m.classList.toggle('ok', !!ok); m.hidden = !t; }
  function openAdmin() {
    var acct = $('accountModal'); if (acct) acct.hidden = true;
    $('giftAdmin').hidden = false; setAdminMsg(''); refreshTarget(); loadSent();
  }
  function refreshTarget() {
    var one = $('gaOne').checked;
    $('gaFindRow').hidden = !one;
    if (!one) { $('gaFound').textContent = 'Everyone will get this gift the next time they open CozyNook (including new players).'; }
    else $('gaFound').textContent = found ? 'Sending to: ' + found.email + ' (Player ID ' + found.id + ')' : 'Type a Player ID or email, then press Find.';
  }
  function findPlayer() {
    var q = ($('gaWho').value || '').trim(); found = null; refreshTarget();
    if (!q) { setAdminMsg('Type a Player ID or an email first.'); return; }
    var query = q.indexOf('@') > 0 ? db().collection('players').where('email', '==', q.toLowerCase()) : db().collection('players').where('id', '==', q.toUpperCase());
    query.limit(5).get().then(function (snap) {
      if (snap.empty) { setAdminMsg('No player found. They need to sign in to CozyNook at least once after this update.'); return; }
      var d = snap.docs[0]; found = { uid: d.id, id: d.data().id, email: d.data().email };
      setAdminMsg(snap.size > 1 ? 'More than one match — sending to the first one. Use their email to be sure.' : 'Player found!', snap.size === 1);
      refreshTarget();
    }).catch(function (e) { setAdminMsg('Couldn\'t search players (' + (e && e.code) + ').'); });
  }
  function sendGift() {
    var one = $('gaOne').checked;
    if (one && !found) { setAdminMsg('Find the player first.'); return; }
    var coins = Math.max(0, Math.min(100000, parseInt($('gaCoins').value, 10) || 0));
    var xp = Math.max(0, Math.min(100000, parseInt($('gaXp').value, 10) || 0));
    var decor = $('gaDecor').value || '';
    var msg = ($('gaText').value || '').trim().slice(0, 140);
    if (!coins && !xp && !decor) { setAdminMsg('Add some coins, XP or a decoration to the gift.'); return; }
    var data = { to: one ? found.uid : 'all', coins: coins, xp: xp, decor: decor, msg: msg, at: Date.now() };
    $('gaSend').disabled = true;
    db().collection('gifts').add(data).then(function () {
      setAdminMsg('Gift sent to ' + (one ? found.email : 'everyone') + '! 🎁', true);
      $('gaCoins').value = ''; $('gaXp').value = ''; $('gaDecor').value = ''; $('gaText').value = '';
      loadSent();
    }).catch(function (e) { setAdminMsg('Couldn\'t send the gift (' + (e && e.code) + ').'); })
      .then(function () { $('gaSend').disabled = false; });
  }
  var who = {};
  function loadSent() {
    var list = $('gaSent');
    db().collection('gifts').orderBy('at', 'desc').limit(15).get().then(function (snap) {
      list.innerHTML = snap.empty ? '<p class="subtle">No gifts sent yet.</p>' : '';
      snap.forEach(function (d) {
        var g = d.data(), row = document.createElement('div'); row.className = 'ga-row';
        var to = g.to === 'all' ? 'Everyone' : (who[g.to] || 'Player ' + playerId(g.to));
        row.innerHTML = '<div><b>' + esc(to) + '</b> · ' + esc(describe(g)) + '<br><small>' + esc(g.msg || '') + ' · ' + new Date(g.at).toLocaleDateString() + '</small></div><button type="button">Delete</button>';
        row.querySelector('button').addEventListener('click', function () {
          d.ref.delete().then(loadSent).catch(function (e) { setAdminMsg('Couldn\'t delete (' + (e && e.code) + ').'); });
        });
        list.appendChild(row);
        if (g.to !== 'all' && !who[g.to]) db().collection('players').doc(g.to).get().then(function (p) { if (p.exists) { who[g.to] = p.data().email; loadSentNames(); } });
      });
    }).catch(function (e) { list.innerHTML = '<p class="subtle">Couldn\'t load sent gifts (' + esc(e && e.code) + ').</p>'; });
  }
  var namesTimer = 0;
  function loadSentNames() { clearTimeout(namesTimer); namesTimer = setTimeout(loadSent, 400); }

  /* ---------- sign-in hook ---------- */
  function onUser(u) {
    current = u; isAdmin = false; queue = []; clearInterval(recheck);
    var btn = $('acctAdmin'); if (btn) btn.hidden = true;
    if (!u || !window.firebase) return;
    // directory entry so the owner can find this player
    db().collection('players').doc(u.uid).set({ id: playerId(u.uid), email: (u.email || '').toLowerCase() }).catch(function () {});
    // only the owner is allowed to read the directory
    db().collection('players').limit(1).get().then(function () { isAdmin = true; if (btn) btn.hidden = false; }).catch(function () {});
    setTimeout(checkGifts, 1200);
    recheck = setInterval(checkGifts, 5 * 60000);
  }
  function start() {
    $('giftCollect').addEventListener('click', collect);
    $('acctAdmin').addEventListener('click', openAdmin);
    $('gaClose').addEventListener('click', function () { $('giftAdmin').hidden = true; });
    $('gaAll').addEventListener('change', refreshTarget); $('gaOne').addEventListener('change', refreshTarget);
    $('gaFind').addEventListener('click', findPlayer);
    $('gaWho').addEventListener('keydown', function (e) { if (e.key === 'Enter') findPlayer(); });
    $('gaSend').addEventListener('click', sendGift);
    var sel = $('gaDecor'), names = (app().decorNames && app().decorNames()) || [];
    names.forEach(function (n) { var o = document.createElement('option'); o.value = n; o.textContent = n; sel.appendChild(o); });
    var last = null;
    setInterval(function () {
      var u = window.CozyCloud && CozyCloud.user ? CozyCloud.user() : null;
      if ((u && u.uid) !== (last && last.uid)) { last = u; onUser(u); }
    }, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.CozyGifts = { check: checkGifts, _state: function () { return { user: !!current, admin: isAdmin, queued: queue.length, showing: showing }; } };
})();
