# Validation record

Run date: 2026-09-14. Documentation updated 2026-09-15.
Host: Windows, Python 3.12.14, genlayer-test 0.29.2, pytest 9.1.1,
genlayer-py 0.16.3, NumPy 2.5.3.

## Final result

```text
gltest tests/ -q -p no:cacheprovider --tb=short
66 passed in 4.33s
```

No tests deleted, skipped or marked xfail. Coverage: 11 RPC integration cases,
29 direct SDK cases and 26 isolated logic/guardrail cases.

RPC tests ran against dedicated local glsim with five validators, web/LLM mocks
installed before non-deterministic writes and leader-only disabled. Direct
tests use actual SDK storage with an in-memory backend. Isolated tests execute
the contract's actual functions extracted from its AST. These are not production
WASM or live-network LLM tests.

## Source checks

- ASCII scan: zero non-ASCII lines, no scan output.
- Header lines 1/2/3 manually and automatically checked against the request.
- Exactly one Contract(gl.Contract); nondeterministic inner functions do not
  reference self; valid Python syntax.
- Contract unchanged during submission preparation.
- Source SHA256: `d6729116aa1fd9ad3902be6ec8f2f92d0f10bb605ffdaaf3b853e48ecf0a7cfc`.

## Test setup repairs

- Downloaded SDK v0.2.16 from its official GitHub release. Archive SHA256
  `4f0b358ec98ec148be9b95cdfb0f0e1a6cbe64da0194fdfac3fffc6f5d1d93e2`
  matched the release asset digest. Ranged requests recovered a stalled transfer.
- Fixed doubled contracts/ path in the integration test factory.
- Fixed the test address helper to accept bytes or existing SDK Address values.
- Added explicit error-message assertions; negative success alone did not prove
  the expected UserError text.
- Added NumPy, needed by SDK schema loading.
- prepare_windows_tests.py repairs open-file cleanup in the pinned loader.
- prepare_glsim_tests.py fixes schema/storage-class discovery through gltest's
  calldata proxy. Execution instance, mocks, storage and votes are unchanged.

Intermediate complete runs: 26 passed/40 setup errors; 53 passed/3 failed/10
errors; 55 passed/1 failed/10 errors. Final full rerun: all 66 passed.

## Deployment evidence

Updated 2026-09-21: the old address did not resolve and was rejected by the portal.
The unchanged source was redeployed to public studionet:
`0x7516772B9B955bdf3bCCfC86DBf01edDb20Fa322`.

- Deployment transaction: `0xfb4f2784ae7eb7504e4b71baf13c0287dd0cc37d5fba034dd77ab361b89edd21`.
- FINALIZED and execution SUCCESS; leader-only disabled, no mocks.
- Public RPC chain ID: 61999.
- Deployed source: 7,766 bytes; matches repository byte-for-byte and SHA256 above.
- Public schema returns all four expected methods.
- Actual read `get_count()` returned 0 through an independent temporary sender,
  without browser authentication or the deployment key.
- Explorer displays the contract, deploy transaction, FINALIZED and SUCCESS.

Evidence is in deployment-verification.json, deployment-studionet.json and the
compact deployment-receipt.json. Reproduce using scripts/verify_public.py.
The README credential-verdict example remains illustrative/expected; only the
deployment and get_count read are real network results in this correction.
