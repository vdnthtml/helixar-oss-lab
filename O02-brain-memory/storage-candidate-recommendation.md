# O02 storage candidate inspection and bounded smoke-fixture recommendation

Date: 2026-07-14  
Scope: architecture/source inspection only for PostgreSQL+pgvector, Qdrant, and MinIO. This note does not authorize production adoption.

## Executive recommendation

Use **PostgreSQL + pgvector as the default bounded operational/vector-store candidate** and keep a **content-addressed S3-compatible object-store port** above the provider. Run one app-level PostgreSQL+pgvector+MinIO compatibility fixture only as protocol and failure-semantics evidence. Do **not** select MinIO as the production object-store implementation from this lab: the inspected community repository says it is no longer maintained, is source-only, and is AGPL-3.0. Do not add Qdrant until measured corpus size, query latency, recall, or filtering requirements show that PostgreSQL exact/HNSW search is insufficient.

The proposed combination is an application-level split, not a native pgvector–MinIO integration:

- PostgreSQL owns tenant-scoped metadata, governance state, lineage pointers, idempotency, revocation/tombstones, audit events, and vectors.
- MinIO is exercised only behind an S3-compatible content-addressed blob port for immutable synthetic source bytes and exports.
- The application owns the outbox/reconciliation boundary; neither storage tool may promote a memory to global/current truth.

Strategic tag: `SHARED PLATFORM`.

## Source-bound candidate dispositions

| Candidate | Inspected source | Exact inspected commit/tree | License proof | Source-level architecture fit | Proof ladder at this point | Disposition |
|---|---|---|---|---|---|---|
| PostgreSQL+pgvector | `https://github.com/pgvector/pgvector.git` | commit `a6420355c5d1c08f4c5fbd5112fc17e4cf3b5eb5`; tree `52b7f4807f58d7ae61990ba5c95f26755e66d65a` | `LICENSE` SHA-256 `6bba9ebeb73e27477463b05e5ef1bf303bccbddb3db9bbc95905d351604d6a87`; PostgreSQL-style | Best default for a bounded corpus because metadata, governance state, vector data, and idempotent state transitions can share one ACID database. README supports exact search, HNSW/IVFFlat, CRUD, hybrid search, and explicit multitenancy guidance. Start with exact search; ANN adds recall/filtering complexity. PostgreSQL server provenance still must be pinned separately before a runtime PASS. | source inspected = yes; install attempted = no; service started = no; deterministic fixture passed = no; integration fit = proposed from source; production suitability = unknown | `ADAPT` |
| Qdrant | `https://github.com/qdrant/qdrant.git` | commit `44ad62f8cd69642be5afa6441612525e24a0d063`; tree `c6b12563a75f1c5ee866e763be8ad93ebc51e5a8` | Apache-2.0 `LICENSE` SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` | Strong dedicated vector-service candidate: payload filtering, dense/sparse/multivector search, WAL, snapshots, sharding/replication, REST/gRPC. It introduces a second authority and dual-write/reconciliation problem if PostgreSQL remains operational truth. Source defaults are not acceptable for this lab: base config binds `0.0.0.0`, enables CORS, has no API key, allows remote snapshot URL recovery, and sends hourly telemetry unless disabled. A Python client/local adapter is not server deployment proof. | source inspected = yes; install attempted = no as an independent candidate; service started = no; deterministic fixture passed = no; integration fit = conditional; production suitability = unknown | `POC_MORE` |
| MinIO | `https://github.com/minio/minio.git` | commit `7aac2a2c5b7c882e68c1ce017d8256be2feea27f`; tree `376b09b793c57170a905208e64590164d8ab7a3b` | AGPL-3.0 `LICENSE` SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` | Useful only as an S3-protocol compatibility fixture from this evidence. The README says the repository is no longer maintained, community distribution is source-only, legacy binaries receive no updates, source builds require Go 1.24+, and proprietary/commercial use needs license review. It is not natively content-addressed; Helixar must calculate SHA-256 keys and treat ETag/version ID only as provider metadata. Versioned DELETE may create a delete marker rather than hard-delete bytes. | source inspected = yes; install attempted = no; service started = no; deterministic fixture passed = no; integration fit = protocol-only; production suitability = blocked/unknown | `REJECT_OPERATIONS` for production; code use also blocked pending AGPL counsel |

