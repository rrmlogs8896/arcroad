/* arcroad share row: uses the device's own share sheet, or copies the link. Sends nothing to arcroad. No storage. ar-000000000000 */
(function () {
  document.querySelectorAll("[data-ar-share]").forEach(function (b) {
    if (b.dataset.ready) return;
    b.dataset.ready = "1";
    b.addEventListener("click", function () {
      var url = b.dataset.url, title = b.dataset.title, label = b.textContent;
      function say(t) { b.textContent = t; setTimeout(function () { b.textContent = label; }, 2200); }
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () { say("Link copied"); }, function () { say(url); });
      } else {
        say(url);
      }
    });
  });

  document.querySelectorAll("[data-ar-copy]").forEach(function (b) {
    if (b.dataset.ready) return; b.dataset.ready = "1";
    b.addEventListener("click", function () {
      var url = b.dataset.url, label = b.textContent;
      function say(t) { b.textContent = t; setTimeout(function () { b.textContent = label; }, 2000); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { say("Copied ✓"); }, function () { say(url); });
      else say(url);
    });
  });
})();
