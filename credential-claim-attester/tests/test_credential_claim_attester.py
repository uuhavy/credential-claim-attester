"""Studio integration tests. Requires a simulator with sim_installMocks."""
import json

import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_failed, tx_execution_succeeded


URL = "https://example.com/credentials/alice"
CLAIM = "AWS Solutions Architect certified"


@pytest.fixture
def contract(default_account):
    return get_contract_factory(contract_file_path="credential_claim_attester.py").deploy(
        args=[], account=default_account
    )


@pytest.fixture
def install_mocks(gl_client):
    def install(verdict="SUPPORTED", confidence=90, body="AWS certificate for Alice", status=200):
        response = gl_client.provider.make_request(
            method="sim_installMocks",
            params={
                "llm_mocks": {".*": json.dumps({
                    "verdict": verdict, "confidence": confidence,
                    "reason": "Assessment based on the supplied certificate evidence.",
                })},
                "web_mocks": {".*": {"status": status, "body": body}},
            },
        )
        assert not response.get("error"), response
    yield install
    response = gl_client.provider.make_request(
        method="sim_installMocks", params={"llm_mocks": {}, "web_mocks": {}}
    )
    assert not response.get("error"), response


def submit(contract, account, claim=CLAIM, url=URL):
    return contract.connect(account).submit_claim(args=[claim, url]).transact(value=0)


def test_happy_path(contract, default_account, install_mocks):
    install_mocks()
    assert tx_execution_succeeded(submit(contract, default_account))
    row = json.loads(contract.get_attestation(args=["0"]).call())
    assert row["verdict"] == "SUPPORTED"
    assert row["confidence"] == 90
    assert row["claimant"].lower() == default_account.address.lower()
    assert contract.get_count().call() == 1
    rows = json.loads(contract.get_claims_by_address(args=[row["claimant"]]).call())
    assert rows == [row]
    assert rows[0]["attestation_id"] == "0"


@pytest.mark.parametrize("verdict,confidence", [("PARTIAL", 60), ("UNSUPPORTED", 20)])
def test_other_verdicts(contract, default_account, install_mocks, verdict, confidence):
    install_mocks(verdict, confidence)
    assert tx_execution_succeeded(submit(contract, default_account))
    row = json.loads(contract.get_attestation(args=["0"]).call())
    assert (row["verdict"], row["confidence"]) == (verdict, confidence)


@pytest.mark.parametrize("claim,url,message", [
    (CLAIM, "not-a-url", "evidence_url must start"),
    ("", URL, "skill_claim must not be empty"),
    ("   ", URL, "skill_claim must not be empty"),
])
def test_invalid_input(contract, default_account, claim, url, message):
    receipt = submit(contract, default_account, claim, url)
    assert tx_execution_failed(receipt)
    assert message in json.dumps(receipt, default=str)
    assert contract.get_count().call() == 0


@pytest.mark.parametrize("status", [200, 503])
def test_unavailable_evidence(contract, default_account, install_mocks, status):
    install_mocks("UNSUPPORTED", 15, body="", status=status)
    assert tx_execution_succeeded(submit(contract, default_account))
    row = json.loads(contract.get_attestation(args=["0"]).call())
    assert row["verdict"] == "UNSUPPORTED"
    assert row["confidence"] < 35


def test_multiple_claims(contract, default_account, install_mocks):
    install_mocks()
    for claim in [CLAIM, "Built a Rust compiler"]:
        assert tx_execution_succeeded(submit(contract, default_account, claim))
    rows = json.loads(contract.get_claims_by_address(args=[default_account.address]).call())
    assert [r["attestation_id"] for r in rows] == ["0", "1"]
    assert [r["skill_claim"] for r in rows] == [CLAIM, "Built a Rust compiler"]
    assert contract.get_count().call() == 2


def test_missing_attestation(contract):
    with pytest.raises(Exception, match="attestation not found"):
        contract.get_attestation(args=["missing"]).call()


def test_unknown_address(contract):
    assert contract.get_claims_by_address(args=["0x" + "12" * 20]).call() == "[]"
