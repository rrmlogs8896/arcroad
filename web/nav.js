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

// Evidence behind a claim (27 Nov 2026): a small "+" next to a claim opens the proof we hold for it,
// a blurred photo from our drives, the driven GPS figures, or the source, so readers can check us.
(function(){
  var d=document, P='/field/photos/', R='/roads/photos/';
  var EV={
    s18:{t:'S18: 13 m across, 1.58 km around',img:P+'s18-under-the-metro',w:1280,h:690,cap:'Taken on our drive here in November 2026, within 150 m of the place: the road under the metro. Faces, plates and phone numbers blurred.',facts:[['Straight across','13 m (OpenStreetMap)'],['Driven, west to east','1.58 km (model 1.57 km)'],['Driven, east to west','1.55 km (model 1.38 km)'],['How measured','Phone GPS once a second, about plus or minus 50 m']],more:['/field/','Every pass we drove']},
    s16:{t:'S16: 19 m across, 2.3 km around',facts:[['Straight across','19 m (OpenStreetMap)'],['Driven','2.30 km (model 2.38 km)'],['Result','Matched the model within the pre-set tolerance']],more:['/field/','See the pass in the results table']},
    s12:{t:'A median closed with blocks',img:P+'s12-median-closed-with-blocks',w:1280,h:700,cap:'S12, November 2026: concrete blocks carry the median on past the place, with no gap to cross.',more:['/field/#photos','All photos from the drives']},
    s13:{t:'One U-turn opening for everyone',img:P+'s13-u-turn-opening',w:1280,h:735,cap:'S13, November 2026: the U-turn about 450 m from the place. Cars, autos, two-wheelers and trucks share one opening.',more:['/field/#photos','All photos from the drives']},
    s11:{t:'The signed U-turn the detour uses',img:P+'s11-u-turn-sign',w:1280,h:700,cap:'S11, November 2026: the U-turn a short way past the place, which one direction has to use.',more:['/field/#photos','All photos from the drives']},
    cross:{t:'Crossing where there is no crossing',img:R+'people-crossing-highway',w:1280,h:600,cap:'NH-65 at night, November 2026: people walk across the highway through a gap beside the barricades. We show what the road invites, never who is to blame.',more:['/roads/#walk','Pedestrians pushed out']}
  };
  var box=null, last=null;
  function close(){ if(box){box.remove();box=null;} if(last){last.setAttribute('aria-expanded','false');last.focus();last=null;} }
  function open(btn){
    var e=EV[btn.getAttribute('data-ev')]; if(!e) return;
    close(); last=btn; btn.setAttribute('aria-expanded','true');
    box=d.createElement('div'); box.className='evp'; box.setAttribute('role','dialog'); box.setAttribute('aria-label','Evidence: '+e.t);
    var x=d.createElement('button'); x.type='button'; x.className='evx'; x.setAttribute('aria-label','Close'); x.textContent='×'; x.onclick=close; box.appendChild(x);
    var k=d.createElement('p'); k.className='evk'; k.textContent='The evidence'; box.appendChild(k);
    var h=d.createElement('h3'); h.textContent=e.t; box.appendChild(h);
    if(e.img){ var a=d.createElement('a'); a.href=e.img+'.jpg'; var im=d.createElement('img'); im.src=e.img+'-640.jpg'; im.srcset=e.img+'-640.jpg 640w, '+e.img+'.jpg 1280w'; im.sizes='(max-width:600px) 92vw, 420px'; im.width=e.w; im.height=e.h; im.alt=e.cap; a.appendChild(im); box.appendChild(a);
      var c=d.createElement('p'); c.className='evc'; c.textContent=e.cap; box.appendChild(c); }
    if(e.facts){ var dl=d.createElement('dl'); e.facts.forEach(function(f){var t=d.createElement('dt');t.textContent=f[0];var v=d.createElement('dd');v.textContent=f[1];dl.appendChild(t);dl.appendChild(v);}); box.appendChild(dl); }
    if(e.more){ var m=d.createElement('a'); m.className='evm'; m.href=e.more[0]; m.textContent=e.more[1]+' →'; box.appendChild(m); }
    d.body.appendChild(box);
    var r=btn.getBoundingClientRect(), wide=innerWidth>640;
    if(wide){ var L=Math.min(innerWidth-box.offsetWidth-16, Math.max(16, r.left+scrollX-20)); box.style.left=L+'px'; var T=r.bottom+scrollY+8; if(r.bottom+box.offsetHeight+16>innerHeight) T=Math.max(scrollY+16, r.top+scrollY-box.offsetHeight-8); box.style.top=T+'px'; }
    else box.classList.add('sheet');
    x.focus();
  }
  d.addEventListener('click',function(ev){ var b=ev.target.closest&&ev.target.closest('.evb'); if(b){ev.preventDefault(); if(last===b) close(); else open(b); return;} if(box&&!box.contains(ev.target)) close(); });
  d.addEventListener('keydown',function(ev){ if(ev.key==='Escape') close(); });
})();

// Moving pictures stay still for readers who ask for reduced motion.
(function(){try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)[].forEach.call(document.querySelectorAll('video[data-journey]'),function(v){v.removeAttribute('autoplay');v.pause();});}catch(e){}})();

