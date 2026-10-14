# Immutable historical seed

`seed/` contains byte-preserved copies of the original demo, master tests, and schema/configuration. `docs/SEED_MANIFEST.json` records their hashes. `tools/verify_seed.py` checks both archive copies and originals when available.

These artifacts retain their original hard-coded test vectors and known pedestrian/replay passes. Passing the historical eight-test suite is a regression receipt, not proof of real passenger verification. Corrected product code lives in `backend/`, and these reference files must not be edited to make tests pass.
