// arcroad research runner: a Worker that starts the night's jobs in a Cloudflare Container and
// files each result in the private R2 bucket "arcroad-research". It has no public route.
import { Container, getContainer } from "@cloudflare/containers";

interface Env {
  RUNNER: DurableObjectNamespace<ResearchRunner>;
  OUT: R2Bucket;
  // Set with `npx wrangler secret put <NAME>` (hidden prompt); never in a file or the repo.
  MAPILLARY_TOKEN?: string;
  ANTHROPIC_API_KEY?: string;
  EYELAB_API_KEY?: string; // its own Console workspace, monthly spend limit USD 5: the Saturday 13point8 research scan
  VIABILITY_API_KEY?: string; // its own Console workspace, monthly spend limit USD 10: the weekly viability brief
  GITHUB_TOKEN?: string; // fine-grained, arcroad-internal only, Contents read/write: files night results
}

export class ResearchRunner extends Container<Env> {
  defaultPort = 8080;
  sleepAfter = "30m"; // the poll every 10 minutes keeps it awake only while a job runs
  constructor(ctx: DurableObjectState<{}>, env: Env) {
    super(ctx, env);
    this.envVars = { MAPILLARY_TOKEN: env.MAPILLARY_TOKEN ?? "", ANTHROPIC_API_KEY: env.ANTHROPIC_API_KEY ?? "", GITHUB_TOKEN: env.GITHUB_TOKEN ?? "", VIABILITY_API_KEY: env.VIABILITY_API_KEY ?? "", EYELAB_API_KEY: env.EYELAB_API_KEY ?? "" };
  }
}

type Status = { running: boolean; done: string[]; failed: Record<string, string>; log: string[]; boot?: string };
type State = { running: boolean; started?: string; filed: string[]; night?: string; boot?: string; current?: string; restarts?: number; crashed?: string[] };
const MAX_RESTARTS = 3; // a night resumes after at most this many container restarts

const START_CRON = "30 16 * * *"; // 22:00 IST

async function readState(env: Env): Promise<State> {
  const o = await env.OUT.get("state.json");
  return o ? ((await o.json()) as State) : { running: false, filed: [] };
}
const writeState = (env: Env, s: State) => env.OUT.put("state.json", JSON.stringify(s, null, 1));

export default {
  async fetch(): Promise<Response> {
    return new Response("Not found", { status: 404 });
  },

  async scheduled(event: ScheduledController, env: Env): Promise<void> {
    const runner = getContainer(env.RUNNER, "nightly");
    const state = await readState(env);

    if (event.cron === START_CRON) {
      if (state.running) return;
      await runner.fetch(new Request("http://runner/start"));
      const night = new Date().toISOString().slice(0, 10);
      await writeState(env, { running: true, started: new Date().toISOString(), filed: [], night });
      return;
    }

    if (!state.running) return; // nothing to watch: let the container sleep
    const st = (await (await runner.fetch(new Request("http://runner/status"))).json()) as Status;

    // The container restarted mid-night (memory, host maintenance): its fresh process knows nothing.
    // Resume with the jobs not yet filed, instead of ending the night silently (the 24-25 Nov bug).
    // A job running at two restarts is treated as the cause and skipped.
    if (state.boot && st.boot && st.boot !== state.boot && !st.running && st.done.length === 0) {
      const crashed = state.crashed ?? [];
      if (state.current && !state.filed.includes(state.current)) crashed.push(state.current);
      const twice = crashed.filter((j, i) => crashed.indexOf(j) !== i);
      state.crashed = crashed;
      state.restarts = (state.restarts ?? 0) + 1;
      await env.OUT.put(`nights/${state.night}/restart-${state.restarts}.json`,
        JSON.stringify({ at: new Date().toISOString(), was_running: state.current ?? null, filed: state.filed }, null, 1));
      if (state.restarts <= MAX_RESTARTS) {
        const skip = [...new Set([...state.filed, ...twice])].join(",");
        await runner.fetch(new Request(`http://runner/start?night=${state.night}&skip=${encodeURIComponent(skip)}`));
        state.boot = st.boot;
        await writeState(env, state);
        return;
      }
      state.running = false;
      await writeState(env, state);
      return;
    }
    state.boot = st.boot ?? state.boot;
    const starts = st.log.filter((l) => l.includes(" start ")).pop();
    if (starts) state.current = starts.split(" start ")[1]?.trim();
    for (const job of st.done) {
      if (state.filed.includes(job)) continue;
      const r = await runner.fetch(new Request(`http://runner/result/${job}`));
      if (!r.ok) continue;
      const ext = r.headers.get("Content-Type")?.includes("json") ? "json" : "tar.gz";
      await env.OUT.put(`nights/${state.night}/${job}.${ext}`, await r.arrayBuffer());
      state.filed.push(job);
    }
    await env.OUT.put(`nights/${state.night}/status.json`, JSON.stringify(st, null, 1));
    if (!st.running) state.running = false;
    await writeState(env, state);
  },
};