## Critical source findings

### PostgreSQL+pgvector

- `README.md:5-12`: vectors remain with relational data and inherit PostgreSQL ACID/PITR/JOIN capabilities.
- `README.md:124-128`: vector rows use ordinary SQL deletion.
- `README.md:197-205`: exact nearest-neighbor search is default; ANN is an explicit recall-for-speed trade.
- `README.md:424-472`: ANN filtering occurs after index scan, and tenant isolation should use list partitioning or separate tables. Therefore the first fixture must use exact search and explicit tenant predicates/partitions rather than claiming ANN tenant safety.
- `README.md:633-642`: PostgreSQL full-text and pgvector can support a later bounded hybrid-search path without adding a second vector authority.

### Qdrant

- `README.md:44-62`: the quick-start container is explicitly insecure and exposed; it cannot be copied into this lane.
- `config/config.yaml:262-305`: defaults bind `0.0.0.0`, enable CORS, expose REST/gRPC, and leave API keys unset.
- `config/config.yaml:333-338`: remote snapshot URL recovery is enabled by default and must be disabled in a bounded environment to reduce SSRF risk.
- `config/config.yaml:367-369`, `src/settings.rs:255-256,427-429`, and `src/common/telemetry_reporting.rs:14-85`: telemetry is enabled by default and POSTs anonymized data to `telemetry.qdrant.io` or staging immediately and then hourly. Any future run must set `telemetry_disabled: true` and `--disable-telemetry`, then verify no egress.
- `README.md:128-163`: the vector feature surface is stronger than the current bounded requirement, making Qdrant a scale/recall-triggered candidate rather than the default authority.
- No repository `SECURITY.md`, `.github/SECURITY.md`, or equivalent tracked security-policy file was found at the inspected commit. Apache-2.0 is proven by `LICENSE`; operational security still depends on explicit hardening.

### MinIO

- `README.md:1-7`: inspected community repository is no longer maintained.
- `README.md:26-39`: source is AGPL-3.0 and community distribution is source-only.
- `README.md:50-57`: legacy binaries are unmaintained.
- `README.md:59-94`: current source build requires Go 1.24+ and production source builds are at operator risk.
- `COMPLIANCE.md:1-7`: usage requires independent license review; the project does not determine compliance for applications.
- `internal/config/callhome/callhome.go:34-44,89-99`: callhome exists but is off by default. A fixture must still set the opt-out explicitly and verify egress denial.
- `cmd/server-main.go:61-73`, `cmd/globals.go:63-67`, `cmd/common-main.go:465-500,704-710`: API and console startup defaults are not loopback-scoped; the console is on by default and may select an all-interface random port.
- `internal/auth/credentials.go:88-100`, `cmd/server-main.go:808-829,997-1001`: absent supplied credentials, factory root credentials are used with a warning. A fixture must provide synthetic credentials and disable the console/root access surface it does not need.
- `cmd/common-main.go:942-945`: TLS is disabled when certificate files are absent. This is acceptable only inside the explicit loopback-only fixture boundary.
- `cmd/globals.go:204-205`, `cmd/server-main.go:854-862`, `cmd/common-main.go:297-330`: release update checks are a separate potential egress path from callhome and must be disabled explicitly.
- `docs/bucket/versioning/README.md:7,17-29`: versioning is off by default; when enabled, an ordinary delete can create a delete marker. Hard deletion therefore requires enumerating and deleting every version and then proving absence.
- `internal/etag/etag.go:18-75,125-135`: ETags are not reliable whole-content digests for encrypted, compressed, or multipart objects. PostgreSQL must retain the application-computed SHA-256 as authority.
- `README.md:1-7` conflicts with `SECURITY.md:3-6`: the README declares the community repository unmaintained while the security policy says fixes are supplied for the latest release. The unmaintained status prevents relying on the policy as a maintenance SLA for this commit.

