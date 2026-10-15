# Verification contract: tl-bus-policy-1

Engineering resolution of H01, 2026-10-15. Implemented in `backend/app/verification.py`; generated policy cases live in `backend/tests/test_verification.py`. This is a deterministic evidence policy, not a calibrated probability of passenger presence. The ingestion API continues to advertise `verification_enabled=false` until the server evidence evaluators and genuine ride validation exist.

## Seven factors and evaluator boundary

Every factor must be present with a typed state: `passed`, `failed`, or `unavailable`. Only passed factors earn a Decimal value in (0,1]. Failed and unavailable values are zero. An evaluator must record its reason, evidence IDs, catalog version, tolerances, and quality checks. Clients supply observations, never factor values, evidence tiers, attestation booleans, or final scores.

| Factor | Weight | Required inputs and interpretation |
| --- | ---: | --- |
| Boarding | 15 | Active-ride start, accurate device fixes near the selected boarding-stop occurrence. Use accuracy and elapsed time; proximity alone does not prove boarding. |
| Service | 10 | Official, versioned service/direction/stop sequence. Selected service must serve both occurrences in that direction. |
| Transit context | 20 | Recent, service-specific monitored arrival context with independently recorded capture freshness. Arrival ETA supports timing plausibility. Schedule-only, historical, absent, or stale context is unavailable for Tier 2. Vehicle-position matching additionally requires a documented position observation time. |
| Progression | 25 | Multiple distinct ordered observations spanning downstream route-stop occurrences and positive elapsed time. A nearest-line fraction alone cannot resolve loops, repeated stops, parallel services, or detours. |
| Speed | 10 | Accuracy-aware distance/time and motion consistency. Stops/congestion are allowed. Bus and car speeds overlap; the historical 12–65 km/h range is never sufficient mode proof. |
| Corridor | 10 | Metre-based distances to authoritative route geometry, accuracy/coverage checks, and explicit ambiguity handling. A straight line between stops is weaker geometry and cannot silently confer full corridor proof. |
| Alighting | 10 | Downstream endpoint occurrence, plausible duration, ride completion and cessation of active capture. |

The pure scoring core consumes evaluated factors; the seven real observation evaluators are subsequent implementation tasks. `SERVER_VALIDATED` is an internal service assertion, not an accepted client string. `TEST_VECTOR` marks generated mathematical/security inputs. That marker propagates through the decision, and production settlement rejects it.

## Validity, missing evidence and score

The denominator is always 100. No reweighting occurs when data is missing. Raw score is the sum of the seven fixed weights times their measurements. Invalid lifecycle, fewer than two distinct pings, zero/nonfinite elapsed duration, or contradicted boarding/service/progression/corridor/alighting produces a rejected decision with effective score zero. Two pings are a minimum validity gate, not sufficient route validation.

Tier 1 requires passed boarding, service and progression. Tier 2 additionally requires corridor, alighting and transit context. If stronger required evidence is unavailable, a raw score of 80 or above is capped at 79. Explanations preserve both raw/effective score and missing-factor reasons. Scores truncate to two decimal places, so 79.995 cannot round up into verified.

| Effective score | Class | Points policy | Public ranking |
| --- | --- | --- | --- |
| 80–100 | verified, requiring Tier 2+ | 100% of configured base | Eligible, subject to privacy/period rules |
| 60–79.99 | probable | 50% when Tier 1+ | Excluded |
| 40–59.99 | low confidence | 0 | Excluded |
| Below 40 or invalid lifecycle | rejected | 0 | Excluded |

The 50% probable award is an engineering default needing client commercial confirmation. The database currently uses a provisional bus base of 10 points and gross daily cap of 100 per user/tenant on the Singapore date. Capped or rejected outcomes have explicit zero-value ledger entries; a previous reversal does not reopen the daily gross cap. Changes require a versioned policy/migration, not a retrospective rewrite.

## Tier and contest policy

- Tier 0: manual or insufficient evidence; personal statistics only, no points from this policy.
- Tier 1: basic route evidence; probable partial rewards at most.
- Tier 2: route, lifecycle and recent transit context; verified eligibility remains a model-based plausibility decision, not proof of a fare transaction or boarding a named vehicle.
- Tier 3: verified Tier 2 plus both independently verified device integrity and a fresh, ride/device-bound trusted QR/NFC boarding proof. Device integrity alone cannot establish boarding. QR/NFC issuer keys, expiry, nonce consumption and binding must be implemented before use.
- Tier 4: future authoritative fare/partner transaction; unavailable in the current implementation.

Each contest specifies allowed modes and required tier (2 or 3). High-value contests require Tier 3 and fraud review; defaults must not admit unsupported proof. Generated cases can qualify only in explicitly marked test environments. Contest registration, attestation verification and replay-resistant QR/NFC issuance are not implemented by the pure eligibility function.

## Bus, rail and thresholds

The three NextBus slots remain independent observations. Neither ETA nor capture time is a position measurement time. No same-vehicle trajectory is manufactured by joining slots or successive responses. Route/arrival agreement cannot reliably exclude a car following a bus route; explain that uncertainty and field-test it.

Rail needs station occurrences, ordered entry/exit/transfer evidence, duration bounds, tunnel/GPS-loss handling and a separately validated transit-context adapter. Train alerts/crowd data do not establish an individual journey. The scoring core caps rail below verified unless that internal adapter is validated; database settlement currently refuses verified rail decisions and awards zero rail points. Mixed-mode rides require leg-specific evaluation; a bus leg cannot validate a rail leg.

Initial configurable evaluator assumptions: boarding radius 50 m; corridor 150 m; arrival context ±180 s, with captured context no older than 30 s; observed-position matching ±30 s; device accuracy at most 50 m for strong proximity evidence. These are initial engineering choices, not calibrated acceptance thresholds. Distinguish uncertainty from contradiction: missing coverage is unavailable; authoritative contrary direction/service is failed. GPS jitter alone must not become a hard contradiction.

Raw trace default is 48 hours after ride completion, within the documented retention ranges. Flagged review extends retention only with an explicit reason, restricted access, expiry date and periodic review. Retention execution is still U06. Never collect outside an active, consenting ride.

## Acceptance evidence still required

Generated tests establish policy consistency, boundary behavior, missing-data conservatism and proof-tier separation. They establish no transit accuracy. Consented Singapore bus traces with boarding/alighting annotations and matching current LTA captures must exercise genuine positives, pedestrians, car/parallel-route cases, GPS gaps, replay, wrong direction and stale/schedule-only feeds. Evaluate rail independently before enabling it. Record observed outcomes and sample limitations rather than asserting an anti-spoofing or accuracy percentage from unit tests.
