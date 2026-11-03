# arcroad research runner (Cloudflare Containers)

A Worker with no public route. At 22:00 IST every night, a cron trigger starts one container (standard-1: ½ vCPU, 4 GiB). The container runs its jobs one after another. A second cron polls every 10 minutes while a job is running and files each finished result in the private R2 bucket `arcroad-research` under `nights/<date>/`. When nothing is running, nothing polls, and the container sleeps after 30 minutes.

## Jobs

1. **openings**: pre-registered in `docs/PREREG-openings.md`. For each place it records whether a public road meets the divided road, whether a signal is nearby, and how many traffic-calming features (speed breakers) are mapped within 750 m. Places are compared against control points.
2. **mapwatch**: road, turn-rule and signal edits within 1 km of each place in the last 48 hours (OpenStreetMap). Any hit puts the place on a re-check list. A few minutes.
3. **routercheck**: pre-registered in `docs/PREREG-routercheck.md`. Routes every place both ways with OSRM and Valhalla, which obey turn restrictions, and compares them with arcroad's model and with the drives. About 3 minutes.
4. **hotspots**: pre-registered in `docs/PREREG-hotspots.md`. Ranks crossing pressure across Hyderabad and at each place from where people live (GHSL, cross-checked with WorldPop), where they go during the day and how much main road serves them (OpenStreetMap). A pressure proxy, not counted traffic. Adds about 10 minutes.
5. **bengaluru**: the same candidate collection as the monthly GitHub workflow (`tools/multicity_collect.py bengaluru --detour`). Its output is a candidate and is not published.

## Deploy (iMac, Docker Desktop running)

```
cd ~/Sites/arcroad-mirror/research/runner && npm install && npx wrangler r2 bucket create arcroad-research && npx wrangler deploy
```

## Read a night's results

```
npx wrangler r2 object get arcroad-research/nights/<date>/openings.json --remote --file openings.json
```

## Cost

The plan includes 375 vCPU-minutes a month. A night that runs all five jobs for an hour uses about 30 vCPU-minutes (½ vCPU × 60 min).
