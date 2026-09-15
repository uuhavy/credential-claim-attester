# Portal submission draft

Track: Builder

Contribution type: Intelligent Contracts

Title: CredentialClaimAttester - Reusable Credential Evidence Attestations

Description:

CredentialClaimAttester assesses whether public web evidence supports a wallet-submitted skill, experience or certification claim and stores an append-only attestation. GenLayer run_nondet_unsafe uses a custom validator that independently reads the evidence and reassesses the claim, agreeing on the MEANING of the decision, not JSON format: verdict and confidence band must match. Different verdicts reject. DAO member vetting, job-board screening and grant collaborator qualification can reuse the same API. It ships with 66 passing local tests and documentation, with no frontend. Builder-reported studionet deployment: 0x8f0Cfbf5B297bD75a665e9c8A42082cAF99ce17D; public RPC re-verification is pending.

Evidence URL: https://github.com/uuhavy/credential-claim-attester

Paste the GitHub URL into the Evidence field. Submit this yourself at
https://portal.genlayer.foundation under Builder -> Intelligent Contracts,
after completing the reCAPTCHA. Before submitting, recheck the studionet
deployment's public visibility; the current verification limitation is recorded
in README.md and VALIDATION.md.
