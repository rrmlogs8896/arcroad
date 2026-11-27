// arcroad private admin (27 Nov 2026): visitor totals from our host and volunteer ("citizen") sign-ups, for Rohit only.
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

// Visitors (27 Nov 2026): our host's own anonymous totals, read from Cloudflare's analytics API with a
// read-only token (CF_STATS_TOKEN) for the arcroad.org zone (CF_ZONE). The site runs no script and sets
// no cookie for this; nothing here identifies anyone. "Browser-like" = page loads whose browser Cloudflare
// recognises, a rough way to set aside most bots. Groups under 3 fold into "Other".
const SCAN = /(^\/\.|\.env|\.git|wp-|\.php|phpinfo|xmlrpc|\/cgi-bin|\/vendor\/|\.aspx?$|\.sql|\.bak|\.save|\/admin\.|\/config)/i;
const IGNORE404 = /^\/cdn-cgi\/|^\/data:|^\/\.well-known\/|^\/humans\.txt$|^\/apple-touch-icon/;
const PAGE_SRC = { "/": "home", "/cost/": "cost", "/roads/": "roads", "/field/": "field", "/moves/": "moves", "/uturns/": "uturns", "/report/": "report", "/globe/": "globe", "/volunteer/": "volunteer" };
async function visitors(env) {
  if (!env.CF_STATS_TOKEN || !env.CF_ZONE) return null;
  const now = Date.now(), s7 = new Date(now - 7 * 864e5).toISOString(), d14 = new Date(now - 14 * 864e5).toISOString().slice(0, 10);
  const B = 'requestSource:"eyeball",edgeResponseContentTypeName:"html",datetime_geq:$s';
  const HU = B + ',userAgentBrowser_neq:"Unknown"';
  const q = `query($z:String!,$s:Time!,$d:Date!){viewer{zones(filter:{zoneTag:$z}){
    raw: httpRequests1dGroups(limit:20,filter:{date_geq:$d},orderBy:[date_ASC]){dimensions{date} uniq{uniques} sum{pageViews}}
    hDay: httpRequestsAdaptiveGroups(limit:20,filter:{${HU}},orderBy:[date_ASC]){count dimensions{date}}
    hPages: httpRequestsAdaptiveGroups(limit:25,filter:{${HU},edgeResponseStatus:200},orderBy:[count_DESC]){count dimensions{clientRequestPath}}
    hCountry: httpRequestsAdaptiveGroups(limit:40,filter:{${HU}},orderBy:[count_DESC]){count dimensions{clientCountryName}}
    hDev: httpRequestsAdaptiveGroups(limit:5,filter:{${HU}},orderBy:[count_DESC]){count dimensions{clientDeviceType}}
    hOS: httpRequestsAdaptiveGroups(limit:8,filter:{${HU}},orderBy:[count_DESC]){count dimensions{userAgentOS}}
    hHour: httpRequestsAdaptiveGroups(limit:200,filter:{${HU}},orderBy:[count_DESC]){count dimensions{datetimeHour}}
    all: httpRequestsAdaptiveGroups(limit:1,filter:{${B}}){count}
    nf: httpRequestsAdaptiveGroups(limit:60,filter:{requestSource:"eyeball",datetime_geq:$s,edgeResponseStatus:404},orderBy:[count_DESC]){count dimensions{clientRequestPath}}
  }}}`;
  const r = await fetch("https://api.cloudflare.com/client/v4/graphql", { method: "POST", headers: { authorization: "Bearer " + env.CF_STATS_TOKEN, "content-type": "application/json" }, body: JSON.stringify({ query: q, variables: { z: env.CF_ZONE, s: s7, d: d14 } }) });
  const j = await r.json().catch(() => null);
  if (!j || j.errors || !j.data) return { error: (j && j.errors && j.errors[0] && j.errors[0].message) || "Cloudflare did not answer" };
  return j.data.viewer.zones[0];
}
function visitorsHtml(v, recs, bars) {
  if (!v) return `<h2 id="visitors">Visitors</h2><p class="mut">Not connected yet: the read-only analytics token has not been added.</p>`;
  if (v.error) return `<h2 id="visitors">Visitors</h2><p class="mut">Could not load visitor totals (${esc(v.error)}).</p>`;
  const sum = (a) => a.reduce((t, x) => t + x.count, 0);
  const pair = (a, k) => a.map((x) => [x.dimensions[k], x.count]);
  const fold = (ps) => { const keep = ps.filter(([, c]) => c >= 3), o = ps.filter(([, c]) => c < 3).reduce((t, [, c]) => t + c, 0); return o ? [...keep, ["Other", o]] : keep; };
  const human = sum(v.hDay), all = v.all[0] ? v.all[0].count : 0;
  const pages = pair(v.hPages, "clientRequestPath").filter(([p]) => !p.startsWith("/cdn-cgi/"));
  const home = (pages.find(([p]) => p === "/") || [, 0])[1], inner = pages.filter(([p]) => p !== "/").reduce((t, [, c]) => t + c, 0);
  const dev = pair(v.hDev, "clientDeviceType"), phone = (dev.find(([d]) => d === "mobile") || [, 0])[1];
  const hours = Array(24).fill(0); for (const h of v.hHour) { const d = new Date(new Date(h.dimensions.datetimeHour).getTime() + 330 * 60e3); hours[d.getUTCHours()] += h.count; }
  const maxH = Math.max(1, ...hours), peak = hours.indexOf(Math.max(...hours));
  const nf = pair(v.nf, "clientRequestPath"), probes = nf.filter(([p]) => SCAN.test(p)).reduce((t, [, c]) => t + c, 0);
  const broken = nf.filter(([p]) => !SCAN.test(p) && !IGNORE404.test(p)).slice(0, 15);
  const wk = Date.now() - 7 * 864e5, joins = {}; for (const x of recs) if (x.src && Date.parse(x.created) >= wk) joins[x.src] = (joins[x.src] || 0) + 1;
  const conv = Object.entries(PAGE_SRC).map(([p, s]) => { const views = (pages.find(([q]) => q === p) || [, 0])[1], n = joins[s] || 0; return [p, views, n, views ? (n / views * 100) : 0]; }).filter(([, views, n]) => views || n);
  const raw = v.raw.map((x) => [x.dimensions.date.slice(5), x.sum.pageViews, x.uniq.uniques]), maxR = Math.max(1, ...raw.map((x) => x[1]));
  const hd = pair(v.hDay, "date").map(([d, c]) => [d.slice(5), c]), maxD = Math.max(1, ...hd.map((x) => x[1]));
  const pct = (a, b) => (b ? Math.round(a / b * 100) : 0) + "%";
  return `<h2 id="visitors">Visitors, last 7 days</h2>
<p class="mut">Counted by our host from page loads; nothing is collected in visitors' browsers. Browser-like loads set most bots aside but not all.</p>
<div class="kpis"><div class="kpi"><b>${human.toLocaleString("en-IN")}</b><span>browser-like page views</span></div><div class="kpi"><b>${pct(human, all)}</b><span>of all page loads look human</span></div><div class="kpi"><b>${pct(inner, home + inner)}</b><span>of views go past the home page</span></div><div class="kpi"><b>${pct(phone, human)}</b><span>on phones</span></div><div class="kpi"><b>${String(peak).padStart(2, "0")}:00</b><span>busiest hour (IST)</span></div><div class="kpi"><b>${broken.reduce((t, [, c]) => t + c, 0)}</b><span>visits to broken links</span></div></div>
<h2>Browser-like views a day</h2>${hd.map(([d, c]) => `<div class="row"><span>${d}</span><span class="bar"><i style="width:${Math.round(c / maxD * 100)}%"></i></span><span class="n">${c}</span></div>`).join("")}
<h2>Pages people read</h2>${bars(pages.slice(0, 20), pages.length ? pages[0][1] : 1)}
<h2>Join card: views and sign-ups, last 7 days</h2><div class="scroll"><table><thead><tr><th>Page</th><th>Views</th><th>Joined there</th><th>Rate</th></tr></thead><tbody>${conv.map(([p, views, n, r]) => `<tr><td>${esc(p)}</td><td>${views}</td><td>${n}</td><td>${r.toFixed(1)}%</td></tr>`).join("")}</tbody></table></div>
<h2>Countries</h2>${bars(fold(pair(v.hCountry, "clientCountryName")), v.hCountry.length ? v.hCountry[0].count : 1)}
<h2>Devices and systems</h2>${bars(dev, human)}${bars(fold(pair(v.hOS, "userAgentOS")), human)}
<h2>Hour of day (IST)</h2><div style="display:grid;grid-template-columns:repeat(24,1fr);gap:3px;align-items:end;height:120px;border-bottom:1px solid #1C2026">${hours.map((c, h) => `<i title="${String(h).padStart(2, "0")}:00 IST, ${c} views" style="display:block;height:${Math.max(2, Math.round(c / maxH * 100))}%;background:${h === peak ? "#E8A87C" : "#E2743B"};border-radius:3px 3px 0 0;opacity:${c ? 1 : .25}"></i>`).join("")}</div><div class="mut" style="display:grid;grid-template-columns:repeat(4,1fr);font-size:12px;margin-top:4px"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span></div>
<h2>Broken links to fix</h2>${broken.length ? bars(broken, broken.reduce((t, [, c]) => t + c, 0)) : `<p class="mut">None this week.</p>`}
<p class="mut">${probes} requests from scanners probing for files that do not exist (such as .env or wp-login) were turned away.</p>
<h2>Raw host totals, last 14 days</h2><p class="mut">Every page load including bots, and unique addresses as the host counts them. For context only.</p><div class="scroll"><table><thead><tr><th>Day</th><th>Page views</th><th>Unique addresses</th></tr></thead><tbody>${raw.map(([d, p, u]) => `<tr><td>${d}</td><td>${p}</td><td>${u}</td></tr>`).join("")}</tbody></table></div>`;
}

async function dashboard(env) {
  const recs = []; let cursor;
  do { const r = await env.VOL.list({ prefix: "vol:", cursor }); for (const k of r.keys) { const v = await env.VOL.get(k.name, "json"); if (v) recs.push(v); } cursor = r.list_complete ? null : r.cursor; } while (cursor && recs.length < 5000);
  const now = Date.now(), day = 864e5, n = recs.length;
  let vraw; try { vraw = await visitors(env); } catch (e) { vraw = { error: "Cloudflare did not answer" }; }
  const vis = visitorsHtml(vraw, recs, bars);
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
  return shell("arcroad · admin", `<div class="top"><div><p class="mut">arcroad · private · updated ${esc(fmt(new Date().toISOString()))} IST</p><h1>arcroad admin</h1><p class="mut"><a href="#visitors">Visitors</a> · <a href="#volunteers">Volunteers</a></p></div><a class="btn" href="/cdn-cgi/access/logout">Sign out</a></div>
${vis}
<h2 id="volunteers" style="margin-top:48px;font-size:24px">Citizens who signed up</h2>
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
