"""Local gltest execution; does not claim to validate GenVM deployment."""
import json

import pytest


URL = "https://example.com/alice"


def address_hex(raw):
    from genlayer import Address
    return raw.as_hex if hasattr(raw, "as_hex") else Address(raw).as_hex


def mocks(vm, verdict="SUPPORTED", confidence=90, reason="Certificate confirms skill.", body="Public certificate"):
    vm.clear_mocks()
    vm.mock_web(r".*", {"status": 200, "body": body})
    vm.mock_llm(r".*", json.dumps({
        "verdict": verdict, "confidence": confidence, "reason": reason,
    }))


@pytest.fixture
def contract(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    return direct_deploy("contracts/credential_claim_attester.py", sdk_version="v0.2.16")


@pytest.mark.parametrize("verdict,confidence", [("SUPPORTED", 90), ("PARTIAL", 60), ("UNSUPPORTED", 20)])
def test_round_trip(contract, direct_vm, direct_alice, verdict, confidence):
    mocks(direct_vm, verdict, confidence)
    assert contract.submit_claim("  AWS certified  ", URL) == "0"
    row = json.loads(contract.get_attestation("0"))
    assert row["skill_claim"] == "AWS certified"
    assert row["verdict"] == verdict
    assert row["confidence"] == confidence
    assert row["claimant"] == address_hex(direct_alice)
    assert json.loads(contract.get_claims_by_address(address_hex(direct_alice).lower())) == [row]
    assert contract.get_count() == 1
    assert direct_vm.run_validator() is True


@pytest.mark.parametrize("claim,url,message", [
    ("Rust", "not-a-url", "evidence_url must start"),
    ("", URL, "skill_claim must not be empty"),
    ("  ", URL, "skill_claim must not be empty"),
])
def test_bad_input(contract, direct_vm, claim, url, message):
    with direct_vm.expect_revert(message):
        contract.submit_claim(claim, url)
    assert contract.get_count() == 0


def test_empty_page(contract, direct_vm):
    mocks(direct_vm, "UNSUPPORTED", 15, body="")
    contract.submit_claim("Rust", URL)
    row = json.loads(contract.get_attestation("0"))
    assert (row["verdict"], row["confidence"]) == ("UNSUPPORTED", 15)


def test_order_and_sender_isolation(contract, direct_vm, direct_alice, direct_bob):
    mocks(direct_vm)
    contract.submit_claim("AWS", URL)
    contract.submit_claim("Rust", URL)
    direct_vm.sender = direct_bob
    contract.submit_claim("Python", URL)
    rows = json.loads(contract.get_claims_by_address(address_hex(direct_alice)))
    assert [r["attestation_id"] for r in rows] == ["0", "1"]
    assert [r["skill_claim"] for r in rows] == ["AWS", "Rust"]
    assert len(json.loads(contract.get_claims_by_address(address_hex(direct_bob)))) == 1
    assert contract.get_count() == 3


def test_missing_reads(contract, direct_vm, direct_bob):
    with direct_vm.expect_revert("attestation not found"):
        contract.get_attestation("404")
    assert contract.get_claims_by_address(address_hex(direct_bob)) == "[]"
    assert contract.get_claims_by_address("unknown") == "[]"


@pytest.mark.parametrize("leader,validator,agree", [
    (0, 34, True), (34, 35, False), (35, 79, True),
    (79, 80, False), (80, 100, True),
])
def test_confidence_bands(contract, direct_vm, leader, validator, agree):
    mocks(direct_vm, confidence=leader)
    contract.submit_claim("Rust", URL)
    mocks(direct_vm, confidence=validator, reason="Different wording and detail.")
    assert direct_vm.run_validator() is agree


def test_verdict_disagreement(contract, direct_vm):
    mocks(direct_vm)
    contract.submit_claim("Rust", URL)
    mocks(direct_vm, "PARTIAL", 90)
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize("raw", ["broken json", "{}", "[]", None])
def test_malformed_leader_result(contract, direct_vm, raw):
    mocks(direct_vm)
    contract.submit_claim("Rust", URL)
    assert direct_vm.run_validator(leader_result=raw) is False


def test_non_return_leader(contract, direct_vm):
    mocks(direct_vm)
    contract.submit_claim("Rust", URL)
    assert direct_vm.run_validator(leader_error=ValueError("leader failed")) is False


@pytest.mark.parametrize("raw", ["broken json", "{}", "[]", '{"verdict":"SUPPORTED","confidence":true,"reason":"x"}'])
def test_malformed_validator_response(contract, direct_vm, raw):
    mocks(direct_vm)
    contract.submit_claim("Rust", URL)
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*", {"status": 200, "body": "Evidence"})
    direct_vm.mock_llm(r".*", raw)
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize("confidence,expected", [(-20, 0), (140, 100)])
def test_normalization(contract, direct_vm, confidence, expected):
    mocks(direct_vm, " supported ", confidence, reason="x" * 450)
    contract.submit_claim("Rust", URL)
    row = json.loads(contract.get_attestation("0"))
    assert row["confidence"] == expected
    assert row["verdict"] == "SUPPORTED"
    assert len(row["reason"]) == 400


def test_repeated_submission_is_append_only(contract, direct_vm, direct_alice):
    mocks(direct_vm)
    first = contract.submit_claim("Rust", URL)
    original = contract.get_attestation(first)
    second = contract.submit_claim("Rust", URL)
    assert (first, second) == ("0", "1")
    assert contract.get_attestation(first) == original
    assert len(json.loads(contract.get_claims_by_address(address_hex(direct_alice)))) == 2


def test_zero_confidence_is_valid(contract, direct_vm):
    mocks(direct_vm, "UNSUPPORTED", 0, body="")
    assert contract.submit_claim("Rust", URL) == "0"
    assert json.loads(contract.get_attestation("0"))["confidence"] == 0


def test_malformed_leader_does_not_write(contract, direct_vm):
    direct_vm.mock_web(r".*", {"status": 200, "body": "Evidence"})
    direct_vm.mock_llm(r".*", "{}")
    with direct_vm.expect_revert("invalid credential assessment response"):
        contract.submit_claim("Rust", URL)
    assert contract.get_count() == 0
