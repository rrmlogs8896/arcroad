# The arcroad engine — what a street is like to live with

Set 1 Nov 2026 from Rohit's brief: the engine combines citizen behaviour, civic sense, vehicle behaviour, potholes, ad-hoc cut-ins, temporary stops, barricades and construction stages, mapped against official government data, plus the fixed things in the road that obstruct daily life (structures of any kind, trees, poles, kiosks). Everything is combined into one model per stretch of road, which drives the score, the immersive ride and the public record.

## Layers

| Layer | What it captures | How it is measured | Code |
|---|---|---|---|
| 1. Network | Legal paths, median gaps, U-turns, one-ways | OSM network + driven ground truth | `groundtruth.py`, `filters.py` |
| 2. Detour | What crossing your own road costs: metres, minutes, waits | Driven pass per spot | `fieldkit.scene` |
| 3. Surface | Potholes, broken patches, speed breakers | Vertical jolts at speed, repeat passes, photos | `fieldkit.jolts` |
| 4. Behaviour | Sudden stops, cut-ins and jinks, wrong-side driving, stops in the carriageway | Hard braking (GPS), short yaw spikes at speed (gyro), photos | `fieldkit.hard_brakes`, `fieldkit.swerves` |
| 5. Works | Barricades, diversions, construction stage (dug, half-built, finished, abandoned) | Photos dated by EXIF, matched to official works records | planned |
| 6. Fixed obstructions | Anything permanent in the carriageway or footpath: a structure, a tree, a transformer, a pole, a kiosk | OSM tags and photos, checked against official encroachment and works lists | planned |
| 8. Economics | What the detours and road conditions cost: fuel, tolls, taxes inside the fuel price, time, and the total for a city | Driven extra km × fuel use × live pump price; price build-up from official data; time valued with official wage data | planned |
| 7. Civic | Who is responsible for this stretch, and what they have said or promised | Road owner (NHAI, ORR operator, corporation), works orders, court directions | `directory.py` |

## Rules that make the combination trustworthy

1. **Every event is a candidate until confirmed** by a second pass, a photo or an official record. Thresholds are fixed in code before any data is looked at (rule 5).
2. **Behaviour is aggregate, never personal.** No number plates, faces or identifiable vehicles are stored or shown. A stretch can be "frequent sudden stops at 6 pm"; a person or vehicle never appears.
3. **Fixed obstructions are described by what they do, never by who they belong to.**
   - A structure in the carriageway is recorded as "permanent structure, narrows the road from 3 lanes to 2", whatever its kind. A place of worship is never labelled as an obstruction by faith, and no faith or community is singled out.
   - Where it matters legally, the record cites the official position. The Supreme Court's interim order of 29 Sep 2009 in *Union of India v. State of Gujarat* (SLP (C) 8519/2006) bars new unauthorised religious construction of any faith on public streets, parks and public places, and later orders made each state responsible for review. The record cites the order and the responsible office, not the structure's religion.
   - Trees are recorded the same way, and never with a suggestion to cut them: the city's tree and works authorities decide.
4. **Official data wins on facts, measurement wins on conditions.** A works order says what was planned and when. A dated photo says what is there today. Where they disagree, both are shown with their dates.
5. **Every published item keeps its provenance:** source, date observed, pass count, method version.

## Economics layer (added 1 Nov 2026 from Rohit's brief: charges, taxes, fuel, current Brent, impact on GDP)

The chain, each link sourced and dated:

1. **Brent crude** (international benchmark, US$/barrel, daily) → **Indian basket** of crude the refiners actually buy.
2. **Pump price build-up** of petrol and diesel: refinery and dealer price, Central excise duty, dealer commission, and the state's VAT. It shows how much of each litre is tax.
3. **Per trip:** the extra km of a detour × the vehicle's fuel use × today's Hyderabad pump price, plus any toll. Split into fuel cost, the tax part of that fuel, and time (at an official average wage).
4. **Per city, per year:** per-trip cost × estimated crossings per day (from traffic counts where official ones exist; otherwise a labelled range) × 365.
5. **Against the economy:** the city total shown next to Telangana's GSDP and India's GDP as a share. It is called an estimated cost to people, never a "GDP loss", because GDP measures output, not wasted time. Every assumption is shown and adjustable.

Rules: fuel prices are refreshed daily from the official source and carry their date. Brent moves the estimate only through the published pump price, never by an assumed pass-through. Ranges are shown wherever the traffic count is estimated.

Sources to verify before ingest: PPAC (Ministry of Petroleum) price build-up and the Indian basket; US EIA daily Brent series (public domain); Telangana's VAT rate on petrol and diesel (state notification); NHAI fee plazas and the ORR toll schedule; MoSPI/RBI GDP and Telangana GSDP; PLFS wages for the value of time.

## Evidence base: independent studies on behaviour and civic sense (gathered 1 Nov 2026)

These are outside numbers the behaviour and civic layers are checked against. They are **priors and context, not our findings**. Our own numbers come only from driven passes. Each line is a paraphrase with its source. No text, tables or charts are copied. Every link is re-checked before anything is published.

