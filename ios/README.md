# arcroad for iPhone

A native SwiftUI app around the arcroad site. The site is bundled into the app, so it works offline. The app adds things the website can't do:

- **Record a crossing.** It uses the phone's GPS while you drive from one side of a median to the other, and scores the drive on the phone with the same rule as `pipeline/groundtruth.py`. The track stays in memory and is deleted after scoring. Only a summary you choose to share leaves the phone.
- **Places, natively.** Places that have been driven open their 3D ride. Places not driven yet show only the straight line across, with a button to record them.
- **Five tabs.** arcroad (the home page with the films), Drive it, Places, Record and About. The website's own header and menu are hidden inside the app, but the attribution footer is kept.

There is no account, no analytics and no third-party code. The privacy manifest declares no data collected.

## Build (on the iMac)

You need Xcode 26 or later. App Store Connect has refused uploads from older Xcode versions since 28 April 2026.

```
brew install xcodegen
cd ~/Sites/arcroad-mirror/ios && xcodegen generate && open arcroad.xcodeproj
```

1. In Xcode, open the arcroad target, then Signing & Capabilities, and pick your Team.
2. Choose an iPhone simulator and run it with ⌘R.
3. To test GPS in the simulator, use Features › Location › Freeway Drive. To record a real crossing, run it on your own iPhone.
4. To ship: Product › Archive, then Distribute App › App Store Connect, then Upload.

A build phase copies `../web` into the app on every build, leaving out the 1440p and 4K films (an iPhone screen never needs them). So the app always carries whatever version of the site is in this folder.

## Files

| File | What it does |
|---|---|
| `project.yml` | XcodeGen spec: bundle id `org.arcroad.app`, iOS 17+, iPhone only, location permission text |
| `arcroad/Site.swift` | Serves the bundled site at `arcroad://app/` with byte ranges, so the films play |
| `arcroad/WebScreen.swift` | Web view for a site page; links to other sites open in Safari |
| `arcroad/Places.swift` | Reads `globe/data/places.json` and `kit/pairs.js` from the bundle |
| `arcroad/Recorder.swift` | GPS recording and on-device scoring (10 m reach, 30 min, 15 s gap) |
| `arcroad/RecordView.swift`, `PlacesView.swift`, `AboutView.swift`, `RootView.swift` | Screens |
| `arcroad/PrivacyInfo.xcprivacy` | Privacy manifest: no tracking, no data collected |

App Store listing, privacy answers and review notes: `docs/APPSTORE.md`.
