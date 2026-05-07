# prereg-v0.0.1 — Spec freeze (pre-data)

Spec frozen 2026-05-07 before any (MA, trial) data extraction.

## OpenTimestamps stamp

**OTS stamp DEFERRED.** The local Windows + Python 3.13 environment hits a known
`opentimestamps-client 0.7.2` + python-bitcoinlib SSL-loader bug
(searches for legacy `libeay32.dll` which is absent on Windows with OpenSSL 3.x).

Resolution options for v0.1.0 release:
1. Use a Python 3.11 or 3.12 env (pyenv, conda, or system install) for OTS only.
2. Use the OpenTimestamps web stamper at https://opentimestamps.org and commit the resulting `.ots` proof.
3. Use a different OTS client (e.g., `ots-cli` from a docker container).

Once a `.ots` proof is generated, place it at `.ots/prereg-v0.0.1-spec.md.ots` and:
```
ots upgrade .ots/prereg-v0.0.1-spec.md.ots   # after Bitcoin block confirmation (~24h)
```
Then commit the upgraded `.ots` file.

## Snapshot contents

- `spec.md` — verbatim copy of `docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md` at this tag.
- `(no .ots yet)` — see above.
