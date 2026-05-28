# Pre-registration — `grid-diamondcutter`

Pre-registered: 2026-05-28. Commit 2 of the publication sequence described in §2.

This document states, before any results have been produced or interpreted in this repository, what the project will investigate, what would falsify each commitment, what the project will not claim, and how readers can independently verify the work.

## §0 — What this project investigates

The project investigates whether power-grid simulation, instrumented with the methodology in this repository, can characterize the structural dynamics by which grid operators choose between two classes of investment in alternative energy: (a) direct deployment of renewables that have already been validated in production elsewhere, and (b) capital allocation to earlier-stage alternative-energy approaches that have not yet cleared the pilot-validation gate. Power-grid operators currently invest predominantly in (a) because the gate to commercial engagement with (b) requires demonstration in already-deployed pilots — a chicken-and-egg condition in which novel approaches do not reach the operator's investment surface, and the field's rate of advance is bounded by it.

The central question is whether simulation can identify the structural conditions under which reallocating a fraction of operator-controlled capital toward earlier-stage approaches produces measurable downstream gains in regional power sovereignty, versus producing no measurable effect. The phenomenon the simulation is specifically built to test for is a **threshold-class cascade**: a region- and regulator-specific moment at which alternative-energy reallocation transitions from marginal contribution to driving force. Below the threshold, reallocation washes out. Above it, reallocation cascades. The project's primary test is whether such a threshold exists in the modeled substrate chain and whether its position is recoverable from regionally measurable parameters (regulatory class, capital-flow structure, edge-research density, grid topology, locality-level demand profile).

The model is **parameterized by region**, not universal. A United States ISO and a Japanese utility operate in structurally different regulatory substrates; the methodology is designed to characterize each in its own terms. This is explicitly a multi-voice model in which voices live across substrates (regulatory, capital, research-edge, grid-operational, locality), not only within one.

### §0.1 — What this project commits to publishing

Within the publication window — currently scoped to the six months following the timestamp of this commit — the project commits to publishing:

- A minimum of three substrate voices added to the registry defined in §3, each one a separately committed predict / kill-condition / run / verdict unit.
- A null-voice ledger in which voices that fail their pre-registered kill conditions remain on the record alongside voices that succeed. The base rate of nulls is expected to be high; the witnessed search is the publication, not any single winning configuration.
- A post-hoc validation pass against a set of pre-named regional exogenous events for which sovereignty-trajectory data is publicly documented. Specific events are pre-committed in §4.
- All measurement artifacts as signed JSON sidecars to the registry entries, machine-readable and timestamped via git.

### §0.2 — What success looks like

Project success at the close of the publication window is defined by the following measurable outcomes:

- At least three voices have landed in the registry with on-record verdicts. Voices that pass their kill condition and voices that fail it both count toward this commitment; what does not count is voices added without a pre-committed kill condition.
- The post-hoc validation pass in §4 has been run against the pre-named historical events, and its results — whether the methodology recovered the qualitative trajectory of those events or did not — have been published.
- At least one independent contributor not affiliated with Eir, Inc. has entered a voice into the registry via the protocol in §6.
- At least one credentialed grid researcher or operator has cited, forked, referenced in publication, or otherwise engaged with the repository in operational documentation.

### §0.3 — What failure looks like

The project pre-commits to recognizing the following as failures of the project, not failures of the substrate. Each is measurable. None is reinterpretable after the fact.

- The voice-failure rate does not materialize. If every voice the project adds passes its kill condition, that is a signal of fishing — kill conditions were not tight enough, or voices were selected after observing outcomes. The project commits to surfacing this if it occurs.
- No independent contributors enter the registry within the publication window. This is a signal that the contribution contract is illegible or unappealing, and the project will revise the contract openly rather than ignore the absence.
- The post-hoc validation pass fails. If the methodology cannot recover the qualitative trajectory of any of the pre-named historical events, that is a null finding for the methodology at the scope investigated. The project will publish the null without re-interpretation.
- No engagement from credentialed grid practitioners or researchers within the publication window. This is a signal that the public-facing presentation has not crossed the language gap to the target audience, and the project will revise its presentation rather than claim quiet success.

### §0.4 — Who this is for

