# Aegean License Catalog

What AegeanWorks offers, what each license gives a user, and which one a project should carry.
The operative texts are the files beside this catalog; this page is the map, not a substitute.

| License | Free use | Redistribution | Commercial | AI training | DRM-free | Patent grant | OSI open source |
|---|---|---|---|---|---|---|---|
| **AL-1.0** — Aegean License 1.0 | One individual, private non-commercial use | No | ACL-1.0 + certificate | No | n/a | Yes, personal use only | No |
| **AGL-1.0** — Aegean Game License 1.0 | Personal play, streaming, modding, free mods | Free mods only | ACL-1.0 + certificate + asset grant | No | **Yes, contractual covenant** | Yes, for AGL uses | No |
| **ASL-1.0** — Aegean Science License 1.0 | Non-commercial research, teaching, publication, reproducibility | Published research modifications | ACL-1.0 + certificate + data/weights grant | Non-commercial research only | n/a | Yes, for ASL uses | No |
| **ACL-1.0** — Aegean Commercial License 1.0 | 28-day non-production evaluation, once per company group | Within a product, per certificate | Paid, scoped by certificate | Only with `ai-training` Allowance | Per agreement | Yes | No |
| **Restricted notice** | Nobody | No | Separate written agreement | No | n/a | No | No |

"OSI open source" means the Open Source Initiative's Definition, which forbids restricting a field
of endeavour (including commercial use). AL-1.0, AGL-1.0 and ASL-1.0 restrict commercial use, so
they are **source-available**, not open source. The catalog never calls them open source.

## Which one should a project use?

