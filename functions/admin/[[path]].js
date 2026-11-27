// arcroad private admin (27 Nov 2026): volunteer ("citizen") sign-up breakdown for Rohit only.
// Sign-in: Cloudflare Access ("arcroad admin" app on arcroad.org/admin), a one-time code to Rohit's email,
// session 30 days. This function also checks the Access token itself (signature, audience, expiry, email),
// so the page stays locked even on a preview address that Access does not cover.
// Shows aggregates and recent sign-ups by area only: no sign-up codes, names, emails or IPs exist or are shown.
const HELP = ["Driving and timing a crossing near me", "Photographing a place (faces and plates blurred)", "Fixing roads on OpenStreetMap", "Telling my resident association or college", "Running arcroad for another city"];
const TIME = ["An hour or two, once", "A few hours a month", "More, regularly"];
const TASKS = { check: "Check a crossing", map: "Fix the map", report: "Report a change", tell: "Tell people", cost: "Work out a cost" };
const H = { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex, nofollow, noarchive", "referrer-policy": "no-referrer", "x-frame-options": "DENY" };
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const enc = new TextEncoder();

const TEAM = "https://blue-pond-74dc.cloudflareaccess.com";
const AUD = "cda342a799fc450906460bb63ea6a5fad4ec98d254302697570a0c82df71ce01";
const OWNER = "rohithmadasu@gmail.com";
const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
let CERTS = null, CERTS_AT = 0;
async function certs() {
  if (CERTS && Date.now() - CERTS_AT < 3600e3) return CERTS;
  const r = await fetch(TEAM + "/cdn-cgi/access/certs"); CERTS = (await r.json()).keys || []; CERTS_AT = Date.now(); return CERTS;
}
async function accessEmail(req) {
  const ck = (req.headers.get("cookie") || "").split(/;\s*/).find((c) => c.startsWith("CF_Authorization="));
  const jwt = req.headers.get("cf-access-jwt-assertion") || (ck ? ck.slice(17) : "");
  const parts = jwt.split("."); if (parts.length !== 3) return null;
  let head, body; try { head = JSON.parse(new TextDecoder().decode(b64u(parts[0]))); body = JSON.parse(new TextDecoder().decode(b64u(parts[1]))); } catch (e) { return null; }
  if (head.alg !== "RS256") return null;
  const jwk = (await certs()).find((k) => k.kid === head.kid); if (!jwk) return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64u(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
  const aud = Array.isArray(body.aud) ? body.aud : [body.aud];
  if (!ok || !aud.includes(AUD) || !body.exp || body.exp * 1000 < Date.now() || body.iss !== TEAM) return null;
  return String(body.email || "").toLowerCase() === OWNER ? body.email : null;
}

const shell = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>${esc(title)}</title><style>
:root{color-scheme:dark}*{box-sizing:border-box;min-width:0}body{margin:0;background:#0B0D10;color:#E8EAED;font:16px/1.55 Inter,system-ui,sans-serif}
main{max-width:1040px;margin:0 auto;padding:clamp(20px,4vw,48px) max(5vw,16px)}h1{font-size:clamp(26px,4vw,36px);line-height:1.1;margin:0 0 6px}h2{font-size:19px;margin:34px 0 12px}
.mut{color:#8B939C;font-size:14px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
.kpi{background:#11141A;border:1px solid #1C2026;border-radius:12px;padding:14px 16px}.kpi b{display:block;font-size:30px;line-height:1.1}.kpi span{color:#8B939C;font-size:13px}
.row{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,2fr) 48px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #1C2026;font-size:14.5px}
.bar{height:8px;border-radius:4px;background:#1C2026;overflow:hidden}.bar i{display:block;height:100%;background:#E2743B}.n{text-align:right;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid #1C2026;vertical-align:top}th{color:#8B939C;font-weight:600}
.scroll{overflow-x:auto}form{display:flex;gap:8px;max-width:360px}input{flex:1;min-height:48px;border-radius:12px;border:1px solid #2A3038;background:#111419;color:#E8EAED;padding:0 14px;font-size:20px;letter-spacing:.2em}
button,.btn{min-height:44px;padding:0 18px;border:0;border-radius:12px;background:#E8A87C;color:#14100C;font:600 15px Inter,system-ui,sans-serif;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center}
.e{color:#E8A87C}.top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}a{color:#F0C2A0}
</style></head><body><main>${body}</main></body></html>`;


const bars = (pairs, total) => pairs.map(([k, v]) => `<div class="row"><span>${esc(k)}</span><span class="bar"><i style="width:${total ? Math.round((v / total) * 100) : 0}%"></i></span><span class="n">${v}</span></div>`).join("") || `<p class="mut">None yet.</p>`;

async function dashboard(env) {
  const recs = []; let cursor;
  do { const r = await env.VOL.list({ prefix: "vol:", cursor }); for (const k of r.keys) { const v = await env.VOL.get(k.name, "json"); if (v) recs.push(v); } cursor = r.list_complete ? null : r.cursor; } while (cursor && recs.length < 5000);
  const now = Date.now(), day = 864e5, n = recs.length;
  const since = (d) => recs.filter((r) => now - Date.parse(r.created) <= d * day).length;
  const count = (f) => { const m = new Map(); for (const r of recs) for (const k of f(r)) m.set(k, (m.get(k) || 0) + 1); return [...m.entries()].sort((a, b) => b[1] - a[1]); };
  const area = count((r) => [r.area ? r.area.replace(/\s+/g, " ").trim().replace(/\b\w/g, (c) => c.toUpperCase()) : "Not given"]);
  const help = count((r) => (r.help && r.help.length ? r.help : ["Not chosen"]));
  const time = count((r) => [r.time || "Not chosen"]);
  const src = count((r) => [r.src ? "From the " + r.src + " page" : "Before 27 Nov (not recorded)"]);
  const tasks = Object.entries(TASKS).map(([k, label]) => [label, recs.filter((r) => r.tasks && r.tasks[k]).length]).sort((a, b) => b[1] - a[1]);
  const days = []; for (let i = 29; i >= 0; i--) { const d = new Date(now - i * day).toISOString().slice(0, 10); days.push([d.slice(5), recs.filter((r) => (r.created || "").slice(0, 10) === d).length]); }
  const maxDay = Math.max(1, ...days.map((d) => d[1]));
  const recent = [...recs].sort((a, b) => (b.created || "").localeCompare(a.created || "")).slice(0, 50);
  const fmt = (s) => (s ? new Date(s).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");
  return shell("arcroad · admin", `<div class="top"><div><p class="mut">arcroad · private · updated ${esc(fmt(new Date().toISOString()))} IST</p><h1>Citizens who signed up</h1></div><a class="btn" href="/cdn-cgi/access/logout">Sign out</a></div>
<div class="kpis"><div class="kpi"><b>${n}</b><span>sign-ups in total</span></div><div class="kpi"><b>${since(1)}</b><span>in the last 24 hours</span></div><div class="kpi"><b>${since(7)}</b><span>in the last 7 days</span></div><div class="kpi"><b>${since(30)}</b><span>in the last 30 days</span></div><div class="kpi"><b>${area.filter(([a]) => a !== "Not given").length}</b><span>different areas</span></div></div>
<h2>Sign-ups a day, last 30 days</h2>${days.map(([d, v]) => `<div class="row"><span>${d}</span><span class="bar"><i style="width:${Math.round((v / maxDay) * 100)}%"></i></span><span class="n">${v}</span></div>`).join("")}
<h2>By area</h2>${bars(area.slice(0, 40), n)}
<h2>Where they joined</h2>${bars(src, n)}
<h2>How they want to help</h2>${bars(help, n)}
<h2>Time offered</h2>${bars(time, n)}
<h2>Starter tasks ticked</h2>${bars(tasks, n)}
<h2>Latest 50</h2><div class="scroll"><table><thead><tr><th>When (IST)</th><th>Area</th><th>Help</th><th>Time</th></tr></thead><tbody>${recent.map((r) => `<tr><td>${esc(fmt(r.created))}</td><td>${esc(r.area || "")}</td><td>${esc((r.help || []).join("; "))}</td><td>${esc(r.time || "")}</td></tr>`).join("") || `<tr><td colspan="4" class="mut">None yet.</td></tr>`}</tbody></table></div>
<p class="mut" style="margin-top:28px">No names, emails, phone numbers or IP addresses are collected. Areas are as typed by each volunteer, with emails and phone numbers stripped on the way in.</p>`);
}

export async function onRequest({ request, env }) {
  if (!env.VOL) return new Response(shell("arcroad · admin", "<h1>Not set up yet</h1><p class='mut'>Storage is missing.</p>"), { status: 503, headers: H });
  let email = null; try { email = await accessEmail(request); } catch (e) { email = null; }
  if (!email) return new Response(shell("arcroad · admin", "<p class='mut'>arcroad · private</p><h1>Private page</h1><p class='mut'>Open <a href='https://arcroad.org/admin/'>arcroad.org/admin</a> and sign in with the code sent to the owner's email.</p>"), { status: 403, headers: H });
  return new Response(await dashboard(env), { headers: H });
}
