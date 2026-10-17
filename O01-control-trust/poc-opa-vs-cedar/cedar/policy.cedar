@id("permit-exact-scope")
permit (
  principal is Helixar::Operator,
  action == Helixar::Action::"propose",
  resource is Helixar::Proposal
)
when {
  principal.tenant == resource.tenant &&
  context.approvalValid &&
  context.approvalTargetHash == resource.targetHash
};

@id("forbid-revoked")
forbid (
  principal is Helixar::Operator,
  action,
  resource is Helixar::Proposal
)
when {
  context.approvalRevoked
};
