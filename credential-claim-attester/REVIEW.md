# Standalone primitive review

## Meaning, not format

The validator independently reads evidence and runs its own assessment. It
compares normalized verdict plus confidence band, not JSON strings or wording.
All six ordered pairs of differing verdicts reject in tests, as do confidence
boundaries 34/35 and 79/80. This is a substantive semantic comparison of the
classification and reliability band. It does not verify every factual statement
in the leader's free-text reason.

## State and lifecycle

Attestation has both storage decorators. Persisted numbers are bigint, map
keys are strings, and per-wallet histories are DynArray values. Consensus
finishes before state writes. IDs increase from zero. The lifecycle is
append-only with no update, delete or consume operation.

## Edge cases: actual behavior

- Empty/whitespace claims and bad URL prefixes raise UserError. URL validation
  checks only the prefix, not the complete host or URL syntax.
- Zero confidence is valid. There is no payment or zero-amount operation.
- Identical submissions are permitted and create different records; there is
  no consume operation needing a double-process flag.
- Web failures become empty evidence. UNSUPPORTED with low confidence is
  prompt policy, not a separate deterministic constraint.
- Invalid model JSON/fields raises UserError during normalization. Invalid
  leader results and failed validator reassessments cause disagreement.
- An exec_prompt service exception can propagate as the runtime's original
  error, because the call precedes the normalization try block. No attestation
  is written, but not every service failure becomes a custom UserError.
- Missing IDs raise UserError; unknown/invalid address reads return an empty list.

## Reusability and limits

DAO member vetting, job-board screening and grant collaborator qualification
can consume the same parameterized API. It is a reusable primitive, rather
than a fixed-input demo. No portal score or acceptance is guaranteed.

The wallet identifies the submitter, not verified ownership of a web profile.
Consumers need a separate identity link. Live pages can change, only the first
6,000 characters are read, evidence snapshots are not stored, and wallet
histories are not paginated. Reasons are leader-authored and confidence is not
a calibrated probability.

## Minimal improvements

Applied without changing public behavior: reproducible dev dependencies,
test-tool compatibility fixes, stronger error assertions, all verdict mismatch
pairs, source guardrail checks, duplicate/zero-confidence tests, and explicit
evidence limitations in documentation.

Future changes requiring builder approval and redeployment:

1. Convert LLM service exceptions into a clear UserError.
2. Enforce empty-evidence verdict/confidence policy in code.
3. Require wallet/profile ownership proof if offering identity verification.

None of these behavior changes were applied. The deployed source is unchanged.
