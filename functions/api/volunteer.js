// Volunteer sign-ups, saved straight to arcroad (26 Nov 2026). No name, email, phone or IP is stored:
// only a random code made on the volunteer's device, the area typed, the ways chosen, the time offered and
// which starter tasks are ticked. The volunteer can remove it at any time (DELETE with the same code).
const CODE = /^AR-V-\d{6}-[A-Z0-9]{4}$/;
const HELP = ["Driving and timing a crossing near me", "Photographing a place (faces and plates blurred)", "Fixing roads on OpenStreetMap", "Telling my resident association or college", "Running arcroad for another city"];
const TIME = ["An hour or two, once", "A few hours a month", "More, regularly"];
const TASKS = ["check", "map", "report", "tell", "cost"];
const SRC = ["volunteer", "home", "cost", "roads", "field", "moves", "uturns", "report", "globe"];
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });
const clean = (s) => String(s || "").replace(/\S+@\S+/g, "").replace(/\+?\d[\d\s-]{7,}\d/g, "").replace(/[<>]/g, "").replace(/\s+/g, " ").trim().slice(0, 80);

export async function onRequestPost({ request, env }) {
  if (!env.VOL) return json({ ok: false, error: "not ready" }, 503);
  const len = Number(request.headers.get("content-length") || 0);
  if (len > 2048) return json({ ok: false, error: "too large" }, 413);
  let b; try { b = await request.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }
  if (!CODE.test(b.code || "")) return json({ ok: false, error: "bad code" }, 400);
  const key = "vol:" + b.code, now = new Date().toISOString();
  const old = await env.VOL.get(key, "json");
  const rec = {
    code: b.code,
    area: clean(b.area),
    help: (Array.isArray(b.help) ? b.help : []).filter((h) => HELP.includes(h)),
    time: TIME.includes(b.time) ? b.time : "",
    tasks: Object.fromEntries(TASKS.map((t) => [t, !!(b.tasks && b.tasks[t])])),
    src: old && old.src ? old.src : SRC.includes(b.src) ? b.src : "",
    created: old ? old.created : now,
    updated: now,
  };
  await env.VOL.put(key, JSON.stringify(rec), { expirationTtl: 60 * 60 * 24 * 366 });
  return json({ ok: true });
}

export async function onRequestDelete({ request, env }) {
  if (!env.VOL) return json({ ok: false }, 503);
  const code = new URL(request.url).searchParams.get("code") || "";
  if (!CODE.test(code)) return json({ ok: false, error: "bad code" }, 400);
  await env.VOL.delete("vol:" + code);
  return json({ ok: true });
}

;(globalThis.__ar=globalThis.__ar||[]).push("ar-5f1c0a7e93b2");

// Public count of sign-ups (a number only), cached for a minute at the edge.
export async function onRequestGet({ env }) {
  if (!env.VOL) return json({ count: null });
  let n = 0, cursor;
  do { const r = await env.VOL.list({ prefix: "vol:", cursor }); n += r.keys.length; cursor = r.list_complete ? null : r.cursor; } while (cursor);
  return new Response(JSON.stringify({ count: n }), { headers: { "content-type": "application/json", "cache-control": "public, max-age=60" } });
}
