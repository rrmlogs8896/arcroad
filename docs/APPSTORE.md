# arcroad on the App Store: listing and submission

Drafted 3 Nov 2026. Everything below is pasted into App Store Connect by the account holder.

## Before you start (one-time, account holder only)

1. **Apple Developer Program:** $99 a year, currently ₹8,700 in India. Enrol as an individual. Your legal name appears on the App Store as the seller.
2. **Xcode 26 or later** on the iMac.
3. **App Store Connect:** My Apps › + › New App.
   - Platform iOS, name **arcroad** (choose a fallback below if it's taken).
   - Language English (U.K.).
   - Bundle ID `org.arcroad.app`.
   - SKU `arcroad-ios-1`.

## Listing

- **Name (30 chars):** arcroad
  - Fallbacks: "arcroad: Road Detours", "arcroad · cost of a crossing"
- **Subtitle (30):** What crossing your road costs
- **Category:** Navigation (secondary: Reference)
- **Price:** Free, with no in-app purchases.
- **Promotional text (170):** Six short films, a 3D ride on the real clock, and a recorder to measure your own crossing. Built from open data, checked by driving.
- **Keywords (100):** median,u-turn,detour,road,traffic,hyderabad,commute,crossing,divided road,civic,open data,map
- **Support URL:** https://arcroad.org/help/
- **Marketing URL:** https://arcroad.org/
- **Privacy Policy URL:** https://arcroad.org/help/#privacy
  - Make sure that anchor exists before you submit, or use https://arcroad.org/help/.

**Description:**

```
A place you can see, 1.5 km away.

Divided roads cut neighbours off. The shop, the school or the office you can see across the median can be more than a kilometre away by road, because the nearest U-turn is far down the road. arcroad measures what that costs, from open map data, and then drives the detour to check.

RIDE IT
Take the wheel for a detour we drove, on its real clock, in 3D. Switch between day and night, see the glare of oncoming high beams after dark, and pick from the places we have driven.

WHAT COULD FIX IT
See a nearer U-turn, a signal or an underpass drawn on the same street, each with the guidance it follows and its trade-off. They are illustrations, not designs: the road owner decides.

RECORD YOUR OWN CROSSING
Drive from one side of the median to the other and your iPhone measures the distance and the time. The GPS track never leaves your phone and is deleted once it is measured. Share the one-line summary with arcroad if you want it counted.

HONEST BY DESIGN
Every number traces to a dated drive or open dataset. A place gets a detour figure only after it is driven. No account, no ads, no tracking.

Map data © OpenStreetMap contributors (ODbL).
```

## App Privacy (the "nutrition label")

- Data collection: **No, we do not collect data from this app.**
  - The location used while recording is processed only on the device and is never sent to the developer or anyone else, so under Apple's definition it is not collected.
- Tracking: **No.**

## Age rating

Answer "None" to every content question. The expected rating is 4+.

## Review notes (App Review Information › Notes)

```
arcroad shows the detour that divided roads force on people living beside them, measured from open map data and checked by driving.

Native features beyond the website:
1. Record (tab 4): records one crossing with GPS while the app is open and scores it on the device (it must come within 10 m of both sides of the median, within 30 minutes). The track is held in memory only and deleted after scoring; nothing is uploaded. To try it outside India, pick any place, tap Start, and in the Simulator use Features > Location > Freeway Drive; it will report "No crossing found" with the reason, which is the expected result away from these places.
2. Places (tab 3): native list of measured places from the bundled data; driven places open their 3D ride, others offer recording.
3. The full site is bundled and works offline; films and the 3D ride run locally.

No login, no in-app purchases, no third-party SDKs, no data collection.
Contact: hello@arcroad.org
```

## Screenshots (iPhone 6.9" required: 1320 × 2868, 3 to 10 of them)

1. The home film, with the caption visible
2. Drive it at night, glare on
3. Drive it: "What could fix this" with the underpass
4. Places list
5. Record, while recording (A reached)
6. Record, result card

Take them in the iPhone 17 Pro Max simulator (⌘S saves to the Desktop).

## Not in version 1

- Background recording. It would need "Always" location, which draws extra review scrutiny and isn't needed when the app is open.
- Sign-in.
- Push notifications.
- Android.