**Grades:** A = peer-reviewed field observation · B = official statistics · C = survey (self-reported, or sponsored) · D = press or commercial, method not disclosed. Only A and B may appear as a comparison on the public site. C and D stay internal.

### Wrong-side driving and lane discipline (layer 4)

| Finding | Grade | Source |
|---|---|---|
| In 2023, wrong-side driving and lane indiscipline accounted for about 5.5% of road deaths nationally. They were the third-largest cause of crashes, with 25,242 crashes and 9,432 deaths. Over-speeding was about 68%. Deaths from wrong-side driving rose about 8% between 2018 and 2023. | B | MoRTH, *Road Accidents in India 2023* (released Aug 2025), as reported by PTI, CAG Chennai and Factly/Dataful. Primary PDF to fetch from morth.nic.in. |
| On national highways in 2022, wrong-side driving was the second-largest cause of deaths (5.8%). The authors call for enforcement and cultural shifts, not just new laws. | A (conference) | IIT Delhi TRIPP (Deepty Jain et al.), World Congress on Injury Prevention and Safety Promotion. |
| Lane indiscipline happens on urban roads as well as highways, even in school-bus fleets. It falls with ADAS feedback plus training. | B/A (pilot) | iRASTE (IIIT Hyderabad INAI, Nagpur and Telangana deployments). |
| In India's mixed traffic, the side-to-side movement of vehicles is a measurable trait in its own right. Lateral clearance differs by vehicle class (for example, three-wheelers keep less gap on the left). | A | Chauhan, Dhamaniya, Arkatkar (SVNIT), Springer 2024; Jurnal Teknologi 78:4 (2016). |
| Wrong-way driving is common enough in India that countermeasures must be designed for India; studies from countries where it is rare do not transfer. | A | TRB TRID record 01994083 (field investigation of crash sites). |

**Hyderabad context (grade D, enforcement counts, not how common a behaviour is):**
- Hyderabad City Traffic Police booked about 4.4 lakh wrong-side challans on two- and three-wheelers in 2024, against about 5.1 lakh in 2023. Four-wheeler wrong-side challans fell sharply (RTI, NewsMeter, Jun 2025).
- Week-long drives in 2025 booked 13,000 to 15,000 wrong-side cases each.
- Rachakonda Traffic Police issued about 1.6 lakh wrong-side challans in 2025.
- Challans measure where police looked, not where people break the rule, so they are never used as a prior for prevalence.

### Headlight glare on the oncoming driver (layer 4 and the immersive ride; added 1 Nov 2026 at Rohit's request)

**Why it matters:** the person facing the light pays for it, not the driver who switched it on. Glare is a behaviour that harms someone else, the same as a cut-in.

| Fact | Grade | Source |
|---|---|---|
| Rule 106 of the Central Motor Vehicles Rules requires headlamps that can be dipped so they do not dazzle the driver of an approaching vehicle. Fines are under MVA s.177 (₹500 first offence, up to ₹1,000 after), and in some places s.184 (dangerous driving). | B (law, wording to verify from the CMVR text) | CMVR 1989 r.106; MVA 1988 ss.177, 184 |
| The Centre told Parliament it keeps no separate data on crashes caused by high-beam glare. About 2.24 lakh of the 4.61 lakh crashes in 2022 happened between 6 pm and 6 am, and over 94,000 between 6 pm and 9 pm alone. | B | MoRTH reply in Parliament, via The Tribune |
| Disability glare (a real loss of vision) is a different thing from discomfort glare (annoyance). After passing a bright oncoming lamp, the eye needs time to recover. Recovery takes longer with more light, for objects at the edge of view, and for older drivers. How uncomfortable a light feels does not predict how much it blinds. | A | Skinner & Bullough, SAE 2009-01-0546 (LRC/NHTSA field study); NHTSA DOT HS 811 043 / 811 007 |
| Glare shortens how far you can see, slows reaction and lengthens recovery. A NHTSA pilot found about two-thirds of headlights were aimed wrongly. | A/B | NHTSA glare reports to Congress (SAFETEA-LU s.2015) |
| In 2016 night tests on Punjab and Haryana highways, about 74% of car and SUV drivers kept high beam on continuously. About 77% of truck drivers dipped for oncoming traffic. | C (NGO, not peer-reviewed) | ArriveSAFE, as reported by 91trucks. Primary report to find. |
| Hyderabad reporting describes aftermarket LED headlamps becoming a trend, including on some municipal tippers. Karnataka and Gujarat ran state drives against "dazzling" LED retrofits in 2025–26. | D | Hans India; Deccan Herald; Ahmedabad Mirror |

**How the engine uses it**
1. **Immersive ride (night mode):** an oncoming high beam fills the view. The scene then stays dimmer for a recovery window that scales with how bright the light was and how long it lasted. Edge objects (a pedestrian, a parked truck, a pothole) reappear last. The caption cites the field study. It never claims a fixed number of seconds as a measurement.
2. **Field kit (planned, candidate only):** night photos and phone light-sensor spikes can flag "glare events" per stretch. They stay candidates until a second pass and a photo confirm them. They are aggregate only: no plates, and no vehicle is ever identifiable.
3. **Design side:** stretches without median screens or street lighting force high beam. The record shows lighting and median condition beside glare events, so the stretch is not blamed on drivers alone.
4. **Public wording:** "night crashes" and "glare" stay separate claims. The official data does not link them, so arcroad never says glare caused a number of crashes.