// Fold (28 Nov 2026): long runs of reading text keep their opening lines and tuck the rest under the site's
// own "+" (the same details.more used across the pages). Text stays in the page for find, links and print.
(function(){
  if(/\/(privacy|terms)(\/|$|\.html)/.test(location.pathname)) return;
  var SKIP='nav,header,footer,form,details,figure,table,aside,[data-join],[data-nofold],.ar-share,.jn,.sn,#clock,.ev-banner';
  var PROSE={P:1,UL:1,OL:1,BLOCKQUOTE:1}, MIN=70, n=0;
  function words(el){return (el.textContent||'').trim().split(/\s+/).filter(Boolean).length;}
  function ok(el){return PROSE[el.tagName]&&!el.closest(SKIP)&&!/\u00a9|contributors|licen[cs]e/i.test(el.textContent)&&!el.querySelector('input,button,select,textarea,canvas,video,iframe');}
  function fold(run){
    var keep=(words(run[0])<14&&run.length>2)?2:1, rest=run.slice(keep), w=0;
    rest.forEach(function(e){w+=words(e);}); if(w<40) return;
    var d=document.createElement('details'), s=document.createElement('summary');
    d.className='more fd'; d.id='fd-'+(++n); s.textContent='More';
    rest[0].parentNode.insertBefore(d,rest[0]); d.appendChild(s); rest.forEach(function(e){d.appendChild(e);});
    d.addEventListener('toggle',function(){ s.textContent=d.open?'Less':'More'; });
  }
  function scan(root){
    var seen=[];
    [].forEach.call(root.querySelectorAll('p,ul,ol,blockquote'),function(el){
      var par=el.parentNode; if(seen.indexOf(par)>-1||!ok(el)) return; seen.push(par);
      var run=[],kids=[].slice.call(par.children);
      for(var i=0;i<=kids.length;i++){
        var k=kids[i]; if(k&&ok(k)){run.push(k);continue;}
        if(run.length>=2){var w=0;run.forEach(function(e){w+=words(e);}); if(w>=MIN) fold(run);}
        run=[];
      }
    });
  }
  function openTo(){ var h=location.hash.slice(1),t; if(!h) return; try{t=document.getElementById(decodeURIComponent(h));}catch(e){} if(!t) return;
    for(var x=t;x;x=x.parentElement) if(x.tagName==='DETAILS') x.open=true; t.scrollIntoView(); }
  function lists(root){
    [].forEach.call(root.querySelectorAll('ul,ol'),function(l){
      if(!ok(l)||l.closest('details')) return;
      var li=[].filter.call(l.children,function(c){return c.tagName==='LI';});
      if(li.length<4||words(l)<90) return;
      var rest=li.slice(2), d=document.createElement('details'), s=document.createElement('summary'), l2=document.createElement(l.tagName);
      d.className='more fd'; d.id='fd-'+(++n); s.textContent='More'; l2.className=l.className;
      if(l.tagName==='OL') l2.setAttribute('start',String((+l.getAttribute('start')||1)+2));
      rest.forEach(function(e){l2.appendChild(e);}); d.appendChild(s); d.appendChild(l2); l.parentNode.insertBefore(d,l.nextSibling);
      d.addEventListener('toggle',function(){ s.textContent=d.open?'Less':'More'; });
    });
  }
  function longs(root){
    [].forEach.call(root.querySelectorAll('p'),function(el){
      if(!ok(el)||el.closest('details')||/\b(lead|lede)\b/.test(el.className)||words(el)<70) return;
      var seen=0, cut=null, off=0;
      for(var i=0;i<el.childNodes.length&&!cut;i++){
        var c=el.childNodes[i];
        if(c.nodeType===3){
          var re=/[.!?]["'\u201d\u2019)]?\s+(?=[A-Z0-9"\u201c])/g, m, txt=c.textContent;
          while((m=re.exec(txt))){ var w=seen+txt.slice(0,m.index+1).trim().split(/\s+/).filter(Boolean).length; if(w>=18){cut=c;off=m.index+m[0].length;break;} }
          if(!cut) seen+=txt.trim().split(/\s+/).filter(Boolean).length;
        } else seen+=words(c);
      }
      if(!cut) return;
      var tail=cut.splitText(off), p2=document.createElement('p'), d=document.createElement('details'), sm=document.createElement('summary');
      p2.className=el.className;
      for(var n2=tail;n2;){var nx=n2.nextSibling;p2.appendChild(n2);n2=nx;}
      if(words(p2)<30){ while(p2.firstChild) el.appendChild(p2.firstChild); el.normalize(); return; }
      d.className='more fd'; d.id='fd-'+(++n); sm.textContent='More'; d.appendChild(sm); d.appendChild(p2);
      el.parentNode.insertBefore(d,el.nextSibling);
      d.addEventListener('toggle',function(){ sm.textContent=d.open?'Less':'More'; });
    });
  }
  function merge(root){
    [].forEach.call(root.querySelectorAll('details.fd'),function(d){
      var nx=d.nextElementSibling;
      while(nx&&nx.tagName==='DETAILS'&&nx.classList.contains('fd')){
        [].slice.call(nx.children).forEach(function(c){ if(c.tagName!=='SUMMARY') d.appendChild(c); });
        var gone=nx; nx=nx.nextElementSibling; gone.parentNode.removeChild(gone);
      }
    });
  }
  function go(){ try{ var r=document.querySelector('main')||document.body; scan(r); lists(r); longs(r); merge(r); openTo(); }catch(e){} }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',go); else go();
  addEventListener('hashchange',openTo);
})();
