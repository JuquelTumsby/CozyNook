/* CozyNook "Study Vibes": calm lo-fi beats made live in the browser with the Web Audio API.
   Nothing is downloaded, so there are no music files or copyright issues. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var LS = 'cozynook-music';

  // MIDI note helpers
  var N = function (name) {
    var m = /^([A-G])(#|b)?(\d)$/.exec(name), base = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[m[1]];
    return base + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0) + (+m[3] + 1) * 12;
  };
  var hz = function (midi) { return 440 * Math.pow(2, (midi - 69) / 12); };
  var chord = function (s) { return s.split(' ').map(N); };

  // Each track: tempo, swing, chords (one per bar), melody scale, drum feel, tone colour.
  var TRACKS = [
    { name: 'Rainy Window', bpm: 72, swing: 0.18, rain: true, cutoff: 1800,
      chords: ['F3 A3 C4 E4', 'E3 G3 B3 D4', 'D3 F3 A3 C4', 'C3 E3 G3 B3'], scale: 'A4 C5 D5 E5 G5', drums: 'soft' },
    { name: 'Midnight Cocoa', bpm: 78, swing: 0.22, cutoff: 1500,
      chords: ['D3 F3 A3 C4', 'G3 B3 D4 F4', 'C3 E3 G3 B3', 'A2 C3 E3 G3'], scale: 'D5 E5 G5 A5 C6', drums: 'lazy' },
    { name: 'Sunny Library', bpm: 86, swing: 0.12, cutoff: 2600,
      chords: ['C3 E3 G3 B3', 'A2 C3 E3 G3', 'F3 A3 C4 E4', 'G3 B3 D4 F4'], scale: 'E5 G5 A5 C6 D6', drums: 'bouncy' },
    { name: 'Cat Nap', bpm: 64, swing: 0.2, cutoff: 1300, sparse: true,
      chords: ['Eb3 G3 Bb3 D4', 'Ab3 C4 Eb4 G4', 'F3 Ab3 C4 Eb4', 'Bb2 D3 F3 Ab3'], scale: 'G4 Bb4 C5 Eb5 F5', drums: 'soft' },
    { name: 'Starlight Study', bpm: 80, swing: 0.16, cutoff: 2100,
      chords: ['A2 C3 E3 G3', 'F3 A3 C4 E4', 'C3 E3 G3 B3', 'G3 B3 D4 F#4'], scale: 'E5 G5 A5 B5 D6', drums: 'lazy' }
  ];

  var ctx = null, master = null, lofi = null, noiseBuf = null, crackle = null, rainNode = null;
  var playing = false, trackIdx = 0, step = 0, nextTime = 0, timer = null, volume = 0.6;
  try { var saved = JSON.parse(localStorage.getItem(LS) || '{}'); if (typeof saved.v === 'number') volume = saved.v; if (typeof saved.t === 'number') trackIdx = saved.t % TRACKS.length; } catch (e) {}
  function remember() { try { localStorage.setItem(LS, JSON.stringify({ v: volume, t: trackIdx })); } catch (e) {} }

  function setup() {
    if (ctx) return;
    var AC = window.AudioContext || window.webkitAudioContext;
    ctx = new AC();
    master = ctx.createGain(); master.gain.value = volume * 1.4;
    var comp = ctx.createDynamicsCompressor(); comp.threshold.value = -18; comp.ratio.value = 3;
    lofi = ctx.createBiquadFilter(); lofi.type = 'lowpass'; lofi.frequency.value = 2000; lofi.Q.value = 0.4;
    lofi.connect(comp); comp.connect(master); master.connect(ctx.destination);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    var d = noiseBuf.getChannelData(0); for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    // vinyl crackle: quiet hiss with tiny pops
    var cb = ctx.createBuffer(1, ctx.sampleRate * 3, ctx.sampleRate), cd = cb.getChannelData(0);
    for (var j = 0; j < cd.length; j++) cd[j] = (Math.random() * 2 - 1) * 0.012 + (Math.random() < 0.0004 ? (Math.random() * 2 - 1) * 0.5 : 0);
    crackle = ctx.createBufferSource(); crackle.buffer = cb; crackle.loop = true;
    var cg = ctx.createGain(); cg.gain.value = 0.5; crackle.connect(cg); cg.connect(master); crackle.start();
  }

  function env(g, t, a, peak, dec) { g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + dec); }
  function keys(midi, t, dur, vol) {   // soft electric-piano-ish tone
    var o1 = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain();
    o1.type = 'triangle'; o2.type = 'sine'; o1.frequency.value = hz(midi); o2.frequency.value = hz(midi) * 2.0;
    o1.detune.value = (Math.random() - 0.5) * 8;
    var g2 = ctx.createGain(); g2.gain.value = 0.25;
    o1.connect(g); o2.connect(g2); g2.connect(g); g.connect(lofi);
    env(g, t, 0.02, vol, dur);
    o1.start(t); o2.start(t); o1.stop(t + dur + 0.1); o2.stop(t + dur + 0.1);
  }
  function bass(midi, t, dur) {
    var o = ctx.createOscillator(), g = ctx.createGain(); o.type = 'sine'; o.frequency.value = hz(midi - 12);
    o.connect(g); g.connect(lofi); env(g, t, 0.01, 0.32, dur); o.start(t); o.stop(t + dur + 0.05);
  }
  function kick(t, v) {
    var o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(42, t + 0.18);
    o.connect(g); g.connect(lofi); env(g, t, 0.003, 0.55 * v, 0.22); o.start(t); o.stop(t + 0.3);
  }
  function noiseHit(t, type, freq, vol, dur) {
    var s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noiseBuf; f.type = type; f.frequency.value = freq; s.connect(f); f.connect(g); g.connect(lofi);
    env(g, t, 0.002, vol, dur); s.start(t, Math.random() * 1.5); s.stop(t + dur + 0.05);
  }
  function startRain(on) {
    if (rainNode) { try { rainNode.stop(); } catch (e) {} rainNode = null; }
    if (!on) return;
    var s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noiseBuf; s.loop = true; f.type = 'bandpass'; f.frequency.value = 1400; f.Q.value = 0.6; g.gain.value = 0.05;
    s.connect(f); f.connect(g); g.connect(master); s.start(); rainNode = s;
  }

  // 16 steps per bar (16th notes)
  function scheduleStep(tr, s, t) {
    var bar = Math.floor(s / 16), pos = s % 16, ch = chord(tr.chords[bar % tr.chords.length]), beat = 60 / tr.bpm;
    if (pos === 0) {
      ch.forEach(function (n, i) { keys(n, t + i * 0.025, beat * 3.6, tr.sparse ? 0.07 : 0.085); });
      bass(ch[0], t, beat * 1.8);
    }
    if (pos === 8) { bass(ch[0], t, beat * 1.2); if (!tr.sparse) ch.slice(1).forEach(function (n, i) { keys(n, t + i * 0.02, beat * 1.5, 0.045); }); }
    var feel = tr.drums;
    if (pos === 0 || (pos === 10 && feel !== 'soft') || (pos === 7 && feel === 'bouncy')) kick(t, feel === 'soft' ? 0.7 : 1);
    if (pos === 4 || pos === 12) noiseHit(t, 'bandpass', 1800, feel === 'soft' ? 0.12 : 0.18, 0.16);
    if (pos % 2 === 0 && !(tr.sparse && pos % 4)) noiseHit(t, 'highpass', 7000, pos % 4 ? 0.025 : 0.04, 0.04);
    if ((pos === 2 || pos === 6 || pos === 10 || pos === 14) && Math.random() < (tr.sparse ? 0.22 : 0.35)) {
      var sc = tr.scale.split(' ').map(N); keys(sc[Math.floor(Math.random() * sc.length)], t, beat * 1.4, 0.06);
    }
  }
  function scheduler() {
    var tr = TRACKS[trackIdx], sixteenth = 60 / tr.bpm / 4;
    while (nextTime < ctx.currentTime + 0.15) {
      var swingDelay = (step % 2) ? sixteenth * tr.swing : 0;
      scheduleStep(tr, step, nextTime + swingDelay);
      nextTime += sixteenth; step++;
    }
  }

  function play() {
    setup();
    if (ctx.state === 'suspended') ctx.resume();
    var tr = TRACKS[trackIdx];
    lofi.frequency.setTargetAtTime(tr.cutoff, ctx.currentTime, 0.3);
    startRain(!!tr.rain);
    master.gain.setTargetAtTime(volume * 1.4, ctx.currentTime, 0.2);
    step = 0; nextTime = ctx.currentTime + 0.08;
    clearInterval(timer); timer = setInterval(scheduler, 25); scheduler();
    playing = true; paint();
  }
  function pause() {
    playing = false; clearInterval(timer);
    if (ctx) { master.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.08); startRain(false); setTimeout(function () { if (!playing && ctx) ctx.suspend(); }, 400); }
    paint();
  }
  function skip(dir) {
    trackIdx = (trackIdx + (dir || 1) + TRACKS.length) % TRACKS.length; remember();
    if (playing) play(); else paint();
  }
  function setVolume(v) { volume = v; remember(); if (ctx && playing) master.gain.setTargetAtTime(v * 1.4, ctx.currentTime, 0.05); }

  function paint() {
    var box = $('musicPlayer'); if (!box) return;
    box.classList.toggle('is-playing', playing);
    $('musicTitle').textContent = TRACKS[trackIdx].name;
    $('musicNum').textContent = (trackIdx + 1) + ' / ' + TRACKS.length;
    var pb = $('musicPlay'); pb.textContent = playing ? '❚❚' : '▶'; pb.setAttribute('aria-label', playing ? 'Pause music' : 'Play music');
    var fp = $('focusMusicBtn'); if (fp) fp.textContent = playing ? 'Pause study music' : 'Play study music';
  }

  function start() {
    var box = $('musicPlayer'); if (!box) return;
    $('musicToggle').addEventListener('click', function () { box.classList.toggle('open'); });
    $('musicPlay').addEventListener('click', function () { playing ? pause() : play(); });
    $('musicNext').addEventListener('click', function () { skip(1); });
    $('musicPrev').addEventListener('click', function () { skip(-1); });
    var vol = $('musicVol'); vol.value = Math.round(volume * 100);
    vol.addEventListener('input', function () { setVolume(vol.value / 100); });
    var fp = $('focusMusicBtn'); if (fp) fp.addEventListener('click', function () { box.classList.add('open'); playing ? pause() : play(); });
    paint();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  window.CozyMusic = { play: play, pause: pause, skip: skip, isPlaying: function () { return playing; }, track: function () { return TRACKS[trackIdx].name; } };
})();
