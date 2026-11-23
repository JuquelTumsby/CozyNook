/* CozyNook accounts + cloud save (Firebase Auth + Firestore).
   The game works fully without this: if Firebase can't load, players keep the
   on-device save exactly as before. Each player's save lives at users/{uid}
   and the Firestore rules only let that signed-in player read/write it. */
(function () {
  'use strict';
  var FIREBASE_CONFIG = {
    apiKey: 'AIzaSyAqGcOCxNJh6CMJ31-upUQcOB4dgYg635M',
    authDomain: 'cozynook-af006.firebaseapp.com',
    projectId: 'cozynook-af006',
    storageBucket: 'cozynook-af006.firebasestorage.app',
    messagingSenderId: '1085620571827',
    appId: '1:1085620571827:web:c336aaaa2e629fc7136ac6'
  };
  var SAVE_KEY = 'cozynook-save', META_KEY = 'cozynook-cloud';
  var SDK = ['assets/vendor/firebase-app-compat.js', 'assets/vendor/firebase-auth-compat.js', 'assets/vendor/firebase-firestore-compat.js'];

  var $ = function (id) { return document.getElementById(id); };
  var auth = null, db = null, user = null, ready = false, failed = false;
  var pushTimer = null, lastPushed = null, busy = false;

  function readMeta() { try { return JSON.parse(localStorage.getItem(META_KEY) || '{}') || {}; } catch (e) { return {}; } }
  function writeMeta(m) { try { localStorage.setItem(META_KEY, JSON.stringify(m)); } catch (e) {} }
  function localRaw() { try { return localStorage.getItem(SAVE_KEY) || '{}'; } catch (e) { return '{}'; } }
  function parse(raw) { try { return JSON.parse(raw) || {}; } catch (e) { return {}; } }
  // Compare saves without the "last visit" clock, which changes every minute.
  function fingerprint(raw) { var s = parse(raw); delete s.lastVisit; delete s.lastSeen; return JSON.stringify(s); }
  function summary(s) { return { coins: s.coins || 0, level: Math.floor((s.xp || 0) / 100) + 1, done: s.done || 0 }; }
  function isFresh(s) {
    return !(s.xp > 0 || s.done > 0 || (s.coins || 50) !== 50 || (s.decor && s.decor.length) || (s.plots || []).some(Boolean) || (s.catName && s.catName !== 'Mochi'));
  }
  function toast(msg) { if (window.CozyApp && CozyApp.toast) CozyApp.toast(msg); }

  /* ---------- UI ---------- */
  function setButton() {
    var b = $('accountBtn'); if (!b) return;
    var label = b.querySelector('.acct-label');
    b.classList.toggle('is-signed-in', !!user);
    b.classList.toggle('is-off', failed);
    if (failed) { label.textContent = 'Offline'; b.title = 'Online saving is unavailable right now. Progress is still saved on this device.'; }
    else if (user) { label.textContent = 'Saved'; b.title = 'Signed in as ' + (user.email || 'you') + '. Progress is saved to your account.'; }
    else { label.textContent = 'Sign in'; b.title = 'Sign in to keep your progress safe on any device'; }
  }
  function show(id) { ['acctOut', 'acctIn', 'acctChoose', 'acctWait'].forEach(function (p) { var el = $(p); if (el) el.hidden = p !== id; }); var x = $('acctClose'); if (x) x.hidden = id === 'acctChoose'; }
  function setMsg(text, ok) { var m = $('acctMsg'); if (!m) return; m.textContent = text || ''; m.classList.toggle('ok', !!ok); m.hidden = !text; }
  function render() {
    setButton();
    if (!$('accountModal') || busy) return;
    if (failed) { show('acctOut'); setMsg('Online saving couldn\'t load. Check your internet and refresh. Your progress is still saved on this device.'); return; }
    if (!ready) { show('acctWait'); return; }
    if (user) {
      show('acctIn');
      $('acctWho').textContent = user.displayName || user.email || 'Cozy friend';
      $('acctEmail').textContent = user.displayName ? (user.email || '') : '';
      var m = readMeta();
      $('acctSynced').textContent = m.syncedAt ? 'Last saved online: ' + new Date(m.syncedAt).toLocaleString() : 'Saving…';
    } else show('acctOut');
  }
  function open() { setMsg(''); $('accountModal').hidden = false; render(); }
  function close() { $('accountModal').hidden = true; }

  function friendly(err) {
    var c = (err && err.code) || '';
    var map = {
      'auth/invalid-email': 'That email doesn\'t look right.',
      'auth/missing-password': 'Type a password first.',
      'auth/weak-password': 'Pick a password with at least 6 characters.',
      'auth/email-already-in-use': 'That email already has an account. Press "Sign in" instead.',
      'auth/invalid-credential': 'Email or password is wrong. Try again, or press "Forgot password?".',
      'auth/wrong-password': 'Email or password is wrong.',
      'auth/user-not-found': 'No account with that email yet. Press "Create account".',
      'auth/too-many-requests': 'Too many tries. Wait a minute and try again.',
      'auth/popup-blocked': 'Your browser blocked the Google window. Allow pop-ups for this site and try again.',
      'auth/popup-closed-by-user': 'The Google window was closed before signing in.',
      'auth/cancelled-popup-request': 'The Google window was closed before signing in.',
      'auth/network-request-failed': 'No internet connection. Try again when you\'re online.',
      'auth/unauthorized-domain': 'This website isn\'t allowed to sign in yet (add it to Firebase Authorized domains).',
      'auth/operation-not-allowed': 'This sign-in method isn\'t switched on in Firebase yet.'
    };
    return map[c] || 'Something went wrong. Please try again.';
  }

  /* ---------- Cloud save ---------- */
  function docRef() { return db.collection('users').doc(user.uid); }

  function push(force) {
    if (!user || !db) return Promise.resolve();
    if (!force && readMeta().uid !== user.uid) return Promise.resolve(); // not linked yet (e.g. still choosing)
    var raw = localRaw(), fp = fingerprint(raw);
    if (!force && fp === lastPushed) return Promise.resolve();
    var now = Date.now(), s = parse(raw), sum = summary(s);
    var data = { save: raw, updatedAt: now, coins: sum.coins, level: sum.level, version: 1 };
    if (s.signInBonus) data.bonusGiven = true;
    return docRef().set(data, { merge: true })
      .then(function () {
        lastPushed = fp;
        var m = readMeta(); m.uid = user.uid; m.syncedAt = now; m.dirty = false; writeMeta(m);
        if (!$('accountModal').hidden) render();
      })
      .catch(function (e) { console.warn('CozyNook cloud save failed', e && e.code); });
  }
  function schedulePush() {
    if (!user) return;
    var m = readMeta(); if (m.uid === user.uid && !m.dirty && fingerprint(localRaw()) !== lastPushed) { m.dirty = true; writeMeta(m); }
    clearTimeout(pushTimer); pushTimer = setTimeout(function () { push(false); }, 2500);
  }
  function flush() { if (user && fingerprint(localRaw()) !== lastPushed) { clearTimeout(pushTimer); push(false); } }

  // Replace this device's save with the account's save, then reload so every screen redraws from it.
  function adopt(raw, updatedAt) {
    if (window.CozyApp) CozyApp.lock = true; // stop the game from re-saving the old state while we reload
    try { localStorage.setItem(SAVE_KEY, raw); } catch (e) {}
    writeMeta({ uid: user.uid, syncedAt: updatedAt, dirty: false, justLoaded: true });
    location.reload();
  }
  function keepLocal() { var m = readMeta(); m.uid = user.uid; writeMeta(m); return push(true); }

  // 50 coins the first time an account signs in. Remembered both in the save and on the
  // account itself, so signing out and back in (or switching devices) can't repeat it.
  function grantBonus(cloud) {
    if (!window.CozyApp || !CozyApp.grantOnce) return;
    if (cloud && cloud.bonusGiven) return;
    if (CozyApp.grantOnce('signInBonus', 50, '🎁 +50 coins for signing in! Welcome!')) { clearTimeout(pushTimer); push(true); }
  }

  function askChoice(cloud) {
    busy = true; show('acctChoose'); $('accountModal').hidden = false; setMsg('');
    var a = summary(parse(localRaw())), b = summary(parse(cloud.save));
    $('chooseLocal').querySelector('small').textContent = 'Level ' + a.level + ' · ' + a.coins + ' coins · ' + a.done + ' tasks done';
    $('chooseCloud').querySelector('small').textContent = 'Level ' + b.level + ' · ' + b.coins + ' coins · ' + b.done + ' tasks done';
    $('chooseCloud').onclick = function () { busy = false; adopt(cloud.save, cloud.updatedAt); };
    $('chooseLocal').onclick = function () { busy = false; keepLocal().then(function () { render(); toast('This device\'s progress is now saved to your account!'); grantBonus(cloud); }); };
  }

  function onSignedIn() {
    var m = readMeta();
    return docRef().get().then(function (snap) {
      var cloud = snap.exists ? snap.data() : null;
      var local = parse(localRaw());
      if (m.justLoaded && m.uid === user.uid) { delete m.justLoaded; writeMeta(m); lastPushed = fingerprint(localRaw()); toast('Welcome back! Your saved progress is loaded.'); setTimeout(function () { grantBonus(cloud); }, 1800); return; }
      if (!cloud || !cloud.save) { return keepLocal().then(function () { toast('Signed in! Your progress is now saved online.'); setTimeout(function () { grantBonus(cloud); }, 1800); }); }
      if (m.uid === user.uid) {
        // This device is already linked to the account.
        var cloudNewer = (cloud.updatedAt || 0) > (m.syncedAt || 0);
        if (!cloudNewer) { lastPushed = fingerprint(cloud.save); grantBonus(cloud); return push(false); }
        if (!m.dirty) return adopt(cloud.save, cloud.updatedAt); // played on another device: pick that up
        return askChoice(cloud);
      }
      // First time this account is used on this device.
      if (fingerprint(cloud.save) === fingerprint(localRaw())) { m.uid = user.uid; m.syncedAt = cloud.updatedAt; writeMeta(m); lastPushed = fingerprint(cloud.save); grantBonus(cloud); return; }
      if (isFresh(local)) return adopt(cloud.save, cloud.updatedAt);
      return askChoice(cloud);
    }).catch(function (e) {
      console.warn('CozyNook cloud load failed', e && e.code);
      setMsg('Signed in, but your online save couldn\'t load. Check your internet and refresh.');
    });
  }

  /* ---------- Actions ---------- */
  function emailPass() { return [($('acctEmailInput').value || '').trim(), $('acctPassInput').value || '']; }
  function guard(p) {
    setMsg(''); var btns = document.querySelectorAll('#accountModal button'); btns.forEach(function (b) { b.disabled = true; });
    return p.catch(function (e) { setMsg(friendly(e)); }).then(function () { btns.forEach(function (b) { b.disabled = false; }); });
  }
  function wire() {
    $('accountBtn').addEventListener('click', open);
    $('acctClose').addEventListener('click', close);
    $('accountModal').addEventListener('click', function (e) { if (e.target.id === 'accountModal' && !busy) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !$('accountModal').hidden && !busy) close(); });
    $('acctGoogle').addEventListener('click', function () {
      if (!auth) return;
      guard(auth.signInWithPopup(new firebase.auth.GoogleAuthProvider()));
    });
    $('acctSignIn').addEventListener('click', function () {
      var ep = emailPass(); if (!auth) return;
      guard(auth.signInWithEmailAndPassword(ep[0], ep[1]));
    });
    $('acctSignUp').addEventListener('click', function () {
      var ep = emailPass(); if (!auth) return;
      guard(auth.createUserWithEmailAndPassword(ep[0], ep[1]));
    });
    $('acctForgot').addEventListener('click', function () {
      var em = emailPass()[0]; if (!auth) return;
      if (!em) { setMsg('Type your email above first, then press "Forgot password?" again.'); return; }
      guard(auth.sendPasswordResetEmail(em).then(function () { setMsg('Check your email for a link to reset your password.', true); }));
    });
    $('acctSignOut').addEventListener('click', function () {
      if (!auth) return;
      guard(push(false).then(function () { return auth.signOut(); }).then(function () {
        // Leave a fresh room for whoever uses this device next; the progress is safe in the account.
        if (window.CozyApp) CozyApp.lock = true;
        try { localStorage.removeItem(SAVE_KEY); localStorage.removeItem(META_KEY); } catch (e) {}
        location.reload();
      }));
    });
    $('acctPassInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') $('acctSignIn').click(); });
    window.addEventListener('cozy:saved', schedulePush);
    document.addEventListener('visibilitychange', function () { if (document.hidden) flush(); });
    window.addEventListener('pagehide', flush);
  }

  /* ---------- Boot ---------- */
  function loadScript(src) {
    return new Promise(function (res, rej) { var s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = function () { rej(new Error('load ' + src)); }; document.head.appendChild(s); });
  }
  function start() {
    wire(); setButton();
    SDK.reduce(function (p, src) { return p.then(function () { return loadScript(src); }); }, Promise.resolve())
      .then(function () {
        firebase.initializeApp(FIREBASE_CONFIG);
        auth = firebase.auth(); db = firebase.firestore();
        // Local testing only: talk to the Firebase emulators instead of the real project.
        if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname) && /[?&]emu=1/.test(location.search)) { auth.useEmulator('http://127.0.0.1:9099', { disableWarnings: true }); db.useEmulator('127.0.0.1', 8080); }
        auth.onAuthStateChanged(function (u) {
          var was = user; user = u; ready = true;
          if (u && (!was || was.uid !== u.uid)) {
            onSignedIn().then(function () { if (!busy && !$('accountModal').hidden) { render(); setTimeout(close, 900); } });
          }
          if (!busy) render();
        });
      })
      .catch(function (e) { console.warn('CozyNook: online saving unavailable', e && e.message); failed = true; ready = true; render(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.CozyCloud = { open: open, isSignedIn: function () { return !!user; }, user: function () { return user; } };
})();
