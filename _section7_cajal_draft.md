## §7 — Limitations stated up front

This section pre-commits the project to a stated set of limitations on what the methodology in this repository can and cannot address, within and beyond the publication window. The limitations are committed in advance for the same reason the honesty bounds in §1 are: so that a reader evaluating any result has the project's own acknowledgement of scope already on the record, and so that subsequent results can be measured against the project's stated scope rather than against an unspecified expectation.

The limitations enumerated here are not failures of the project; they are scope. The project's success criteria in §0.2 and failure criteria in §0.3 operate inside these limits. A result that exceeds the scope of these limitations — by speaking to a question or claim outside what the methodology can address — is a flagging event under §1's bound-crossing protocol, not a result.

### §7.1 — Substrate-coverage limitation

The methodology characterizes a small set of substrate voices within the publication window. At the project's pre-committed minimum (§0.2: three voices), the substrate coverage is intentionally narrow, selected for falsifiability rather than for exhaustive representation of the modeled domain. The honest end-state is not a model of "the power grid" or "the alternative-energy investment system" in full; it is a witnessed search across a small number of pre-committed voices, with the failure rate among those voices treated as the finding alongside any successful recoveries.

Readers who require comprehensive coverage of either domain for operational decisions should not draw such coverage from this repository within the publication window.

### §7.2 — Regional-scope limitation

The methodology is parameterized per region. Voices added against a particular regulatory substrate — a particular country's ISO regime, a particular jurisdiction's tax-credit structure, a particular grid operator's authorization scope — characterize that substrate; they do not transfer to other substrates without separate voice addition. The pre-committed regions for the publication window will be named in the registry as voices land. Conclusions outside the named regional set are out of scope.

### §7.3 — Temporal-scope limitation

The publication window is bounded (currently six months from the timestamp of commit 2). Findings produced at the close of the window reflect the state of the substrate voices that landed within the window. The methodology does not back-cast the moment of any future regulatory, capital, or research-edge transition; it characterizes the conditions under which such a transition, if it occurs, would be recognizable. Forward-looking statements about the trajectory of any real region's power sovereignty are out of scope.

Voices that take longer than the publication window to produce a verdict are pre-committed to be marked open at window close and dated forward; they are not retroactively withdrawn from the registry.

### §7.4 — Validation-recovery scope

The historical-events validation pass in §4 recovers events at the qualitative-trajectory level, as pre-committed in lighthouse's §4 commitment. The methodology does not produce point estimates against the validation events, does not claim numerical agreement with documented post-event measurements, and does not credential itself against any specific production simulation result. Recovery is binary at the qualitative level: the substrate-chain trajectory either reproduces the documented qualitative response within the documented window, or it does not.

### §7.5 — Proxy-data limitation

The methodology operates against publicly available regional parameters: regulatory text, tax-credit and incentive records, grid-topology documentation, bibliometric and grant-record proxies for edge-research density, and locality-level demand profiles drawn from open data. The methodology does not access — and the project does not have — private financial pipelines, undisclosed term sheets, confidential operator dispatch logs, or non-public regulatory deliberations. Findings are conditional on the public proxies used. Any divergence between a public proxy and the underlying private reality the proxy stands for is a limitation of the proxy, and any methodology result built on that proxy is itself constrained by it.

### §7.6 — Methodological-novelty scope

The project investigates whether simulation can be used to identify a class of structural dynamics in the modeled substrate chain. The project does not claim novelty for power-grid simulation as a field; many production simulators predate this project and do other things well. The contribution this project pre-registers is the substrate-voice predict / kill-condition / run / verdict protocol applied to the specific question of §0. Reviewers comparing this repository to production grid-engineering tools should consult §1's first bound: the open repository is not interchangeable with those tools and does not aim to be.

### §7.7 — Not a substitute for

The project pre-commits, in advance and on the record, that nothing produced in this repository within the publication window is a substitute for:

- Production grid-engineering analysis. Operational decisions about real grids should use production solvers (MATPOWER, OpenDSS, GridLAB-D, vendor systems) with operator-grade fidelity and engineering sign-off.
- Real-world investment decisions. Capital reallocation by an operator, fund, or research-stage company should not be made on the basis of a methodology result from this repository alone. The findings are characterizations of conditional structural dynamics under stated assumptions, not investment advice.
- Fiduciary or regulatory analysis. The methodology has no fiduciary credential. Conclusions produced from it do not satisfy regulatory or fiduciary reporting requirements in any jurisdiction.
- Production-grade certainty about any region's future power sovereignty. The methodology characterizes recognizability of structural transitions, not their occurrence.

Readers for whom any of the above is the operational need should treat this repository as context for that need, not as a tool to fulfill it.

### §7.8 — Limitations of this limitations section

This section is itself limited. The project pre-commits to revisiting §7 in subsequent commits as voices land and as the publication window proceeds; new limitations may be added, but existing limitations are not removed or weakened without an explicit and dated commit explaining the removal. The same expansion-permitted-relaxation-not discipline applied to §1's bounds applies here. If a reader believes the project has crossed a stated limit — produced a result outside scope, claimed coverage beyond what is named — the project commits to surfacing that under §1's bound-crossing protocol and publishing the resolution alongside the failure ledger.

---
