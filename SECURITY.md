# Security policy

## Scope

counterscreen is research software. It produces design candidates and
statistical claims; it does not handle credentials, personal data, or
patient data, and it exposes no network service.

Two areas are worth a security eye regardless:

- **Third-party model execution.** The `generate`, `sequence` and `fold`
  packages drive external binaries and model weights as subprocesses. A
  malicious weights file or a crafted structure input is an untrusted input
  to someone else's parser.
- **Provenance integrity.** Results under `campaigns/*/results/` are
  evidence and are append-only. A defect that lets a recorded measurement be
  silently rewritten is a correctness *and* integrity bug, and we treat it as
  the more serious of the two.

## Reporting a vulnerability

Report privately through GitHub's advisory form:

<https://github.com/mbote-droid/counterscreen/security/advisories/new>

Please do not open a public issue for anything exploitable. Include what you
did, what happened, and the commit you were on. Expect an acknowledgement
within a week; this is a small project and there is no on-call rota.

## Supported versions

Pre-1.0. Only the tip of the default branch is supported. No backports.

## What is not a vulnerability

- A model producing a bad design. That is a scientific result, and the
  control panel exists to catch it.
- Needing a GPU, large weights, or licensed third-party software to run the
  generative stages.
- Resource exhaustion from deliberately oversized structure inputs run
  locally by the operator.
