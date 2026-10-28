# Module spec: "The white beam"

Status: spec, approved in principle by Rohit on 28 Oct 2026. Not built.
Owner: Claude. Build runs on Rohit's iMac; deploy from his Terminal.
Where it lives: a card on the arcroad site (candidate placement: `web/act.html`,
beside the other "what you can do" items), not inside the detour model. It
publishes no modelled number and does not touch the Phase 2b gate.

## What it teaches, in one sentence

An over-powered or unaimed headlamp does not make the road darker for the
driver coming the other way; it throws a veil of scattered light inside their
eye that washes out the contrast of whatever is ahead of them, for a second or
two longer than the lamp is in view.

## The card (phone-height, nothing scrolls inside it)

- The view is the oncoming driver's eyes: a night road, a pedestrian crossing
  about 40 m ahead, a car approaching in the other lane.
- One slider, "Their headlamp": from *Stock, aimed* to *Aftermarket white,
  unaimed*. Moving it raises the illuminance at the eye (E). The scene gains a
  veil, the pedestrian loses contrast. Two live readouts:
  - "Pedestrian contrast": 100% at the left end, falling as the veil rises.
  - "Blind distance after they pass": the 1 to 2 s transient at the chosen
    speed (default 60 km/h = 16.7 m/s, so 17 to 33 m). Speed is a small
    stepper: 40 / 60 / 80 km/h.
- One toggle, "Driver's age": 25 / 60. The 60 setting widens the veil and
  lengthens recovery (see sources).
- One line beneath: *Permitted: white or yellowish-white, type-approved,
  aimed. Not permitted: unapproved high-wattage LED/HID, bar and show lights.*
  CMVR Rule 106 · AIS-010 · Bengaluru, Jan 2026: about 10,000 cases.
- Evidence labels in the house style: veil formula ESTABLISHED; age effect
  ESTABLISHED; Bengaluru figures and the W figures SUPPORTED (press report of
  a police statement); colour-temperature effect NOT MODELLED (no source yet).
- Honest caveat text: "A simplified model of the eye, not a measurement of any
  lamp. Colour (cool white vs warm) is not modelled until there is a source."

## The model behind the slider (all client-side, no data leaves the page)

- Veiling luminance (CIE disability-glare, Stiles-Holladay form):
  `Lv = 10 * E / theta^2`, E in lux at the eye, theta the angle between the
  line of sight and the glare source in degrees, valid for theta > 1 degree.
- Contrast of the pedestrian against the road:
  `C = (Lt - Lb) / (Lb + Lv)`. Readout shows C / C0 as a percentage.
- Age: use the CIE age factor `(1 + (age/62.5)^4)` as a multiplier on Lv
  (CIE 146/147:2002 general disability glare equation). This is the term
  behind the 25 / 60 toggle; cite it on the card.
- Transient: show 1 to 2 s as a range, never a single number; distance =
  speed * time.
- Slider endpoints are illustrative illuminance values; label them as such.
  Do not claim a specific lamp produces a specific lux.

## Design

Restraint carries the premium feel: dark full-bleed scene, one accent colour
for the beam, hairline controls, readouts in the site's mono type, the site's
existing type scale unchanged. No icons, no paragraphs inside the card. Pause
the animation off-screen; honour prefers-reduced-motion with a still frame at
the slider position.

## Sources (checked 28 Oct 2026)

- Higgins, K. E., *Physiology of glare and readaptation (including age
  differences)*, NHTSA Workshop on Headlamp Safety Metrics, 13 Jul 2004.
  Gives Lv = 10E/theta^2; "thresholds higher for older subjects under all
  conditions"; transient adaptation "in the initial 1-2 seconds after sudden
  change in light level".
  https://www.lrc.rpi.edu/programs/transportation/pdf/NITSA/HigginsNHTSAworkshop.pdf
- CIE 146/147:2002, *CIE equations for disability glare* (age term). To be
  cited from the CIE page when the card is built; not fetched this session.
- Deccan Herald, 12 Jan 2026, "Bengaluru: dazzling headlights land 10,000
  motorists in trouble": drive from 7 Jan 2026, 9,782 cases by Sunday;
  standard LED 4-12 W vs illegal fitments 50-100 W+; bar/show lights removed
  on the spot; white or warm-yellow permitted; cites CMVR and AIS-130 for LED
  source approval.
  https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fbengaluru%2Fbengaluru-dazzling-headlights-land-10000-motorists-in-trouble-3858981
- CMVR Rule 106 (headlamps) and AIS-010 (installation of lighting): confirm
  wording against the Ministry's text before publishing; the trade article
  used for the 70 W and fine figures (carzspa.com, 16 Mar 2026) is not an
  official source and its fine figures are NOT to be shown without the Act
  section.

## Not yet verified (do not publish until closed)

- Fine amounts and the Motor Vehicles Act section for lighting offences.
- Whether cool-white light raises disability or discomfort glare at equal
  illuminance (needed before any colour slider is added).
- Exact AIS-010 limits on luminous intensity for the "stock" endpoint label.
