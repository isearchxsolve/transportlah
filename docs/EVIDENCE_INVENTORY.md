# Evidence and dependency inventory

Updated: 2026-10-15 (Asia/Calcutta). Completes B06/B08 within the explicitly searched scope; absence outside that scope is not claimed.

## Available historical evidence

- Original file: `D:/anonym/deliverables/evidence/lta_live_capture.json`.
- Unchanged replay copy: `backend/tests/data/lta_stop44009_service190_20261010.json`.
- File SHA-256: `5e73dfaf56515f05b8648a0dce335dcd454ed65732810780c94b527b8427d21e`.
- Stored raw payload SHA-256: `b4f78f86b4a7025005cd90be2974678e43aa06ecbe6be493798a2244454778e9`; recomputed using the original sorted-key JSON hashing convention and matched.
- Recorded capture time: `2026-10-10T21:42:59.758498+00:00`.
- Scope: stop `44009`, service `190`, three separate approaching-bus entries.
- Quality: each has `Monitored=0`, `Latitude=0.0`, `Longitude=0.0`. No usable vehicle coordinates are present.
- Provenance boundary: historical document labels its source LIVE_NETWORK. Integrity is checked; a new authenticated handshake and independent proof of the original collection are not supplied by this planning/implementation pass. Treat it as historical replay, not a current live receipt.

## Unchanged seed/master evidence

`docs/SEED_MANIFEST.json` inventories nine original seed/text files and their byte-identical archives in `reference/seed`. `tools/verify_seed.py` checks archival hashes and available originals.

The original master test hash remains `621efc6540f0e3815c0428be92e43ad9788e82a437e418a2187af3c1c09f1834`. Its eight tests were executed unchanged and passed. Their original hard-coded vectors and known false-pass cases are historical regression inputs, not authentic device recordings.

## Current dependency status

| Dependency | Observation | Consequence |
| --- | --- | --- |
| LTA key environment | `LTA_DATAMALL_KEY` and `LTA_KEY_PATH` were not set when inventoried | Current authenticated live handshake remains unperformed. The implementation fails explicitly without a key. |
| Key/capture file inventory | Relevant filename search across D:/anonym found the seed proxy and the historical capture; no configured current key was identified. Vault filename filter for LTA/DataMall returned none. | Do not claim the user's account has no key; only current configuration/identified files are absent. No personal mailbox/password extraction was performed. |
| Genuine multi-stop captures | One scoped historical capture identified | M1 live multi-stop acceptance remains pending. Unknown stops fail without fabricated fallback. |
| Singapore device GPX | No GPX found in the searched deliverables/war-log roots | Device evidence remains unavailable within that scope; do not invent it. |
| Docker | No executable locally; actual CI service containers executed | PostGIS16/PostGIS3.5.2 and Redis7.4 cloud integration passed. Product Compose/image build still pending. |
| Flutter | No executable found locally | No mobile scaffold/build acceptance claimed. Cloud/client implementation pending. |
| Apple/Google signing | Account availability not inspected | Unknown, not assumed absent. |
| Git/CI | Private isearchxsolve/transportlah, branch codex/transportlah-foundation; High source e25420c5351529fb019b8b2b4675847b27730de6 | CI run38662867180 passed57 tests with zero skips and actual readiness. Downloaded artifact/source blob hashes verified. |
| Private runner allowance | Billing/usage endpoints unreadable with available scopes | Authorized implementation CI now executed; no extra account scopes requested. No claim about remaining account allowance. |

## Evidence that remains required

- A current real LTA key handshake and multiple real stop/service captures.
- Official stop/service/route records and geometry provenance.
- Consented real bus and rail recordings, including ambiguous/negative field cases where obtainable.
- Genuine-corpus workload measurements, recovery and operational execution. Generated PostGIS query plans and backend cloud CI are now available; they do not satisfy genuine workload/device accuracy acceptance.
- Signed mobile builds, installation, background-location behavior, and field results on physical devices.
- Written client acceptance against the reconciled full scope.
