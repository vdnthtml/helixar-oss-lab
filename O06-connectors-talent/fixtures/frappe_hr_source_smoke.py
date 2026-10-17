#!/usr/bin/env python3
"""Validate Frappe HR onboarding contract from the pinned source tree."""
from __future__ import annotations

import json
import py_compile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
REPO = LAB / "repos" / "frappe-hr"
doctype_path = REPO / "hrms" / "hr" / "doctype" / "employee_onboarding" / "employee_onboarding.json"
controller_path = REPO / "hrms" / "controllers" / "employee_boarding_controller.py"
doctype = json.loads(doctype_path.read_text(encoding="utf-8"))
fields = {field["fieldname"]: field for field in doctype["fields"]}

assert doctype["name"] == "Employee Onboarding"
assert fields["job_applicant"]["reqd"] == 1
assert fields["job_offer"]["reqd"] == 1
assert fields["boarding_status"]["read_only"] == 1
assert fields["boarding_status"]["options"].splitlines() == ["Pending", "In Process", "Completed"]
roles = {permission["role"]: permission for permission in doctype["permissions"]}
assert roles["HR Manager"]["submit"] == 1
assert roles["HR User"].get("submit", 0) == 0
assert roles["HR Manager"]["export"] == 1
assert roles["System Manager"]["delete"] == 1

controller = controller_path.read_text(encoding="utf-8")
assert "update_employee_boarding_status" in controller
assert 'frappe.db.set_value("Employee Onboarding"' in controller
py_compile.compile(str(controller_path), doraise=True)

result = {
    "status": "PASS",
    "validatedSource": str(doctype_path.relative_to(LAB)),
    "controllerSyntaxCompiled": True,
    "humanOwnedStates": ["Pending", "In Process", "Completed"],
    "requiredLinks": ["Job Applicant", "Job Offer"],
    "roleGate": {"HR Manager submit": True, "HR User submit": False},
    "exportPermission": "HR Manager",
    "deletePermission": "System Manager",
    "serviceStarted": False,
    "limitation": "Frappe and ERPNext v17 dependencies not installed; schema/controller component smoke only",
}
(LAB / "artifacts" / "frappe-hr-source-smoke.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
