package helixar.authz

import rego.v1

default allow := false

allow if {
  input.subject.tenant == input.resource.tenant
  input.action == "propose"
  input.approval.valid == true
  input.approval.revoked == false
  input.approval.target_hash == input.resource.target_hash
}