## Current-host feasibility result

The 2026-07-14 live preflight found no `docker`, `podman`, `psql`, `postgres`, `pg_config`, `minio`, `mc`, `go`, `rustc`, or `cargo` executable on this macOS arm64 host. Candidate ports `5432`, `6333`, `6334`, `9000`, and `9001` were free. Therefore a real PostgreSQL+pgvector+MinIO service fixture is **not currently feasible without adding new runtime/toolchain dependencies**, and none was silently installed.

The existing PASS in `logs/048-llamaindex-qdrant-fixture-rerun-classvar.stdout.log` proves only LlamaIndex with embedded `qdrant-client` local persistence. It explicitly does not prove the Qdrant server, auth, TLS, replication, snapshots, or production operations and is not counted as `O02-STOR-FX-01`.

## Recommended one bounded combination fixture

Fixture ID: `O02-STOR-FX-01`  
Name: **Governed memory plus content-addressed source object**  
Stack under test: pinned PostgreSQL release + pinned pgvector release/commit + inspected MinIO source build, all in disposable directories and bound only to `127.0.0.1`.  
Purpose: prove the application contract across one relational/vector authority and one replaceable S3-compatible blob provider. It is not production-suitability evidence.

### Synthetic corpus

Use four tiny UTF-8 source objects (under 1 KiB each) with `.invalid` identities:

- two tenants: `tenant-a.invalid`, `tenant-b.invalid`;
- one proposed memory per tenant with similar vectors to detect tenant leakage;
- one duplicate same-key/same-digest write;
- one same-key/different-digest conflict;
- one revocation and one hard-deletion request.

Embedding vectors must be deterministic constants produced by the fixture, not a hosted or downloadable embedding model.

### Storage contract

PostgreSQL tables or equivalent bounded schema:

1. `source_object`: tenant, source ID, SHA-256, byte size, media type, S3 key, object version/etag, created time.
2. `memory_proposal`: tenant, proposal ID, source ID/digest, deterministic vector, proposed text, idempotency key, status.
3. `memory_current`: tenant, memory ID, approved proposal/version, vector, validity interval; only approved, non-revoked records appear here.
4. `memory_event`: append-only proposal/promotion/revocation/deletion/reload events with actor, policy, correlation ID, prior/new digest, and timestamp.
5. `storage_outbox`: pending object/metadata reconciliation actions so a failed MinIO or PostgreSQL operation cannot be silently treated as committed.

MinIO bucket and key rule:

- bucket: `o02-stor-fx-01`;
- key: `sha256/<first-two-hex>/<full-sha256>`;
- immutable object bytes plus only non-sensitive synthetic metadata;
- no memory authority state in object tags.

### Required execution sequence

1. **Preflight and isolation**
   - Pin the PostgreSQL server release/commit and license separately; do not count pgvector provenance as PostgreSQL provenance.
   - Build/start MinIO only if Go 1.24+ is present and legal review permits an ephemeral AGPL lab run. Do not use an unpinned legacy binary.
   - Bind PostgreSQL and MinIO to dedicated `127.0.0.1` ports; prove listeners with `lsof`.
   - Start MinIO with explicit loopback API and console addresses, disable the console if it is not required, supply synthetic non-default credentials, disable callhome and release-update checks, and run the first runtime attempt under an OS-level outbound-network deny boundary.
2. **Ingest as proposal, not truth**
   - PUT content-addressed object; verify returned digest/etag.
   - Insert `source_object`, `memory_proposal`, and outbox/event rows.
   - Query current retrieval and assert the proposal is absent.
3. **Explicit promotion**
   - Apply a synthetic human-approval fixture carrying actor, policy version, proposal digest, expiry, and correlation ID.
   - In one PostgreSQL transaction, insert the append-only approval/promotion event and project one `memory_current` row.
