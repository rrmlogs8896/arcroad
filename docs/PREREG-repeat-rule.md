# Amendment: a repeat pass counts only in the same direction

Written 5 Nov 2026 at 10:00 IST, after the 4 Nov S12 result was published as "corroborated". It is a declared method change: stated here, applied to every drive on file, and the change it makes is published.

**What was wrong.** The 1 Nov triangulation rule (pipeline/fieldscore.py) gave a pass the kind R, a repeat, when the same place had been driven on another day *in either direction*. The two directions at a place are different routes: at S12, A to B is about 2.0 km and B to A about 1.0 km. Driving each once is two single measurements, not one measurement repeated. The 5 Nov devil's-advocate review raised this, and it was accepted as an honesty fix.

**The rule now.** R needs another pass at the same place, in the same direction, on another day or at least 30 minutes apart on the same day. Nothing else changes: thresholds, verdicts, evidence levels and the S and P kinds are as before.

**Effect, re-applied to every drive on file (1 to 4 Nov).** Only the two S12 rows change, from S+R corroborated to S candidate. S18 B to A stays S+P corroborated, because its second kind is a photo, not a repeat. The verdicts and the "9 of 9 directions matched" count do not change.

**Competing explanation, and what would settle it (rule 5).** One could argue both directions test the same model at the same place, so they do support each other. They test it on different routes, though, and a second drive of the same direction is the only thing that separates a real match from a lucky one. A second S12 drive in either direction will show it.