- **Software, tools, libraries, apps** → AL-1.0 (AIKit's default). Commercial users buy ACL-1.0.
- **Games, interactive fiction, engines, level packs** → AGL-1.0. It adds the DRM-free covenant,
  streaming/recording permission, private servers, modding, and an explicit asset boundary.
- **Research code, notebooks, simulations, benchmarks** → ASL-1.0. It adds publication,
  reproducibility sharing, non-commercial text/data mining and non-commercial ML training.
- **Datasets and model weights** → a project may list them under ASL-1.0 when it owns them; a
  separate data/weights grant is still needed for commercial use. Third-party data keeps its own
  license.
- **Anything valuable enough that public distribution is the risk** → the restricted tier, not a
  public license. It is a forward-only cutoff; earlier releases are not revoked.

A project that mixes domains should choose the license of its **primary deliverable**. A game
engine with a research paper uses AGL-1.0 for the game and can publish the paper's code under
ASL-1.0 separately. Never stack two LICENSE files in one repository: one project, one tier.

## What every license keeps

- **No AI training** outside the science grant or an `ai-training` Allowance.
- **No trademarks**: names, logos and project marks are not licensed.
- **No warranty or support**: pure copyright grants, AS IS, no SLA.
- **No sublicensing or standalone resale.**
- **Forward-only restriction**: a later version may be All Rights Reserved; a copy already
  granted keeps its grant.
- **Assets are separate**: code and logic are licensed; art, audio, datasets and model weights need
  a grant under [ASSET_POLICY.md](https://github.com/AegeanWorks/aegean-licensing/blob/main/licenses/ASSET_POLICY.md)
  or an explicit asset manifest.
- **Contributions** need the [AegeanWorks CLA](https://github.com/AegeanWorks/aegean-licensing/blob/main/licenses/CONTRIBUTING_CLA.md)
  so the licensor can relicense them.

## Strengths

- **One base, three domains.** AL-1.0 is the base; AGL-1.0 and ASL-1.0 add only the clauses their
  domain needs, so the family stays coherent and reviewable.
- **A real commercial path.** Every free tier points to ACL-1.0 and a certificate in the public
  register; the certificate is scoped, time-limited and verifiable offline.
- **A patent grant.** All three free tiers grant patent claims the licensor can license, with a
  patent-defense termination. This is what CC BY-NC lacks and why CC itself recommends against CC
  for software.
- **A DRM-free covenant.** AGL-1.0 is not just "we happen not to ship DRM": it promises no
  mandatory client, account binding or activation, forbids a distributor adding DRM, and keeps an
  offline build playable after online services end. This is close to GOG's DRM-free promise, but
  written as a license condition.
- **A science-specific grant.** ASL-1.0 permits publication, reproducibility packages and
  non-commercial ML training without pretending the material is open source or unrestricted.
- **Asset and data boundaries.** The license says what is code, what is an asset/dataset, and what
  needs a separate grant, instead of silently licensing a creator's art with the code.
- **Machine-readable analysis.** AIKit reads project markers, reports confidence and evidence,
  and can apply a high-confidence choice before publishing. Tags and license are chosen from the
  project, not guessed from its name.

## Weaknesses and risks

- **Non-commercial is fact-specific.** "Primarily intended for commercial advantage" is the
  Creative Commons formulation; a court applies it to the facts. A funded academic project, a
  startup evaluating a product, or a monetized channel can all be argued either way. The text
  states examples, but it cannot remove the uncertainty.
- **Custom licenses have adoption friction.** SPDX has no official identifier, so tools see
  `LicenseRef-AL-1.0`, `LicenseRef-AGL-1.0` or `LicenseRef-ASL-1.0` and cannot map them to a known
  policy. That is valid SPDX, but it needs the license text beside the code.
- **A license binds recipients, not the world.** A platform, a search index or a person who never
  accepts the terms is not automatically bound. The restricted tier and the register are the
  practical enforcement layers.
- **DRM-free is a promise about builds, not platforms.** A storefront can still require an account
  to download; a console can still impose its own measures. AGL-1.0 says so instead of overpromising.
- **Anti-cheat and multiplayer need judgment.** The carve-out protects legitimate multiplayer
  integrity, but a court or a platform may read "anti-consumer" differently. The clause is written
  to distinguish single-player rights from cheating enforcement.
- **Assets and data are not covered by ACL-1.0.** Commercial use of art, audio, datasets or model
  weights needs a separate grant. Until that grant exists, a commercial certificate covers code
  only.
- **No use-restriction list like OpenRAIL.** ASL-1.0 has a short lawful/ethical clause, not the
  OpenRAIL attachment of prohibited uses. A project that needs a RAIL-style list for model weights
  should add an OpenRAIL-M/D attachment; ASL-1.0 alone is not one.
- **No security, support or update commitment.** The licenses say AS IS. A paid customer may expect
  an SLA; that belongs in the Order Form, not the license.
- **No legal review yet.** These are drafts until counsel reviews them. The counsel note in each
  text is deliberate, not boilerplate.

## How this compares with common licenses

- **Creative Commons BY-NC 4.0** is the reference for a non-commercial grant, and its definition of
  "commercial" informs AGL-1.0 and ASL-1.0. CC itself recommends against using CC licenses for
  software because they do not address source distribution or patents. ASL-1.0 keeps CC's
  non-commercial idea and adds a patent grant, source terms and a data boundary.
- **PolyForm Noncommercial 1.0.0** is the closest standard source-available non-commercial
  software license. It grants use, changes, distribution and a patent license for non-commercial
  purposes. AL-1.0 is stricter (no distribution at all); AGL-1.0 and ASL-1.0 are closer to
  PolyForm in spirit but add domain rights. PolyForm's patent-defense and 32-day cure language is
  a good model; AL-1.0 uses a 30-day cure and the same patent-defense idea.
- **OpenRAIL-M / OpenRAIL-D** add a list of prohibited uses and require the restrictions to travel
  with derivatives. They are a better fit for model weights or sensitive datasets than a general
  research license. ASL-1.0 has a short lawful/ethical clause, not the full RAIL attachment.
- **BSL 1.1, Elastic License 2.0 and SSPL** are source-available licenses that restrict competing
  or hosted use and, for BSL, convert to open source after a change date. AL-1.0 is simpler and
  stricter; ACL-1.0 is the paid path instead of a delayed open-source conversion.
- **MIT, Apache-2.0, GPL and AGPL** permit commercial use and therefore fail the "personal use
  only" goal. Apache-2.0's patent grant is the model for AGL-1.0 and ASL-1.0; its trademark and
  notice clauses are the model for AL-1.0's notice rules.
- **GOG's DRM-free model** is a distribution promise (offline installers, no client required,
  access after a store shutdown), not a license. AGL-1.0 turns the same promise into a condition
  on the licensor and on anyone who distributes a permitted mod or patch.

## What is still missing

1. **Trademark and brand policy** (currently one paragraph inside AL-1.0).
2. **A data/model-weights license** for ASL projects that ship datasets or trained weights.
3. **A game asset-pack license** for art/audio sold separately from AGL-1.0 code.
4. **A security disclosure policy** and a **support/update policy** per tier.
5. **Counsel review** of AL-1.0, AGL-1.0 and ASL-1.0 before the first paid issuance.
6. **An optional OpenRAIL attachment** for model weights or datasets that need a prohibited-use
   list.
7. **A contribution and provenance policy** for third-party assets and data, not only code.

## Verification

Every commercial certificate is checked against the public register
([`licenses/issued.json`](https://github.com/AegeanWorks/aegean-licensing/blob/main/licenses/issued.json)).
The digest proves the record was not altered; only AegeanWorks' private signing key proves
authenticity. Personal-use licenses (AL, AGL, ASL) need no certificate. Commercial use always does.

Contact: `aegean-licensing@proton.me`