4. **Deterministic retrieval and tenant isolation**
   - Use exact pgvector cosine/L2 ordering, mandatory `tenant_id` filter, and `memory_id` as the final tie-break.
   - Run each query ten times and require identical ordered IDs and scores.
   - Query each tenant with the other tenant's near-identical vector and require zero cross-tenant IDs.
5. **Concurrency/idempotency**
   - Launch concurrent same-key/same-digest writes and require exactly one proposal/current identity with deterministic replay response.
   - Launch same-key/different-digest writes and require an explicit conflict; `INSERT OR IGNORE`/silent overwrite fails the fixture.
6. **Revocation**
   - Append revocation event and remove the row from `memory_current` in one transaction.
   - Require current retrieval to return nothing while audit history and source lineage remain queryable.
7. **Deletion semantics**
   - Execute the approved synthetic deletion policy: delete or tombstone all current/proposal vector projections and delete the blob key.
   - Require MinIO GET/HEAD to return not found, PostgreSQL current retrieval to return no item, and the append-only deletion receipt to retain only allowed non-content identifiers/digests.
8. **Export/reload**
   - Export PostgreSQL rows/events plus a manifest of object keys, versions, sizes, and SHA-256 values.
   - Recreate fresh PostgreSQL and bucket state, reload, verify every object digest, and rerun all exact retrieval queries with identical ordering.
9. **Failure/reconciliation cases**
   - Object PUT succeeds but DB commit fails: outbox/cleanup reconciliation removes or marks the orphan; no current memory appears.
   - DB proposal commits but object PUT fails: proposal remains blocked and non-retrievable; retry is idempotent.
   - MinIO unavailable during deletion: current retrieval is revoked immediately, deletion stays pending, and the receipt does not claim hard deletion until HEAD/GET proves absence.
10. **Cleanup**
   - Stop both services, prove no candidate ports are listening, retain only sanitized fixture/log evidence, and record exact removal commands.

### Acceptance criteria

- Four synthetic inputs reconcile to exact expected object/proposal/event counts.
- Proposed memory is never returned before promotion.
- Revoked/deleted memory is never returned from current retrieval.
- Cross-tenant retrieval count is zero on every detail/list/query path exercised.
- Same-key/same-digest concurrent replay yields one logical record; different-digest reuse fails closed.
- Ten repeated exact queries before export and after reload return identical ordered IDs and scores.
- Every object manifest digest matches before export and after reload.
- First runtime attempt has public-network egress denied; external business writes and credential reads remain zero.
- Both services remain loopback-only and are stopped at completion.
- A PASS proves only this fixture and S3-port compatibility. It does not approve MinIO, Qdrant, ANN recall, HA, auth, backup, or production operations.

## Why not Qdrant in the first combination

Qdrant becomes justified only when a measured trigger is met, for example:

- exact pgvector p95 latency exceeds the approved threshold at the actual tenant-filtered corpus size;
- PostgreSQL HNSW cannot meet an independently defined recall target under tenant filters;
- sparse/multivector or dedicated vector scaling is required;
- vector load materially harms the operational PostgreSQL SLO.

Until then, Qdrant adds a second durable service, dual-write/reconciliation risk, backup/restore coordination, separate auth/tenant enforcement, and telemetry/unsafe-default hardening without proving more business value.

## Human decisions still required

1. Approve or reject MinIO AGPL use even for an ephemeral compatibility fixture.
2. Decide the production S3-compatible provider independently; MinIO is not approved by this note.
3. Approve the exact PostgreSQL release and obtain exact source/license provenance before a runtime PASS.
4. Approve tenant isolation mode: partition-per-tenant/table family versus row-level security plus mandatory scoped queries.
5. Define measured latency/recall/corpus thresholds that would trigger a Qdrant POC.
6. Define hard-delete versus audit-retention policy for digests, source identifiers, and approval/deletion receipts.
