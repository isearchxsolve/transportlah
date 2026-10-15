# Versioned catalog importer

Implementation batch after the High pass, 2026-10-15. Code: `backend/app/catalog.py`, migration002, `tools/import_catalog.py`. I05 remains open until a real company-key capture/import and consistency review are executed.

The [official DataMall guide](https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf) specifies BusStops, BusServices and BusRoutes endpoints, pages of at most500 and the `$skip` offset. Stop coordinates and service/direction/stop sequence are normalized; route Distance stays kilometres. Boarding/arrival VisitNumber is not an extra route field; repeated stops are represented by distinct sequence occurrences.

The client uses only fixed HTTPS endpoints, not feed-supplied next-link URLs. Each response is bounded2MiB; total64MiB; at most500pages/dataset and a15minute capture window. Reject malformed, repeated, missing, duplicate, hash-mismatched or referentially inconsistent records; an upstream error fails clearly without fallback. There is no automatic429 retry storm. Request bounds are engineering protections, not an account quota agreement.

Store original page payload/hash/capture time and root start/completion/provenance. The root canonical JSON digest identifies an immutable snapshot; exact replay imports once. New versions never overwrite historical stop coordinates. Each route occurrence references the matching versioned service/stop; stop chords are weak geometry. Generated cases produce TEST_VECTOR paths. Degenerate/single-stop routes preserve raw occurrences but have no manufactured usable line.

Run a real capture using a private configured LTA key:

```powershell
.\.venv\Scripts\python.exe tools/import_catalog.py
```

Output goes under ignored private/catalog. Apply migrations with the tool-only MIGRATION_DATABASE_URL, then import the preserved capture:

```powershell
.\.venv\Scripts\python.exe tools/migrate.py
.\.venv\Scripts\python.exe tools/import_catalog.py --capture <preserved-capture.json> --write-database
```

Database import is transactional under an advisory lock; errors cannot leave a half-written new version. Catalog tables and route geometry reject update/delete. No active catalog is automatically promoted: sequential offset collection is not an atomic upstream snapshot and cannot prove absence of omissions during feed changes. Review completeness/consistency and live provenance before selecting a version for product use. TEST_VECTOR snapshots cannot be advertised as real catalog acceptance.

Current evidence: generated pagination/error/normalization tests and real cloud database import/retry/immutability checks. Real company key remains unconfigured; the live collector must fail without producing a fake capture. Provider/mobile endpoint integration remains separate.
