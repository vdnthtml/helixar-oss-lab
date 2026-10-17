permit (
  principal is Helixar::Operator,
  action == Helixar::Action::"propose",
  resource is Helixar::Proposal
)
when {
  principal.tenent == resource.tenant
};
