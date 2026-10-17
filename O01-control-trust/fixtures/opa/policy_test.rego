package helixar.authz_test

import data.helixar.authz.allow
import rego.v1

test_allow_exact_scope if {
  allow with input as {
    "subject": {"tenant": "tenant-a.invalid"},
    "action": "propose",
    "resource": {"tenant": "tenant-a.invalid", "target_hash": "sha256:synthetic.invalid"},
    "approval": {"valid": true, "target_hash": "sha256:synthetic.invalid"}
  }
}

test_deny_cross_tenant if {
  not allow with input as {
    "subject": {"tenant": "tenant-b.invalid"},
    "action": "propose",
    "resource": {"tenant": "tenant-a.invalid", "target_hash": "sha256:synthetic.invalid"},
    "approval": {"valid": true, "target_hash": "sha256:synthetic.invalid"}
  }
}

test_deny_hash_mismatch if {
  not allow with input as {
    "subject": {"tenant": "tenant-a.invalid"},
    "action": "propose",
    "resource": {"tenant": "tenant-a.invalid", "target_hash": "sha256:changed.invalid"},
    "approval": {"valid": true, "target_hash": "sha256:synthetic.invalid"}
  }
}
