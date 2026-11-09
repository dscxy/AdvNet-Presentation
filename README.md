# AdvNet Presentation

Material for a course presentation on *AdvNet: Revealing Performance Issues in Network
Protocols by Generating Adversarial Environments* (PACMNET / CoNEXT 2026,
[doi:10.1145/3808660](https://doi.org/10.1145/3808660)).

The deliverables are a beamer slide deck and a spoken script for a 25-minute talk, aimed at
students who have not read the paper. `AGENTS.md` carries the working conventions and the
course requirements the talk has to satisfy; this file is the map of the repository.

## Layout

| Path | Contents |
| --- | --- |
| `AGENTS.md` | Project conventions, presentation objective, and the mandatory course requirements. |
| `docs/` | Source material: the paper PDF, plus `docs/mineru/` with a machine-readable parse of it. |
| `scripts/` | Accepted spoken script and the slide-change cue sheet for a 25-minute talk. |
| `slides/` | Beamer source, the compiled presentation PDF, figure assets, and build instructions. |
| `third_party/AdvNet/` | The authors' implementation, tracked as a git submodule. |
| `tmp/` | Scratch space for local work; not tracked by git. |

### `docs/mineru/`

Produced once from the PDF with MinerU at its `advanced` tier. The Markdown parse is what we
quote from when drafting the slides and the script.

| Path | Contents |
| --- | --- |
| `advnet/markdown.md` | Full paper as Markdown; figures under `advnet/images/`. |
| `advnet/*.json` | Parser sidecars (`middle_json`, `model_output`, `structured_content`). |

### `third_party/AdvNet`

Upstream: [Dariwala/AdvNet](https://github.com/Dariwala/AdvNet), MIT licensed, pinned to
`main` at commit `6390c47`. Initialize it after cloning:

```bash
git submodule update --init third_party/AdvNet
```

The repository implements the design described in the paper: trace generators (`GA/`, `BO/`,
`BL/`, `RL/`, `random_generator/`), scoring, post-learning selection, and the emulation
backends for single-flow CC, MPTCP, QUIC, data channels, and multi-flow setups.

## Upstream branch `fix/throughput-unit-mismatch`

One commit (`af7c795`, "Fix throughput unit mismatch in type-8 scoring"), **not** merged into
`main`. It touches `mptcp/evaluate.py` only: on the `mptcp_type == 8` path the reference
bandwidth is converted from kbit/s to MiB/s before scoring, so that it matches the unit of
the measured throughput.

This matters when quoting or reproducing the MPTCP numbers (§4.4.4). The score is a ratio
between reference and target performance (§3.5, Eq. 1), so a unit mismatch on the reference
side skews every score for that configuration.

The submodule stays pinned to `main`. Check the branch out only if you actually run the code:

```bash
git -C third_party/AdvNet fetch origin fix/throughput-unit-mismatch
git -C third_party/AdvNet checkout fix/throughput-unit-mismatch

# restore the pinned commit afterwards
git submodule update third_party/AdvNet
```

Until it is restored, the checked-out branch shows up as a modified submodule in `git status`.