### Pedestrians and signals (future layer, and the immersive ride)

| Finding | Grade | Source |
|---|---|---|
| About 45% of pedestrians who arrive during the red phase cross against it, mostly in the second half of the red. | A | Kumar & Ghosh, *Safety Science* 2021, 12 signalised intersections, doi:10.1016/j.ssci.2021.105604. |
| Across 55 Kolkata junctions, junctions with a higher share of pedestrians crossing on red also have more fatal pedestrian crashes. | A | *Safety Science* 124:104610 (2020). |
| Longer red phases are linked to more violations. In 2,360 observed pedestrians, about 29% were distracted, and those texting were more likely to violate. | A | Raoniar & Maurya (IIT Guwahati), EASTS 2022 and *Transportation Letters* 2024. |
| Where a foot overbridge stands next to an at-grade crossing, only about a quarter of pedestrians used it. Use depends on how the time compares, not on attitude. | A | Mumbai video survey of 1,134 pedestrians (Patra et al.). |
| Design crossing speeds under mixed traffic are about 1.12 m/s for adults and 0.95 m/s for older pedestrians. | A | Marisamynathan & Perumal, *J. Traffic Transp. Eng.* 2014, doi:10.1016/S2095-7564(15)30094-5. |

**Engine lesson:** a lot of "civic sense" failure is a response to the design. Long waits, missing gaps and badly placed overbridges produce the violation. The engine records the design condition beside the behaviour, so a stretch is never blamed on its users alone. This is the same principle as arcroad's detour score.

### Safety-gear compliance (context only; we do not observe it)

| Finding | Grade | Source |
|---|---|---|
| About 9 in 10 people do not use the rear seatbelt. Under 3 in 10 knew it is mandatory. | C | SaveLIFE Foundation and Nissan, MDRA, 11 cities, 6,306 interviews (2018). |
| Seatbelt violations at observed Delhi and Mumbai sections roughly halved after the higher fines of 2019. | A-/B (observational, NGO) | SaveLIFE Foundation, MV Amendment Act 2019 study. |
| In 2023, 16,025 people killed were not wearing seatbelts. Two-wheeler riders were 44.8% of deaths and pedestrians 20.4%. | B | MoRTH 2023. |

**Engine lesson:** enforcement that people can see changes behaviour fast. Behaviour is not fixed by "culture". It responds to design and enforcement, which is what arcroad can show.

### Horns and noise (possible layer, from the phone microphone; off by default)

- **Grade D:** reporting (NPR, Sep 2025) quotes ambient noise in Mumbai above 80 dB and aftermarket horns near 120 dB.
- **Grade D:** a Bengaluru "honking" study (2016) has a commercial method that was not disclosed. It is not usable.
- **Grade A, to read:** an SPA Bhopal thesis on driver behaviour and traffic noise in Aizawl.
- The microphone stays off in the field kit (privacy). If a noise layer is ever added, it records dB levels only, never audio.

### Surveys about attitudes (grade C, internal only)

LocalCircles, Cars24 and the Ford "Cartesy" surveys are opt-in or sponsored. They show attitudes (for example, that rules feel optional unless enforcement is visible). They are not rates. CAG Chennai's Jan 2025 Tamil Nadu perception survey (12 districts) is more careful and is worth reading for its method.

### Rules for using this evidence

1. Never compare our rate with a study's rate unless the site type and the definition match (for example, red-phase arrivals at signalised crossings).
2. Never say anything about a group of people, community, faith, region or gender. Several surveys break results down this way. We do not carry those breakdowns.
3. Recheck every figure against the primary report before it reaches the public site. MoRTH figures are police-reported. WHO estimates are higher (to verify from the WHO Global Status Report on Road Safety 2023), so we say "police-recorded".
4. Opinion pieces about Indian "civic sense" are not evidence and are not cited.

## Official data to map against (licence check before ingest)

- **Works and diversions:** corporation (GHMC/CMC/MMC) e-procurement works orders, Hyderabad Traffic Police diversion advisories, HMRL works notices, NHAI project status and NH concession maintenance duties.
- **Road ownership:** NHAI (national highways), HMDA/IRB Golconda (ORR), corporations (city roads).
- **Encroachment policy:** the Supreme Court orders in SLP (C) 8519/2006 (primary: main.sci.gov.in/judgment/judis/35617.pdf) and Telangana's compliance policy or GO under it (to find and verify).
- **Trees:** Telangana's Water, Land and Trees Act 2002 and the corporation's tree-felling permission process (to verify).

## Status (1 Nov 2026)

- Layers 2 to 4 are built in `fieldkit` with tests. Layers 5 and 6 are designed here. Their sources still need checking, and nothing in them is published before that.
- The first real data is today's field day (8 spots). It is scored with the thresholds above and not adjusted afterwards.
