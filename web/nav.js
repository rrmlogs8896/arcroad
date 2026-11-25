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
    g.addEventListener('mouseenter', function () { if (small.matches) return; groups.forEach(function (o) { if (o !== g) { set(o, false); if (o.contains(document.activeElement)) document.activeElement.blur(); } }); });
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
;(function(){
  var d=document; if(d.documentElement.hasAttribute('data-ar-motion'))return; d.documentElement.setAttribute('data-ar-motion','');
  var R=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  var bar=d.createElement('div'); bar.className='ar-prog'; bar.setAttribute('aria-hidden','true'); d.body.appendChild(bar);
  var q=false; function prog(){q=false; var h=d.documentElement, m=h.scrollHeight-h.clientHeight; bar.style.transform='scaleX('+(m>40?Math.min(1,(window.scrollY||h.scrollTop)/m):0)+')';}
  window.addEventListener('scroll',function(){if(!q){q=true;requestAnimationFrame(prog);}},{passive:true}); window.addEventListener('resize',prog); prog();
  if(R||!('IntersectionObserver' in window))return;
  var H=window.innerHeight;
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('ar-in');io.unobserve(e.target);}});},{rootMargin:'0px 0px -6% 0px'});
  [].forEach.call(d.querySelectorAll('main h2, main .stats>div, main .wrap, main figure, main .qr-sum, main details.more, main .ar-share'),function(e){
    if(e.getBoundingClientRect().top>H*0.92){e.classList.add('ar-rv');io.observe(e);}
  });
  var co=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){co.unobserve(e.target);up(e.target);}});},{threshold:0.6});
  [].forEach.call(d.querySelectorAll('.stats b'),function(b){var t=b.textContent.trim(); if(/^\d{1,3}(,\d{3})*$|^\d+$/.test(t)&&+t.replace(/,/g,'')>=10)co.observe(b);});
  function up(b){var t=b.textContent.trim(), n=+t.replace(/,/g,''), s=0;
    b.style.minWidth=b.getBoundingClientRect().width+'px'; b.style.display='inline-block'; b.style.fontVariantNumeric='tabular-nums';
    function f(now){if(!s)s=now; var p=Math.min(1,(now-s)/900), k=1-Math.pow(1-p,3);
      b.textContent=p<1?Math.round(n*k).toLocaleString('en-IN'):t; if(p<1)requestAnimationFrame(f);}
    requestAnimationFrame(f);}
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-18d723157239");