The intended readers of this pre-registration and the surrounding repository are practitioners and researchers in power-grid operations, alternative-energy investment, and computational methodology for either. The register throughout this document is peer addressing peer: project-level commitments stated flatly, with measurable success and failure conditions named in advance. This is not vendor material and is not written to evangelize. Readers who require operator-grade fidelity should consult §1 for the project's pre-registered honesty bounds before evaluating any reported result.

## §1 — Honesty bounds

This section enumerates, in advance and on the record, claims that the project will *not* make, with the reason for each bound. Reviewers and replicators can hold the project accountable to these bounds at any point in the publication window. The bounds are committed at this commit timestamp; expansion (adding bounds) is permitted in subsequent commits; relaxation (removing or weakening bounds) is not.

The project commits to flagging at the surface of any future result — README, registry entry, publication, derived presentation — when a reader would otherwise reasonably infer one of these claims from the result.

| The project will NOT claim | Because |
| :--- | :--- |
| That the flow allocator implemented in the open repository is a DC power-flow solver, an AC power-flow solver, an EMT simulator, a transient-stability simulator, or a protection simulator. | The flow allocator is a heuristic energy allocator. It is the right shape for the methodology's substrate-characterization question but is not numerically interchangeable with grid-engineering production solvers. Naming it as one of those classes adjacent to MATPOWER, PYPOWER, OpenDSS, or GridLAB-D would mislead a reader who recognizes those tools. |
| That the `pypower_adapter_stub` or `pandapower_adapter_stub` voices in the repository delegate to real PYPOWER or pandapower load-flow runs unless the documentation for each voice explicitly states that delegation has been implemented in a specific commit and references the commit hash where delegation became real. | A stub that returns heuristic output is not a real delegation. Mistaking a stub for the real engagement collapses the value of any subsequent verification a reader performs against it. Each voice's adapter status is named in its own docstring and registry entry. |
| That the cross-band coupling coefficient measured in the demonstration meta-simulation (currently +0.832 control↔dynamics correlation) is a measurement of physical grid coupling, or that its magnitude generalizes to any real grid. | The coefficient is the correlation between two simulated voices the project authored. It demonstrates that the project's polyphony pattern detects coupling when coupling exists in a substrate; it does not measure coupling in any grid the project has not built. Future per-voice predict / kill-condition / run / verdict units that operate against real-grid data will be the source of any claim about real-grid coupling. |
| That a cascade result produced by the methodology — the threshold-class cascade investigated in §0, the qualitative trajectory recovered in §4's validation pass, or any aggregate across voices — is a prediction of what the real economy or the real grid will do. | Cascade results are computed under stated modeling assumptions. They are conditional findings of the form: under these voices, under these assumptions, under these substrate parameters, the methodology returns *X*. Reading such a result as a forecast of what the real grid will do without a registered voice that explicitly tests the forecasting claim crosses the bound. |
| That the methodology generalizes across regulatory regions without per-region voice addition. | A United States ISO and a Japanese utility operate under structurally different regulatory substrates. The methodology is designed to characterize each in its own terms via separately committed voices. Region-transferred conclusions without region-specific voices are out of scope for this publication window. |
| That the funding-gap closure for earlier-stage alternative-energy approaches, modeled in §0, is a measurement of any specific company's funding pipeline. | Funding-gap modeling in this repository operates against public bibliometric and grant-record proxies. It does not have visibility into private financing rounds, term sheets, or commitments outside of public record. Results are conditional on the proxies used and are not direct funding-flow measurements. |
| That a low voice-failure rate is a positive signal about the methodology. | A low voice-failure rate is a signal that the project's kill conditions are not tight enough or that voices are being added after observing outcomes. The project commits in §0.3 to surfacing this as a project failure if it occurs. Reviewers should treat a sharp drop in null voices over the publication window as a request for additional auditing, not as a strengthening of confidence. |
| That the closed components of the project's analytical pipeline (`eirmath`, per §6) are required to evaluate any claim made in this pre-registration. | The central question of §0, the substrate-voice methodology of §3, the historical-events validation pass of §4, and the safety-boundary commitments of §5 are evaluable from the open repository alone. Closed components handle proprietary financial and operational-capex modeling against which methodology measurements are interpreted in commercial work; they are not part of this pre-registration's claims. |

