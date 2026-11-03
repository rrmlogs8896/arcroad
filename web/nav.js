/* arcroad navigation: tap or click toggles a group; Escape or a click elsewhere closes it.
   Hover opening on desktop is pure CSS, so the menu works before this file loads. No storage, no network. */
(function () {
  'use strict';
  var nav = document.querySelector('.sn'); if (!nav) return;
  var groups = Array.prototype.slice.call(nav.querySelectorAll('.sn-g'));
  var small = window.matchMedia('(max-width:720px)');
  function set(g, open) {
    g.classList.toggle('open', open);
    if (open) g.classList.remove('shut');
    g.querySelector('button').setAttribute('aria-expanded', String(open));
  }
  function closeAll(except) { groups.forEach(function (g) { if (g !== except) set(g, false); }); }
  groups.forEach(function (g) {
    var b = g.querySelector('button');
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = !g.classList.contains('open');
      closeAll(g); set(g, open);
      if (!open) g.classList.add('shut');
      if (open && small.matches && g.scrollIntoView) g.scrollIntoView({ block: 'nearest', inline: 'start', behavior: 'smooth' });
    });
    g.addEventListener('mouseleave', function () { g.classList.remove('shut'); if (!small.matches) set(g, false); });
    g.addEventListener('focusout', function (e) { if (!g.contains(e.relatedTarget)) { g.classList.remove('shut'); set(g, false); } });
  });
  document.addEventListener('click', function (e) { if (!nav.contains(e.target)) closeAll(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    groups.forEach(function (g) {
      if (g.classList.contains('open') || g.contains(document.activeElement)) { set(g, false); g.classList.add('shut'); g.querySelector('button').focus(); }
    });
  });
  function edge() { nav.classList.toggle('fade', nav.scrollWidth - nav.clientWidth - nav.scrollLeft > 4); }
  nav.addEventListener('scroll', edge, { passive: true }); window.addEventListener('resize', edge); edge();
})();
