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
      var px = Math.max(12, Math.round(Math.max(w, h) / 6));
      var tmp = document.createElement("canvas"); tmp.width = Math.max(1, Math.ceil(w / px)); tmp.height = Math.max(1, Math.ceil(h / px));
      tmp.getContext("2d").drawImage(cv, x, y, w, h, 0, 0, tmp.width, tmp.height);
      ctx.imageSmoothingEnabled = false; ctx.drawImage(tmp, 0, 0, tmp.width, tmp.height, x, y, w, h); ctx.imageSmoothingEnabled = true;
      if (r === drag) { ctx.strokeStyle = "#E8A87C"; ctx.lineWidth = 2 / scale; ctx.strokeRect(x, y, w, h); }
    });
    undoB.disabled = !rects.length; saveB.disabled = !rects.length;
    if (out) { out.hidden = true; }
  }
  function pos(e) {
    var b = cv.getBoundingClientRect();
    return { x: Math.max(0, Math.min(cv.width, (e.clientX - b.left) * cv.width / b.width)), y: Math.max(0, Math.min(cv.height, (e.clientY - b.top) * cv.height / b.height)) };
  }
  // Pointer events cover finger, pen and mouse alike; the canvas keeps the pointer until it lifts.
  var downAt = null;
  function start(e) {
    if (!img || (e.pointerType === "mouse" && e.button !== 0)) return;
    e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch (x) {}
    var p = pos(e); downAt = p; drag = { x: p.x, y: p.y, x2: p.x, y2: p.y };
  }
  function move(e) { if (!drag) return; e.preventDefault(); var p = pos(e); drag.x2 = p.x; drag.y2 = p.y; draw(); }
  function end(e) {
    if (!drag) return;
    var w = Math.abs(drag.x2 - drag.x), h = Math.abs(drag.y2 - drag.y);
    if (w > 12 && h > 12) rects.push(drag);
    else if (downAt) {
      // A tap blurs a square around the spot: quick for a face or a plate.
      var side = Math.round(Math.min(cv.width, cv.height) * 0.14), c = downAt;
      rects.push({ x: Math.max(0, c.x - side / 2), y: Math.max(0, c.y - side / 2), x2: Math.min(cv.width, c.x + side / 2), y2: Math.min(cv.height, c.y + side / 2) });
    }
    drag = null; downAt = null; draw();
    if (e && e.pointerId != null) { try { cv.releasePointerCapture(e.pointerId); } catch (x) {} }
  }
  cv.style.touchAction = "none";
  cv.addEventListener("pointerdown", start); cv.addEventListener("pointermove", move);
  cv.addEventListener("pointerup", end); cv.addEventListener("pointercancel", function () { drag = null; downAt = null; draw(); });
  file.addEventListener("change", function () {
    var f = file.files && file.files[0]; if (!f) return;
    var url = URL.createObjectURL(f), im = new Image();
    im.onload = function () {
      var max = 1600, k = Math.min(1, max / Math.max(im.naturalWidth, im.naturalHeight));
      cv.width = Math.round(im.naturalWidth * k); cv.height = Math.round(im.naturalHeight * k);
      scale = cv.getBoundingClientRect().width / cv.width || 1;
      img = im; rects = []; cv.hidden = false; cv.style.display = "block"; tip.textContent = "Tap each face and number plate, or drag a box over it. Location data in the photo is removed when you save.";
      draw(); URL.revokeObjectURL(url);
    };
    im.onerror = function () { tip.textContent = "This photo type could not be opened here. Try a JPEG or a screenshot of it."; };
    im.src = url;
  });
  undoB.addEventListener("click", function () { rects.pop(); draw(); });
  var out = null;
  function blobNow() {
    var u = cv.toDataURL("image/jpeg", 0.9), bin = atob(u.split(",")[1]), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return { url: u, blob: new Blob([a], { type: "image/jpeg" }) };
  }
  function showCopy(u) {
    if (!out) {
      out = document.createElement("figure"); out.style.margin = "10px 0 0";
      out.innerHTML = '<img alt="Your blurred copy" style="max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line);-webkit-touch-callout:default"><figcaption class="note" style="margin-top:6px">This is the blurred copy. On a phone, press and hold it, then choose Save to Photos.</figcaption>';
      saveB.parentNode.parentNode.appendChild(out);
    }
    out.querySelector("img").src = u; out.hidden = false;
  }
  saveB.addEventListener("click", function () {
    if (!rects.length) { tip.textContent = "Tap each face and number plate first, or drag a box over it."; return; }
    var r = blobNow(), f = new File([r.blob], "arcroad-report-blurred.jpg", { type: "image/jpeg" });
    showCopy(r.url);
    if (navigator.canShare && navigator.canShare({ files: [f] })) {
      navigator.share({ files: [f], title: "arcroad report photo" }).catch(function () {});
      return;
    }
    var a = document.createElement("a"); a.href = URL.createObjectURL(r.blob); a.download = f.name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  });
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-5e832c4a382b");