The project additionally pre-commits to publishing, at the close of the publication window, a record of any times during the window when a public-facing result was flagged for crossing one of these bounds — by an external reviewer, an internal review pass, or a maintainer — and the action taken in response. The flagging record will be published alongside the failure ledger described in §0.3.

---

## §2 — Publishing shape

The repository's git history is itself the publication, and its commit order is the integrity proof.

| Commit | What it lands | What it proves |
| :---: | :--- | :--- |
| 1 | The instrument: the open-source grid simulator (Apache 2.0), runnable from a fresh clone with `numpy` only. | The tool existed independent of any result. |
| 2 | This pre-registration: project commitments, honesty bounds, kill conditions for each forthcoming voice, falsification conditions for the project itself. | Commitment is timestamped before any result. |
| 3 to *n* | Per-voice predict / kill-condition / run / verdict units. Voices that pass and voices that fail are both committed. | Each voice was committed before it ran, by virtue of the timestamp of its predict step preceding the timestamp of its run step. |
| final | Interpretation: aggregation across voices, the threshold finding (or its absence), and the project's accounting of which §0 success and failure conditions materialized. | Honored — or did not honor — the prior commitments, on the record. |

This shape is designed so that no commit reorders the meaning of any earlier commit. A reader who clones the repository at any commit hash receives the project's state as it existed at that timestamp. The reading order across the publication window is identical to the writing order: commit hashes are reading the past in the order it was committed.

## §3 — Voice-registry protocol

This section pre-commits the project to a single atomic unit for every addition to the substrate chain — a *voice* — and to the protocol by which voices enter, succeed, or fail in the registry. The protocol is designed so that every voice carries its own falsification condition into the registry alongside its prediction. A voice for which a kill condition has not been pre-committed is not a registry entry, regardless of who authored it or what its run output appears to show.

### §3.1 — The per-voice unit

Each voice that enters the registry is committed as a single unit composed of five fields. All five fields are required; a voice missing any one of them is not in the registry.

1. **Voice name** — a unique identifier for the voice within its substrate (for voices within a substrate) or across the substrate chain (for voices linking substrates). The name is fixed at the moment of the predict-step commit and is not revised by subsequent commits.
2. **Predicted residual coupling** — the specific coupling the voice is hypothesized to capture, stated as a numerical or categorical bound. For voices within a substrate, this is the named residual that the voice is claimed to reduce when added. For voices that link substrates, the prediction additionally states the direction of the link (which substrate's output drives the other's input), the predicted magnitude range, and the null direction (the link does not exist or the direction is reversed).
3. **Kill condition** — the specific run outcome that would falsify the prediction. Kill conditions are stated in terms computable from the voice's run output alone, without reference to external interpretation. A voice whose kill condition is not falsifiable from its own run output is not a registry entry.
4. **Run protocol** — the literal invocation that produces the verdict. This includes the source-file path, the entry point, all input parameters, the random seed if the run is stochastic, and any environment specification required for independent reproduction.
5. **Verdict** — the mechanical computation of pass, fail, or partial from the run output against the prediction and kill condition. The verdict is produced by the run protocol itself, not by post-hoc interpretation.

The five-field unit is committed as a signed JSON sidecar to the voice's source file, per §4.1. The sidecar's SHA-256 hash and timestamp establish that the predict, kill-condition, and run-protocol fields preceded the verdict field.

### §3.2 — Two axes for adding voices

Voices enter the registry along two distinct axes. The project pre-commits to the distinction because the audit-defensibility of a voice depends on which axis it occupies.

**Polyphony — voices within a substrate.** A polyphony voice is added when an existing single-voice model of one substrate produces an unexplained residual that the new voice is hypothesized to capture. The justification for adding a polyphony voice is the named residual; a polyphony voice without a named pre-existing residual is out of scope for the registry.

**Coupling — voices linking substrates.** A coupling voice is added when the substrate chain has a gap that no within-substrate addition can close — specifically, when the output of one substrate is hypothesized to drive the input of another. Coupling voices are directional and causal claims; the registry holds them to a stricter pre-commitment than polyphony voices. A coupling voice must pre-register its predicted direction, predicted magnitude range, and the null direction in which the link does not exist. The verdict reports whether the run output is consistent with the predicted direction, consistent with the null, or neither (which is itself a failure to recover any direction and is recorded as such).

