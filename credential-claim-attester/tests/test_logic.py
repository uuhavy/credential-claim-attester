"""Exercise actual decision functions without SDK downloads or storage emulation."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import typing

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "contracts" / "credential_claim_attester.py"


@pytest.fixture
def logic():
    tree = ast.parse(SOURCE.read_text(encoding="ascii"))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ("_norm_verdict", "_band", "_decision")]
    contract = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Contract")
    submit = next(n for n in contract.body if isinstance(n, ast.FunctionDef) and n.name == "submit_claim")
    functions += [n for n in submit.body if isinstance(n, ast.FunctionDef)]

    class Return:
        def __init__(self, calldata):
            self.calldata = calldata

    class UserError(Exception):
        pass

    state = SimpleNamespace(web="evidence", answer={"verdict": "SUPPORTED", "confidence": 90, "reason": "Evidence confirms skill."}, prompts=[])

    def render(url, mode):
        assert mode == "text"
        if isinstance(state.web, Exception):
            raise state.web
        return state.web

    def prompt(text, response_format):
        assert response_format == "json"
        state.prompts.append(text)
        return state.answer

    gl = SimpleNamespace(vm=SimpleNamespace(Return=Return, UserError=UserError),
                         nondet=SimpleNamespace(web=SimpleNamespace(render=render), exec_prompt=prompt))
    scope = {"json": json, "typing": typing, "gl": gl,
             "skill_claim": "Rust", "evidence_url": "https://example.com"}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), "exec"), scope)
    return SimpleNamespace(**scope, state=state)


@pytest.mark.parametrize("a,b,expected", [(0,34,True),(34,35,False),(35,79,True),(79,80,False),(80,100,True)])
def test_semantic_bands(logic, a, b, expected):
    leader = json.dumps({"verdict":"SUPPORTED","confidence":a,"reason":"Leader wording"})
    logic.state.answer["confidence"] = b
    assert logic.validator_fn(logic.gl.vm.Return(leader)) is expected


@pytest.mark.parametrize("leader_verdict,validator_verdict", [
    ("SUPPORTED", "PARTIAL"), ("SUPPORTED", "UNSUPPORTED"),
    ("PARTIAL", "SUPPORTED"), ("PARTIAL", "UNSUPPORTED"),
    ("UNSUPPORTED", "SUPPORTED"), ("UNSUPPORTED", "PARTIAL"),
])
def test_verdict_difference(logic, leader_verdict, validator_verdict):
    logic.state.answer["verdict"] = leader_verdict
    leader = logic.leader_fn()
    logic.state.answer["verdict"] = validator_verdict
    assert logic.validator_fn(logic.gl.vm.Return(leader)) is False


@pytest.mark.parametrize("raw", ["invalid", "{}", "[]", "null", '{"verdict":"SUPPORTED","confidence":true,"reason":"x"}'])
def test_bad_leader(logic, raw):
    assert logic.validator_fn(logic.gl.vm.Return(raw)) is False


def test_non_return(logic):
    assert logic.validator_fn(ValueError("failed")) is False


@pytest.mark.parametrize("raw", ["invalid", {}, {"verdict":"UNKNOWN","confidence":50,"reason":"x"}])
def test_bad_validator_output(logic, raw):
    leader = logic.leader_fn()
    logic.state.answer = raw
    assert logic.validator_fn(logic.gl.vm.Return(leader)) is False


@pytest.mark.parametrize("page", ["", RuntimeError("network unavailable")])
def test_web_failure_still_calls_llm(logic, page):
    logic.state.web = page
    logic.state.answer.update(verdict="UNSUPPORTED", confidence=15)
    assert json.loads(logic.leader_fn())["confidence"] == 15
    assert json.loads(logic.state.prompts[0].split("\n", 1)[1])["evidence_text"] == ""


def test_evidence_limit(logic):
    logic.state.web = "x" * 7000
    logic.leader_fn()
    assert len(json.loads(logic.state.prompts[0].split("\n",1)[1])["evidence_text"]) == 6000


@pytest.mark.parametrize("confidence,expected", [(-3,0),(120,100)])
def test_normalized_output(logic, confidence, expected):
    logic.state.answer.update(verdict=" supported ", confidence=confidence, reason="x" * 500)
    result = json.loads(logic.leader_fn())
    assert result == {"verdict":"SUPPORTED", "confidence":expected, "reason":"x" * 400}


def test_deployment_guardrails():
    raw = SOURCE.read_bytes()
    assert raw.isascii()
    source = raw.decode("ascii")
    assert source.splitlines()[:3] == [
        "# v0.2.16",
        '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }',
        'from genlayer import *',
    ]
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and any(ast.unparse(b) == "gl.Contract" for b in n.bases)]
    assert len(classes) == 1 and classes[0].name == "Contract"
    submit = next(n for n in classes[0].body if isinstance(n, ast.FunctionDef)
                  and n.name == "submit_claim")
    inner = [n for n in submit.body if isinstance(n, ast.FunctionDef)]
    assert {n.name for n in inner} == {"leader_fn", "validator_fn"}
    assert not any(isinstance(n, ast.Name) and n.id == "self"
                   for fn in inner for n in ast.walk(fn))
    nondet_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and ast.unparse(n.func).startswith("gl.nondet.")]
    leader = next(n for n in inner if n.name == "leader_fn")
    assert nondet_calls and all(n in list(ast.walk(leader)) for n in nondet_calls)
