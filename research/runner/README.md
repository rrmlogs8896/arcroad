# arcroad research runner (Cloudflare Containers)

A Worker with no public route. At 22:00 IST every night, a cron trigger starts one container (standard-1: ½ vCPU, 4 GiB). The container runs its jobs one after another. A second cron polls every 10 minutes while a job is running and files each finished result in the private R2 bucket `arcroad-research` under `nights/<date>/`. When nothing is running, nothing polls, and the container sleeps after 30 minutes.

## Jobs

1. **openings**: pre-registered in `docs/PREREG-openings.md`. For each place it records whether a public road meets the divided road, whether a signal is nearby, and how many traffic-calming features (speed breakers) are mapped within 750 m. Places are compared against control points.
2. **bengaluru**: the same candidate collection as the monthly GitHub workflow (`tools/multicity_collect.py bengaluru --detour`). Its output is a candidate and is not published.

## Deploy (iMac, Docker Desktop running)

```
cd ~/Sites/arcroad-mirror/research/runner && npm install && npx wrangler r2 bucket create arcroad-research && npx wrangler deploy
```

## Read a night's results

```
npx wrangler r2 object get arcroad-research/nights/<date>/openings.json --remote --file openings.json
```

## Cost

The plan includes 375 vCPU-minutes a month. A night that runs both jobs for an hour uses about 30 vCPU-minutes (½ vCPU × 60 min).