### §3.3 — The minimum-coupled-chain principle

The project pre-commits to adding voices only when a named residual or a named substrate gap demands them. Voices are not added to extend coverage of the substrate chain for its own sake. At the close of the publication window, the registry is expected to record both the minimum coupled chain — the set of voices that captured the cascade investigated in §0 — and the larger set of voices that were proposed and tested but did not capture a residual or link a gap.

The honest end state of the registry is not "*N* voices, all of which helped." It is: "*K* voices were committed; *N* captured real residuals or links; *K − N* did not. Here is the minimum coupled chain that carried the cascade from §0 if such a chain was found, and here is everything that was tested and did not."

### §3.4 — Null-voice ledger

Voices that fail their pre-registered kill condition remain in the registry under a separate accounting category — the null-voice ledger — which is part of the publication, not subtracted from it. The null ledger records the voice's five-field unit identically to a passing voice, with the verdict field marked as fail and the run output retained verbatim.

The null ledger is the audit-defense against the forking-paths critique: every framing that was committed and ran is visible alongside the framings that succeeded, with the base rate of failures (failing voices ÷ total voices committed) computable from the registry at any commit hash. A monotonically shrinking unexplained-residual figure across the substrate chain cannot be inferred from a clean published winner alone; it requires the visible record of what did not work, dated before each addition.

### §3.5 — Independent-contributor protocol

A contributor external to the maintainers of this repository may enter a voice into the registry by the same protocol that internal contributors follow. The contributor submits the five-field unit as a pull request to the repository. The predict, kill-condition, and run-protocol fields must be present in the initial commit of the pull request; the verdict field is produced by the run step.

For the contributor's voice to be accepted into the registry, the five-field unit must be complete and the kill condition must be falsifiable from the run output alone. Reviewers do not adjudicate whether the prediction will turn out to be correct; they adjudicate only whether the unit is well-formed and whether the kill condition is genuinely testable. A pull request whose kill condition cannot be evaluated mechanically from the run output is returned to the contributor for revision, not merged into the registry.

A voice whose verdict is fail enters the null ledger; a voice whose verdict is pass enters the kept-voice ledger. Neither verdict affects the contributor's eligibility to submit further voices. The contribution procedure for code and documentation outside the per-voice protocol is documented separately in `CONTRIBUTING.md`.

## §4 — Pre-committed measurements and historical-events validation

This section pre-commits the project to a measurement set. Two classes of measurement are committed in advance: (a) the per-voice measurements that each registry entry produces by virtue of its predict / kill-condition / run / verdict shape; and (b) a separate post-hoc validation pass against a fixed set of historical regional exogenous events. Both classes of measurement are pre-committed in this document, before any voice has been run and before any historical-events run has been performed.

### §4.1 — Per-voice measurements

Each voice that enters the registry under the protocol in §3 produces, by virtue of that protocol, the following pre-committed measurements:

- The voice's prediction — a specific numerical or categorical bound on what the voice will report when run on its specified inputs.
- The voice's kill condition — the result that would falsify the prediction. Kill conditions must be testable from the voice's run output alone, without external reinterpretation.
- The voice's run record — the exact code path executed, including random seeds, input parameters, and any environment specification needed for independent reproduction.
- The voice's verdict — pass, fail, or partial, computed mechanically from the run output against the prediction and kill condition.

Each per-voice measurement is committed to the registry as a signed JSON sidecar to the voice's source file. The sidecar carries a SHA-256 hash of the canonical run output and a timestamp that precedes the run step.

### §4.2 — Post-hoc historical-events validation set

The project pre-commits to running its methodology against three historical regional exogenous events for which sovereignty-trajectory data is publicly documented. The events are selected to triangulate across mechanism shape, geography, and time arc, so that recovery on any one event cannot stand in for recovery on all three.

The three events, named here before the validation runs are performed:

1. **Texas, February 2021 — Uri winter storm and ERCOT grid event.** A physical exogenous shock followed by operator and regulatory response. The substrate chain affected runs from grid-operational impact through locality-level sovereignty consequences and into capital and regulatory substrate responses (winterization mandates, market-design pivots). Public data sources include ERCOT public filings, Public Utility Commission of Texas orders, and Department of Energy post-event analyses.

