#!/usr/bin/env python3
"""Validate O02 storage candidate provenance and bounded fixture recommendation."""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTE = ROOT / "storage-candidate-recommendation.md"
SPEC = ROOT / "storage-fixture-spec.json"

EXPECTED = {
    "PostgreSQL+pgvector": {
        "repo": ROOT / "repos/pgvector",
        "commit": "a6420355c5d1c08f4c5fbd5112fc17e4cf3b5eb5",
        "tree": "52b7f4807f58d7ae61990ba5c95f26755e66d65a",
        "license_sha256": "6bba9ebeb73e27477463b05e5ef1bf303bccbddb3db9bbc95905d351604d6a87",
    },
    "Qdrant": {
        "repo": ROOT / "repos/qdrant",
        "commit": "44ad62f8cd69642be5afa6441612525e24a0d063",
        "tree": "c6b12563a75f1c5ee866e763be8ad93ebc51e5a8",
        "license_sha256": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    },
    "MinIO": {
        "repo": ROOT / "repos/minio",
        "commit": "7aac2a2c5b7c882e68c1ce017d8256be2feea27f",
        "tree": "376b09b793c57170a905208e64590164d8ab7a3b",
        "license_sha256": "0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0",
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def port_free(port: int) -> bool:
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            if sock.connect_ex((host, port)) == 0:
                return False
        finally:
            sock.close()
    return True


def main() -> int:
    note = NOTE.read_text(encoding="utf-8")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    checks: dict[str, object] = {}

    for candidate, expected in EXPECTED.items():
        repo = expected["repo"]
        actual = {
            "commit": git(repo, "rev-parse", "HEAD"),
            "tree": git(repo, "rev-parse", "HEAD^{tree}"),
            "license_sha256": sha256(repo / "LICENSE"),
            "clean": git(repo, "status", "--porcelain=v1") == "",
        }
        assert actual["commit"] == expected["commit"], (candidate, actual)
        assert actual["tree"] == expected["tree"], (candidate, actual)
        assert actual["license_sha256"] == expected["license_sha256"], (candidate, actual)
        assert actual["clean"], (candidate, actual)
        assert expected["commit"] in note
        checks[candidate] = actual

    assert spec["fixture_id"] == "O02-STOR-FX-01"
    assert spec["status"] == "RECOMMENDED_NOT_RUN"
    assert spec["stack"]["authority_store"] == "PostgreSQL with pgvector"
    assert spec["stack"]["object_port_fixture_provider"] == "MinIO"
    assert spec["stack"]["excluded_from_first_fixture"] == "Qdrant"
    assert "proposal is not current truth" in spec["authority_invariants"]
    assert any("127.0.0.1" in item for item in spec["runtime_requirements"])
    assert "O02-STOR-FX-01" in note
    assert "REJECT_OPERATIONS" in note and "POC_MORE" in note and "ADAPT" in note

    commands = ["docker", "podman", "psql", "postgres", "pg_config", "minio", "mc", "go", "rustc", "cargo"]
    command_paths = {command: shutil.which(command) for command in commands}
    free_ports = {str(port): port_free(port) for port in (5432, 6333, 6334, 9000, 9001)}
    assert all(free_ports.values()), free_ports

    output = {
        "status": "PASS",
        "recommendation_validated": True,
        "fixture_status": spec["status"],
        "fixture_id": spec["fixture_id"],
        "candidate_provenance": checks,
        "host_command_paths": command_paths,
        "candidate_ports_free": free_ports,
        "service_fixture_run": False,
        "service_fixture_not_run_reason": spec["not_run_reason"],
        "proof_boundary": "Source provenance and recommendation/spec consistency only; no PostgreSQL, Qdrant, or MinIO server was installed or started.",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
