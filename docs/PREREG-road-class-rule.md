# Amendment: places on motorways are out of scope

Written 8 Nov 2026 at 13:30 IST, after every result up to 7 Nov had been published. It is a declared method change: stated here, applied to every city and every drive on file, and the change it makes is published.

**What was wrong.** The place selection kept any arterial road, motorways included. On a motorway, an access-controlled expressway such as Hyderabad's Outer Ring Road, nobody is meant to cross or turn round: the long way, through an interchange, is the design. A long detour there is a property of the road type, not a gap that a resident could ask to have fixed. The site already said so in two places (the cost page left the Outer Ring Road pass out, and the field page listed it as a limit), but the counts still included it. The 7 Nov Bengaluru checks made the problem plain: four of the eight places picked there were on motorways.

**The rule now.** A place whose either side lies on a road OpenStreetMap tags `highway=motorway` or `motorway_link` is left out of the sample, the counts, the globe, the drive page and the letters kit. The road class is read from OpenStreetMap by the openings check (`research/runner/app/openings.py`). Driven results at such places are kept on the field page for the record, under a separate heading, and are not counted. Nothing else changes: the match tolerance, the counting rules, verdicts and evidence levels are as before.

**Effect, re-applied to every drive and city on file.**
- Hyderabad: S23 and S24, both on the Outer Ring Road, leave the sample, which goes from 24 places to 22. S24's two driven directions (1 Nov) leave the count: "10 of 10 directions matched" becomes "8 of 8", and places driven go from 7 to 6. The longest drive on file is no longer 11.6 km (S24) but 2.3 km (S16).
- Bengaluru (private, not published): B01, B03, B04 and B06 leave the candidate list and are replaced from the same ranked list under the same selection, with motorways skipped.
- The 1 Nov field sample is not redrawn. Redrawing after seeing the results would be a worse change than this one; the sample stays as drawn, minus two places.

**Competing explanation, and what would settle it (rule 5).** One could argue a motorway detour still costs people time, so it belongs in the count. It does cost time, but a finding is only useful if it points to something an authority could change, and on an expressway the remedy is a new interchange, a different kind of claim from a missing median opening. If motorway places are wanted later, they will be measured as their own group with their own question, not mixed into this one. Removing two matching passes makes the headline smaller, not larger, which is the direction rule 4 asks to be careful about least.