2. **European Union, May 2022 — REPowerEU plan and post-invasion energy decoupling.** A regulatory and geopolitical exogenous shock followed by continent-scale capital and substrate reallocation. The substrate chain affected runs from regulatory directive through capital flow through research-edge funding into locality-level energy mix (heat pumps, green hydrogen, biomethane). Public data sources include European Commission REPowerEU dashboards, International Energy Agency tracking reports, and member-state public filings.

3. **Japan, March 2011 — Fukushima event and subsequent nuclear-to-renewable substrate restructure.** A hybrid physical and regulatory exogenous shock with an extended observable trajectory across more than a decade. The substrate chain affected runs the full length of the chain modeled in this project — physical event through regulatory pivot (FIT scheme, 2012) through capital flow (solar capex inflection, 2012–2014) through research-edge engagement (offshore wind, hydrogen) into locality-level sovereignty rebalancing (regional utilities versus the TEPCO axis). Public data sources include METI public records, Institute of Energy Economics Japan reports, and Japan Renewable Energy Foundation publications.

### §4.3 — Recovery criteria and the project-level kill condition

Recovery for the post-hoc validation pass is pre-committed to the qualitative-trajectory level, not to point estimates. The methodology recovers an event when its substrate-chain output, fed only public regional parameters at a time stamp before the event, reproduces the documented qualitative trajectory of operator, regulatory, and capital substrate response within the documented window.

The project-level kill condition for the validation pass is pre-committed as follows: if the methodology fails to recover the qualitative trajectory of at least two of the three named events, that constitutes a null finding for the methodology at this scope. The project commits to publishing that null finding, without re-interpreting the events or re-tuning the methodology to fit them after the fact. The pre-registered correction protocol in §5 governs any methodology revision; revisions that follow a null finding are themselves pre-registered as v2 measurements, with v1 left intact on the record.

Additional historical events may be added to the validation set in subsequent passes, but only as additions: the three events named in §4.2 are not removable from the pre-committed set, and any v2 methodology revision is tested against all three before the v2 verdict is published.

## §5 — Deviations and corrections protocol

Pre-registration is the discipline of stating commitments before results are produced. Living with that discipline requires a stated protocol for the case in which a pre-registered measurement turns out to be ill-formed, ill-specified, or otherwise in need of revision after it has been committed. This section pre-commits the project to the protocol it will follow when that happens.

The protocol is designed to distinguish two cases that pre-registration discipline keeps separate. The first is an **analyst error**: the measurement was specified incorrectly by the contributor, in a way that does not depend on the data. The second is a **data property**: the measurement was specified correctly, and the data has produced a result inconsistent with the prediction. Conflating these two cases is the failure mode pre-registration is designed to prevent. The protocol below names them apart at the moment of revision.

### §5.1 — When a pre-registered measurement is found to be incorrectly specified

If a contributor or reviewer determines, after a pre-registered measurement has been committed but before or after it has been run, that the measurement is incorrectly specified — for example, that a formula does not produce the quantity the prediction is about, or that a kill condition does not actually falsify the prediction, or that a fingerprint discretization is too coarse to discriminate the predicted bounds — the following sequence applies.

1. The incorrect specification is named explicitly as an analyst error. The error is documented in a correction note at the top of the measurement file or its sidecar JSON. The correction note states what was wrong, what is being changed, and that the error is a property of the analyst's specification and not a property of the data.
2. A version-2 measurement is pre-registered in the same file or sidecar, alongside the version-1 specification. The version-2 measurement carries its own prediction, kill condition, run protocol, and verdict criteria, all pre-committed in advance of any version-2 run.
3. The version-1 specification is not deleted. It remains on the record, marked as deprecated by the analyst error noted in step 1. Readers can inspect the prior state of the project's commitments at any time by reading the version-1 entry and the correction note that accompanies its deprecation.
4. The version-2 measurement is then run under the same protocol as any other pre-registered measurement. Its verdict is published whether it passes, fails, or is partial.

A working example of this protocol is carried in `examples/ieee_case_demo.py`, where a version-1 cycle-walk specification produced a stability-class verdict that was traceable not to the data but to a formula that did not measure what the prediction was about. The version-2 specification corrects the formula, names the version-1 error explicitly, and reports the version-2 result on the corrected basis. The version-1 specification and its correction note remain in the file as a reference implementation of this protocol.

