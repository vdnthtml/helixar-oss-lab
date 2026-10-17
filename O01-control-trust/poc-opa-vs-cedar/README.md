# OPA vs Cedar decision POC

## Question

Given the same synthetic, tenant-scoped, hash-bound approval contract, when OPA 1.18.2 and Cedar CLI 4.11.2 evaluate valid, denied, revoked, malformed and schema-invalid cases offline, which is the safer P0 policy engine beneath Helixar's own authority ledger?

## Observable acceptance

- Six matched authorization cases return identical ALLOW/DENY outcomes.
- Both policy toolchains reject a misspelled schema field before deployment when schema validation is enabled.
- Runtime malformed/missing inputs are compared explicitly; fail-closed is required and diagnostic behavior is recorded.
- Final matched runs execute under macOS network denial.
- Exact versions, source commits, package/binary hashes, license evidence, resource use and cleanup are recorded.

This is a disposable Wave-A decision POC. It does not create implementation authority or integrate either engine into a Helixar repository.
