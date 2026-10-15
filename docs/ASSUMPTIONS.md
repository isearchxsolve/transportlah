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
| Boarding radius | H01 default 50m with strong-evidence device accuracy at most50m | Evaluator implementation and field calibration pending; no proximity-only passenger claim. |
| Route corridor width | H01 default150m; native geography and real149/151m boundary checks implemented | Genuine geometry/evaluator calibration remains pending; chord paths cannot silently confer full corridor credit. |
| Time windows | Boarding context, capture age, and position observation time must be distinct | Architecture +/-3 minutes, pilot 30s, and seed default 60s are not interchangeable concepts. No current vehicle-position observation timestamp is inferred from ETA. |
| Speed handling | No 12-65 km/h classifier implemented | Overlap with other travel modes and bus stops/congestion makes speed alone insufficient. H01. |
| Confidence classes | Spec boundaries80/60/40 implemented in pure policy | Fixed weights, zero unavailable credit, required-evidence cap79 and hard validity gates resolved; real factor evaluators/field calibration remain pending. |
| Sampling cadence | Spec phase-aware sampling during active rides only | Platform, battery, GPS-loss, and physical-device behavior pending; no always-on tracking enabled. |
| Raw-trace retention | H01 default48h; flagged exception requires reason/access restrictions/explicit expiry/review | U06 deletion implementation and client privacy confirmation remain pending. No real commuter traces collected. |
| Rail evidence | Separate station/transfer/tunnel/duration adapter required | H01 contract resolved; adapter/field validation pending. Verified rail settlement is refused and rail points remain zero. |
| Reward economics | Version1 busbase10/probable50%/grossdaily100, Singapore date | Provisional engineering defaults enforced transactionally; client economics confirmation pending. Reversals do not reopen the gross cap. |
| Fare/CO2 factors | Versioned, source-attributed estimates | Not implemented; current authoritative references required when these modules start. |

Do not silently replace assumptions with claimed empirical facts. A configured value and a passing local test are not field calibration.