### §5.2 — When a pre-registered measurement is correctly specified and produces a result inconsistent with the prediction

This is the case the project most wants to find. A correctly specified measurement that fails its kill condition is a null finding, and null findings are the load-bearing output of pre-registration discipline. The protocol for this case is short:

1. The measurement's verdict is recorded as a fail. The fail is added to the null-voice ledger per §3 and §6.
2. No revision of the measurement is performed. The measurement specified what it specified, and the data produced what it produced. Both stand on the record.
3. The contributor or a subsequent contributor may pre-register a different measurement, with its own prediction, kill condition, and verdict criteria. This new measurement is a separate registry entry, not a revision of the failing one. The new entry is dated after the failing entry, by virtue of git timestamping.

The discipline pre-registered here is that a failing measurement is not retroactively revised into a passing one. A new measurement is a new measurement, not a corrected version of an old one, when the original measurement was correctly specified. The version-2 protocol in §5.1 applies only when the original specification was itself in error.

### §5.3 — Boundaries on revision

The project pre-commits to the following revision boundaries.

- Once a measurement has been committed to the registry, its file content cannot be edited in a way that erases its prior state. Corrections are additive, not destructive. The git history is the record.
- The post-hoc historical-events validation set in §4.2 is closed for removal. Additional events may be added in subsequent passes. Removing an event from the validation set after the methodology has been run against it constitutes a project-level discipline violation and would be a §0.3 failure mode.
- A revision to the methodology that follows a null finding — for example, a redesign of a voice's run protocol after the original voice fails — is pre-registered as a version-2 measurement under §5.1, with all three §4.2 events re-run against the version-2 methodology before any version-2 verdict is published.
- A revision that follows a successful measurement is not permitted to claim retroactive credit for the success. If the measurement passes, the measurement passes as committed; subsequent revisions to the methodology start a new measurement, not a continuation of the old one.

### §5.4 — The audit role of the correction note

Every correction made under this protocol carries a correction note, machine-readable, committed to the file or its sidecar. The correction note records the date of the correction, the contributor responsible for the correction, the specific change being made, the analyst-error-vs-data-property determination, and a pointer to the version-1 entry being deprecated. Readers and auditors can reconstruct the full history of the project's commitments and revisions by reading the correction-note trail through the git history.

## §6 — Contribution and governance

External contributors are welcome to add substrate voices, simulator adapters, station-set definitions, and reproducibility tooling under the same Apache 2.0 license as the rest of the repository. The contribution procedure is documented in `CONTRIBUTING.md`.

For the purposes of this pre-registration, a contributor's voice enters the registry if and only if it lands as a complete predict / kill-condition / run / verdict unit per the protocol described in §3. Voices that fail their kill condition are merged into the null-voice ledger and remain part of the record. Voices added without a pre-committed kill condition are not eligible for the registry until the kill condition is committed separately and dated. This rule applies equally to contributions from Eir, Inc. and to contributions from any external party.

Repository governance during the publication window is intentionally minimal. Pull requests are reviewed by repository maintainers listed in `CONTRIBUTORS.md`. Maintainership is not a vendor relationship. Maintainers commit to publishing the failure conditions for the maintenance role itself — if review latency, decision quality, or process transparency degrade in measurable ways during the window — and to surfacing those failures alongside the project's own failure ledger.

This repository carries the open instrument and the methodology. Eir, Inc. maintains a separate proprietary package, `eirmath`, that supplies the closed components of the project's analytical pipeline — specifically the financial-performance and operational-capex modeling components against which the methodology's measurements are interpreted in proprietary work. The open repository is sufficient to validate the methodology's shape and to permit independent replication of the substrate-characterization steps. The proprietary numerical components are not required to evaluate the central question of §0, and are not part of this pre-registration's claims. The interface boundary between the open repository and `eirmath` is documented in the source code at the points where the open and closed components meet.

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

The historical-events validation pass in §4 recovers events at the qualitative-trajectory level, as pre-committed in that section. The methodology does not produce point estimates against the validation events, does not claim numerical agreement with documented post-event measurements, and does not credential itself against any specific production simulation result. Recovery is binary at the qualitative level: the substrate-chain trajectory either reproduces the documented qualitative response within the documented window, or it does not.

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

