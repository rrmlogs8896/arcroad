/* Blur a photo on this device before you send it. Nothing is uploaded: the photo is drawn on a canvas in
   your browser, you drag boxes over faces and number plates, and you save or share the blurred copy. */
(function () {
  "use strict";
  var box = document.getElementById("blur");
  if (!box) return;
  var file = box.querySelector("#bl-file"), cv = box.querySelector("#bl-cv"), ctx = cv.getContext("2d");
  var undoB = box.querySelector("#bl-undo"), saveB = box.querySelector("#bl-save"), tip = box.querySelector("#bl-tip");
  var img = null, rects = [], drag = null, scale = 1;
  function draw() {
    if (!img) return;
    ctx.drawImage(img, 0, 0, cv.width, cv.height);
    rects.concat(drag ? [drag] : []).forEach(function (r) {
      var x = Math.min(r.x, r.x2), y = Math.min(r.y, r.y2), w = Math.abs(r.x2 - r.x), h = Math.abs(r.y2 - r.y);
      if (w < 4 || h < 4) return;
      var px = Math.max(8, Math.round(Math.max(w, h) / 10));
      var tmp = document.createElement("canvas"); tmp.width = Math.max(1, Math.ceil(w / px)); tmp.height = Math.max(1, Math.ceil(h / px));
      tmp.getContext("2d").drawImage(cv, x, y, w, h, 0, 0, tmp.width, tmp.height);
      ctx.imageSmoothingEnabled = false; ctx.drawImage(tmp, 0, 0, tmp.width, tmp.height, x, y, w, h); ctx.imageSmoothingEnabled = true;
      if (r === drag) { ctx.strokeStyle = "#E8A87C"; ctx.lineWidth = 2 / scale; ctx.strokeRect(x, y, w, h); }
    });
    undoB.disabled = !rects.length; saveB.disabled = false;
  }
  function pos(e) {
    var b = cv.getBoundingClientRect(), t = e.touches ? e.touches[0] : e;
    return { x: (t.clientX - b.left) * cv.width / b.width, y: (t.clientY - b.top) * cv.height / b.height };
  }
  function start(e) { if (!img) return; e.preventDefault(); var p = pos(e); drag = { x: p.x, y: p.y, x2: p.x, y2: p.y }; }
  function move(e) { if (!drag) return; e.preventDefault(); var p = pos(e); drag.x2 = p.x; drag.y2 = p.y; draw(); }
  function end() { if (!drag) return; if (Math.abs(drag.x2 - drag.x) > 6 && Math.abs(drag.y2 - drag.y) > 6) rects.push(drag); drag = null; draw(); }
  cv.addEventListener("mousedown", start); window.addEventListener("mousemove", move); window.addEventListener("mouseup", end);
  cv.addEventListener("touchstart", start, { passive: false }); cv.addEventListener("touchmove", move, { passive: false }); cv.addEventListener("touchend", end);
  file.addEventListener("change", function () {
    var f = file.files && file.files[0]; if (!f) return;
    var url = URL.createObjectURL(f), im = new Image();
    im.onload = function () {
      var max = 1600, k = Math.min(1, max / Math.max(im.naturalWidth, im.naturalHeight));
      cv.width = Math.round(im.naturalWidth * k); cv.height = Math.round(im.naturalHeight * k);
      scale = cv.getBoundingClientRect().width / cv.width || 1;
      img = im; rects = []; cv.hidden = false; cv.style.display = "block"; tip.textContent = "Drag a box over each face and number plate. Location data in the photo is removed when you save.";
      draw(); URL.revokeObjectURL(url);
    };
    im.onerror = function () { tip.textContent = "This photo type could not be opened here. Try a JPEG or a screenshot of it."; };
    im.src = url;
  });
  undoB.addEventListener("click", function () { rects.pop(); draw(); });
  saveB.addEventListener("click", function () {
    cv.toBlob(function (b) {
      if (!b) return;
      var f = new File([b], "arcroad-report-blurred.jpg", { type: "image/jpeg" });
      if (navigator.canShare && navigator.canShare({ files: [f] })) { navigator.share({ files: [f], title: "arcroad report photo" }).catch(function () {}); return; }
      var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = f.name; document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    }, "image/jpeg", 0.9);
  });
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-5e832c4a382b");
