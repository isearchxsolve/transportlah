# Configuration and assumption register

Updated: 2026-10-15 (Asia/Calcutta). Completes B04 as a documentation task, not field validation.

| Parameter / rule | Current handling | Basis / status |
| --- | --- | --- |
| Cache TTL | Configurable; default 30 seconds | Engineering default from the earlier proposal; not a guarantee of upstream freshness. |
| Per-stop polling interval | Configurable; live minimum/default 20 seconds | Official guide's documented refresh cadence. This is not an authenticated account-wide rate entitlement. All service scopes for one stop share the budget. |
| Request timeout | Configurable; default 10 seconds | Engineering default; validate against the actual upstream and deployment. |
| Stop/cache capacity | Configurable; defaults 128 stops and 512 cached request scopes | Engineering resource bounds, not tested load capacity or contractual limits. |
| Upstream payload size | Hard bound 2 MiB | Engineering protection; no claim about the largest legitimate response until live multi-stop capture is verified. |
| Process coordination | One worker/process | Local cache and budgets are not shared. Redis rate/cache coordination is pending. |
| Boarding radius | Historical architecture proposed 50m; not implemented | Field calibration and GPS-accuracy treatment parked in H01. |
| Route corridor width | Original spec 100-200m; architecture 150m; seed/pilot 100m | These are assumptions/settings from different sources. Definitive rule and geometry are parked in H01/H02. |
| Time windows | Boarding context, capture age, and position observation time must be distinct | Architecture +/-3 minutes, pilot 30s, and seed default 60s are not interchangeable concepts. No current vehicle-position observation timestamp is inferred from ETA. |
| Speed handling | No 12-65 km/h classifier implemented | Overlap with other travel modes and bus stops/congestion makes speed alone insufficient. H01. |
| Confidence classes | Spec boundaries 80/60/40 retained as requirements | Factor evaluation, missing-evidence handling, hard validity gates, and evidence tiers are unresolved in H01. |
| Sampling cadence | Spec phase-aware sampling during active rides only | Platform, battery, GPS-loss, and physical-device behavior pending; no always-on tracking enabled. |
| Raw-trace retention | Original 24-72h plus flagged-review exception recorded | Definitive retention/deletion policy unresolved; no commuter raw traces collected by this implementation. |
| Rail evidence | Separate from bus arrival context | H01 design pending; alerts/crowd context cannot be promoted to passenger evidence. |
| Fare/CO2 factors | Versioned, source-attributed estimates | Not implemented; current authoritative references required when these modules start. |

Do not silently replace assumptions with claimed empirical facts. A configured value and a passing local test are not field calibration.
