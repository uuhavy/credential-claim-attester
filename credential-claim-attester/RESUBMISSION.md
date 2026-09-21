# Corrected contribution - public deployment

The rejection identified an unresolvable deployment address. This correction
replaces that address with a new public deployment of the exact same source.
No change was made to the contract or its validator.

Use **Resubmit / Submit a corrected contribution**, not an appeal asserting the
original address was valid. The original address still does not resolve.

## Replace both evidence entries

1. Studio contract:
   https://explorer-studio.genlayer.com/address/0x7516772B9B955bdf3bCCfC86DBf01edDb20Fa322
2. GitHub repository:
   https://github.com/uuhavy/credential-claim-attester

Network: **studionet** (chain ID 61999). Contribution date: **2026-09-21** for
the corrected public deployment. Use Title and Description from SUBMISSION.md.
Remove the previous contract link rather than keeping two conflicting addresses.

## Correction note

The unresolvable address has been replaced with a public studionet deployment:
0x7516772B9B955bdf3bCCfC86DBf01edDb20Fa322. Deployment transaction
0xfb4f2784ae7eb7504e4b71baf13c0287dd0cc37d5fba034dd77ab361b89edd21 is
FINALIZED with SUCCESS. Public RPC verification confirms deployed source matches
the submitted repository byte-for-byte, the schema exposes all four methods,
and get_count() returns 0. Reproducible verification and evidence are committed
to the repository. Contract code and consensus logic are unchanged.

Complete the reCAPTCHA and submit the corrected contribution yourself under
Builder -> Intelligent Contracts. Re-run public verification before submission
if time has passed; hosted network availability cannot be guaranteed indefinitely.
