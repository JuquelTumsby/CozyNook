/* CozyNook calendar planner: a month view where players add plans to any day.
   Plans live in the main save as state.plans = { 'YYYY-M-D': [ {id, text, time, color, done, rewarded} ] }
   so they sync with the account like everything else. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var app = function () { return window.CozyApp || {}; };
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var COLORS = [['pink', '#ff9cba'], ['mint', '#7fd6a8'], ['sky', '#7cc4f0'], ['sun', '#ffd36e'], ['lilac', '#b9a0f0']];
  var REWARD_COINS = 5, REWARD_XP = 10;
  var view = new Date(), selected = new Date(), color = 'pink';
  view.setDate(1);

  var key = function (d) { return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); };
  var same = function (a, b) { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); };
  function plans() { var p = app().getData ? app().getData('plans') : null; return p && typeof p === 'object' && !Array.isArray(p) ? p : {}; }
  function savePlans(p) { if (app().setData) app().setData('plans', p); }
  function colorHex(c) { var f = COLORS.filter(function (x) { return x[0] === c; })[0]; return f ? f[1] : COLORS[0][1]; }
  function fmtTime(t) { if (!t) return ''; var h = +t.split(':')[0], m = t.split(':')[1]; return (h % 12 || 12) + ':' + m + (h < 12 ? ' am' : ' pm'); }

  function renderGrid() {
    var grid = $('calGrid'); if (!grid) return;
    $('calTitle').textContent = MONTHS[view.getMonth()] + ' ' + view.getFullYear();
    grid.innerHTML = '';
    DAYS.forEach(function (d) { var h = document.createElement('div'); h.className = 'cal-dow'; h.textContent = d; grid.appendChild(h); });
    var first = new Date(view.getFullYear(), view.getMonth(), 1), days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
    for (var i = 0; i < first.getDay(); i++) { var e = document.createElement('div'); e.className = 'cal-empty'; grid.appendChild(e); }
    var all = plans(), today = new Date(); today.setHours(0, 0, 0, 0);
    for (var day = 1; day <= days; day++) {
      var d = new Date(view.getFullYear(), view.getMonth(), day), list = all[key(d)] || [];
      var b = document.createElement('button'); b.type = 'button'; b.className = 'cal-day';
      if (same(d, today)) b.classList.add('today');
      if (same(d, selected)) b.classList.add('selected');
      if (d < today) b.classList.add('past');
      if (list.length && list.every(function (p) { return p.done; })) b.classList.add('all-done');
      b.dataset.day = day;
      var dots = list.slice(0, 4).map(function (p) { return '<i style="background:' + colorHex(p.color) + '"></i>'; }).join('');
      b.innerHTML = '<span class="cal-num">' + day + '</span><span class="cal-dots">' + dots + (list.length > 4 ? '<em>+</em>' : '') + '</span>';
      b.setAttribute('aria-label', MONTHS[d.getMonth()] + ' ' + day + (list.length ? ', ' + list.length + ' plan' + (list.length === 1 ? '' : 's') : ', no plans'));
      grid.appendChild(b);
    }
  }

  function renderDay() {
    var box = $('calList'); if (!box) return;
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var label = same(selected, today) ? 'Today' : DAYS[selected.getDay()] + ', ' + MONTHS[selected.getMonth()] + ' ' + selected.getDate();
    $('calDayTitle').textContent = label;
    var list = (plans()[key(selected)] || []).slice().sort(function (a, b) { return (a.time || '99') < (b.time || '99') ? -1 : 1; });
    box.innerHTML = '';
    if (!list.length) { box.innerHTML = '<div class="empty">Nothing planned yet. Add something below! 🌷</div>'; return; }
    list.forEach(function (p) {
      var row = document.createElement('div'); row.className = 'cal-plan' + (p.done ? ' done' : '');
      row.style.borderLeftColor = colorHex(p.color);
      row.innerHTML = '<input type="checkbox"' + (p.done ? ' checked' : '') + ' aria-label="Done"><span class="cal-time"></span><span class="cal-text"></span><button type="button" class="tiny-btn" aria-label="Delete plan">×</button>';
      row.querySelector('.cal-time').textContent = fmtTime(p.time);
      row.querySelector('.cal-text').textContent = p.text;
      row.querySelector('input').addEventListener('change', function () { toggle(p.id); });
      row.querySelector('button').addEventListener('click', function () { remove(p.id); });
      box.appendChild(row);
    });
  }
  function renderColors() {
    var box = $('calColors'); box.innerHTML = '';
    COLORS.forEach(function (c) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'cal-color' + (c[0] === color ? ' on' : '');
      b.style.background = c[1]; b.setAttribute('aria-label', c[0] + ' colour'); b.setAttribute('aria-pressed', c[0] === color);
      b.addEventListener('click', function () { color = c[0]; renderColors(); });
      box.appendChild(b);
    });
  }
  function render() { renderGrid(); renderDay(); }

  function add() {
    var text = ($('calText').value || '').trim().slice(0, 60);
    if (!text) { $('calText').focus(); return; }
    var all = plans(), k = key(selected);
    all[k] = (all[k] || []).concat([{ id: Date.now(), text: text, time: $('calTime').value || '', color: color, done: false }]);
    savePlans(all); $('calText').value = ''; $('calTime').value = '';
    render();
    if (app().toast) app().toast('Added to ' + $('calDayTitle').textContent + ' 📅');
  }
  function toggle(id) {
    var all = plans(), list = all[key(selected)] || [], p = list.filter(function (x) { return x.id === id; })[0]; if (!p) return;
    p.done = !p.done;
    var paid = p.done && !p.rewarded; if (paid) p.rewarded = true;
    savePlans(all);
    if (paid && app().earn) app().earn(REWARD_COINS, REWARD_XP, 'Plan done! +' + REWARD_COINS + ' coins ✨');
    render();
  }
  function remove(id) {
    var all = plans(), k = key(selected);
    all[k] = (all[k] || []).filter(function (x) { return x.id !== id; });
    if (!all[k].length) delete all[k];
    savePlans(all); render();
  }

  function start() {
    if (!$('calGrid')) return;
    $('calPrev').addEventListener('click', function () { view.setMonth(view.getMonth() - 1); renderGrid(); });
    $('calNext').addEventListener('click', function () { view.setMonth(view.getMonth() + 1); renderGrid(); });
    $('calToday').addEventListener('click', function () { selected = new Date(); view = new Date(); view.setDate(1); render(); });
    $('calGrid').addEventListener('click', function (e) {
      var b = e.target.closest('.cal-day'); if (!b) return;
      selected = new Date(view.getFullYear(), view.getMonth(), +b.dataset.day); render();
      if (window.innerWidth < 760) $('calDayTitle').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    $('calAdd').addEventListener('click', add);
    $('calText').addEventListener('keydown', function (e) { if (e.key === 'Enter') add(); });
    renderColors(); render();
    // refresh when the save changes elsewhere (e.g. loaded from the account)
    window.addEventListener('cozy:saved', function () { if (!document.activeElement || !document.activeElement.closest('.cal-panel')) render(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.CozyCalendar = { leftToday: function () { return (plans()[key(new Date())] || []).filter(function (p) { return !p.done; }).length; } };
})();
