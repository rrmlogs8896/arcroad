/* Volunteer sign-up and feedback, sent from the visitor's own email app to hello@arcroad.org.
   The page itself sends and stores nothing. A reference is made on this device so both sides can refer to it. */
(function () {
  "use strict";
  function ref(k) { return "AR-" + k + "-" + (function(){var d=new Date(),p=function(n){return (n<10?'0':'')+n};return String(d.getFullYear()).slice(2)+p(d.getMonth()+1)+p(d.getDate())})() + "-" + Math.random().toString(36).slice(2, 6).toUpperCase(); }
  var GUESS = [["correction", ["wrong", "error", "mistake", "incorrect", "correct", "outdated", "not true"]], ["idea", ["idea", "suggest", "could you", "should", "feature", "add", "wish"]], ["partnership", ["partner", "pilot", "collaborat", "work with", "government", "police", "ngo", "company"]], ["press", ["journalist", "article", "interview", "media", "press", "story"]], ["praise", ["great", "love", "thank", "amazing", "nice", "good work", "well done"]], ["question", ["?", "how", "why", "what", "when", "can i"]]];
  Array.prototype.forEach.call(document.querySelectorAll("form[data-intake]"), function (f) {
    var kind = f.getAttribute("data-intake"), msg = f.querySelector(".in-msg"), r = ref(kind === "volunteer" ? "V" : "F");
    var text = f.querySelector("textarea"), sel = f.querySelector("select[name=type]");
    if (text && sel) text.addEventListener("input", function () {
      if (sel.dataset.touched) return; var q = text.value.toLowerCase();
      for (var i = 0; i < GUESS.length; i++) { if (GUESS[i][1].some(function (w) { return q.indexOf(w) > -1; })) { sel.value = GUESS[i][0]; break; } }
    });
    if (sel) sel.addEventListener("change", function () { sel.dataset.touched = "1"; });
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var lines = [(kind === "volunteer" ? "Volunteer sign-up" : "Feedback") + " · reference " + r, ""];
      Array.prototype.forEach.call(f.elements, function (el) {
        if (!el.name || el.type === "submit") return;
        if (el.type === "checkbox") { if (el.checked) lines.push("- " + el.value); return; }
        if (el.value.trim()) lines.push((el.getAttribute("data-label") || el.name) + ": " + el.value.trim());
      });
      lines.push("", "Sent from arcroad.org. You can ask us to delete this at any time by replying to this email.");
      var subj = "[arcroad " + kind + "] " + r + (sel ? " · " + sel.value : "");
      if (msg) msg.textContent = "Your mail app should open with this ready to send. Your reference is " + r + ".";
      location.href = "mailto:hello@arcroad.org?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(lines.join("\n"));
    });
  });
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-5ae0b4f8de32");
