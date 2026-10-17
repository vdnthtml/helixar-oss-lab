package helixar.authz

import rego.v1

default allow := false

allow if {
  input.subject.tenent == input.resource.tenant
  input.action == "propose"
}
