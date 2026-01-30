# Diamond (<>) Roadmap v0.1
# This roadmap encodes major phases, milestones, and workstreams
# required to deliver a production-ready implementation of the Diamond language.

type Quarter = String where:
    regex "^[0-9]{4}-Q[1-4]$"
    prompt "Represent calendar quarters as YYYY-Q# (e.g., 2025-Q1)."

type WorkstreamTag = String where:
    regex "^[A-Z]{2,8}$"
    prompt "Use concise uppercase identifiers such as LANG, RUNTIME, SECURITY."

type MilestoneStatus = String where:
    enum ["Planned", "InFlight", "Complete"]
    prompt "Choose one of Planned, InFlight, or Complete."

struct SemanticVersion:
    major: Int
    minor: Int
    patch: Int = 0

struct Workstream:
    tag: WorkstreamTag
    name: String
    description: String
    leads: List[String]
    dependencies: List[WorkstreamTag] = []
    notes: List[String] = []

struct Milestone:
    id: String where:
        regex "^MS-[0-9]{3}$"
        prompt "Milestone IDs must follow the pattern MS-###."
    title: String
    description: String
    owner: WorkstreamTag
    quarter: Quarter
    status: MilestoneStatus = "Planned"
    dependencies: List[String] = []
    deliverables: List[String] = []
    acceptance: List[String] = []

struct Phase:
    code: String where:
        regex "^PH-[0-9]{2}$"
    name: String
    start: Quarter
    end: Quarter
    intent: String
    milestones: List[Milestone] = []
    risks: List[String] = []
    mitigation: List[String] = []

struct Roadmap:
    version: SemanticVersion
    updated_at: String
    vision: String
    principles: List[String]
    workstreams: List[Workstream]
    phases: List[Phase]
    notes: List[String] = []

const ROADMAP_VERSION: SemanticVersion = SemanticVersion(
    major = 0,
    minor = 1,
    patch = 0
)

const PRIMARY_WORKSTREAMS: List[Workstream] = [
    Workstream(
        tag = "LANG",
        name = "Language Specification",
        description = "Define grammar, typing rules, semantic refinements, and canonical examples.",
        leads = ["Specification WG"],
        dependencies = [],
        notes = [
            "Owns docs/spec grammar, types, effects, and roadmap evolution.",
            "Partners with SECURITY for semantic refinement guardrails."
        ]
    ),
    Workstream(
        tag = "COMP",
        name = "Compiler Toolchain",
        description = "Implement parser, analyzer, HIR, Wasm component backend, and CLI.",
        leads = ["Compiler WG"],
        dependencies = ["LANG"],
        notes = [
            "Emit capability manifests and constrained decoding metadata.",
            "Provide language server diagnostics via shared libraries."
        ]
    ),
    Workstream(
        tag = "RUNTIME",
        name = "Runtime & Effects",
        description = "Deliver Wasm host, effect dispatcher, continuation persistence, and supervisor APIs.",
        leads = ["Runtime WG"],
        dependencies = ["COMP", "SEC"],
        notes = [
            "Integrates decision engine and prompt router.",
            "Implements capability enforcement in accordance with security specs."
        ]
    ),
    Workstream(
        tag = "SEC",
        name = "Security & OCap",
        description = "Define capability schemas, threat models, and verification tooling.",
        leads = ["Security WG"],
        dependencies = ["LANG"],
        notes = [
            "Maintains docs/security playbooks and incident response procedures.",
            "Validates Gem registry provenance and capability attenuation."
        ]
    ),
    Workstream(
        tag = "ML",
        name = "Synthetic Bootstrapping & Models",
        description = "Generate Diamond corpus, run LLM evolution loops, and fine-tune authoring models.",
        leads = ["ML Enablement WG"],
        dependencies = ["LANG", "COMP"],
        notes = [
            "Coordinates with TOOLING for transpiler and verifier suites.",
            "Publishes benchmark harnesses for compilation and semantic accuracy."
        ]
    ),
    Workstream(
        tag = "TOOLING",
        name = "Developer Tooling & UX",
        description = "Provide language server, prompt packs, transpiler, and CLI ergonomics.",
        leads = ["Developer Experience WG"],
        dependencies = ["COMP", "RUNTIME"],
        notes = [
            "Ensures examples/ and docs/ stay in sync with tooling capabilities.",
            "Owns onboarding scripts and playground experiences."
        ]
    )
]

const PHASES: List[Phase] = [
    Phase(
        code = "PH-00",
        name = "Specification Freeze",
        start = "2024-Q4",
        end = "2025-Q1",
        intent = "Lock core language semantics, security posture, and runtime contracts to unblock implementation.",
        milestones = [
            Milestone(
                id = "MS-001",
                title = "Grammar & Typing Sign-off",
                description = "Publish docs/spec grammar, types, and effects with RFC approval from LANG & SEC.",
                owner = "LANG",
                quarter = "2024-Q4",
                deliverables = [
                    "docs/spec/grammar.md tracked with regression tests",
                    "docs/spec/types.md with structural + semantic refinement examples"
                ],
                acceptance = [
                    "Compiler front-end prototype parses canonical corpus without errors",
                    "Security review confirms semantic refinement hooks"
                ]
            ),
            Milestone(
                id = "MS-002",
                title = "Capability Security Baseline",
                description = "Document OCap policies, threat model, and capability manifests for core stdlib.",
                owner = "SEC",
                quarter = "2024-Q4",
                dependencies = ["MS-001"],
                deliverables = [
                    "docs/spec/capabilities.md v1.0",
                    "docs/security/threat-model.md initial publication"
                ],
                acceptance = [
                    "Security WG sign-off with recorded meeting notes",
                    "No open critical findings in red-team dry run"
                ]
            ),
            Milestone(
                id = "MS-003",
                title = "Runtime Contract Definition",
                description = "Finalize effect dispatcher, continuation format, and Wasm ABI in docs/spec/runtime.md.",
                owner = "RUNTIME",
                quarter = "2025-Q1",
                dependencies = ["MS-001", "MS-002"],
                deliverables = [
                    "docs/spec/runtime.md with continuation serialization appendix",
                    "docs/spec/effects.md cross-referenced with runtime behaviors"
                ],
                acceptance = [
                    "Prototype effect harness passes suspension/resume fixture suite",
                    "Compatibility tests confirm ABI stability across sample modules"
                ]
            )
        ],
        risks = [
            "Scope creep in specification documents delaying downstream workstreams."
        ],
        mitigation = [
            "Enforce RFC timeboxes and weekly WG syncs.",
            "Escalate unresolved design disputes to governance council within 72 hours."
        ]
    ),
    Phase(
        code = "PH-01",
        name = "Compiler & Tooling Foundations",
        start = "2025-Q1",
        end = "2025-Q2",
        intent = "Stand up the reference compiler, language server, and transpiler to support corpus generation.",
        milestones = [
            Milestone(
                id = "MS-004",
                title = "Front-End Completion",
                description = "Deliver parser, symbol resolution, and effect-aware type checker with golden tests.",
                owner = "COMP",
                quarter = "2025-Q1",
                dependencies = ["MS-001"],
                status = "InFlight",
                deliverables = [
                    "packages/compiler/crates/frontend with 95% coverage on regression suite",
                    "packages/compiler/tests syntax + effect conformance harness"
                ],
                acceptance = [
                    "Nightly build compiles canonical examples without regressions",
                    "LSP integration provides diagnostics for 90% of intentional errors"
                ]
            ),
            Milestone(
                id = "MS-005",
                title = "Wasm Component Backend",
                description = "Emit capability-scoped Wasm components with constrained decoding metadata.",
                owner = "COMP",
                quarter = "2025-Q2",
                dependencies = ["MS-004", "MS-003"],
                deliverables = [
                    "packages/compiler/crates/backend generating WIT interfaces",
                    "Integration tests running compiled modules via runtime host"
                ],
                acceptance = [
                    "Runtime executes compiled artifacts across Linux/macOS without sandbox violations",
                    "Capability manifest verifier passes for stdlib smoke tests"
                ]
            ),
            Milestone(
                id = "MS-006",
                title = "Tooling Bootstrap",
                description = "Release alpha language server, formatter, and Python→Diamond transpiler.",
                owner = "TOOLING",
                quarter = "2025-Q2",
                dependencies = ["MS-004"],
                deliverables = [
                    "packages/language-server alpha release notes",
                    "packages/tooling/transpiler CLI with AST parity validation"
                ],
                acceptance = [
                    "Developers can edit examples with live diagnostics",
                    "Transpiler generates compilable Diamond for ≥70% of curated Python set"
                ]
            )
        ],
        risks = [
            "Compiler performance regressions slowing developer feedback.",
            "Transpiler hallucinations introducing insecure capability usage."
        ],
        mitigation = [
            "Introduce CI performance budgets and profiling gates.",
            "Integrate security lint into transpiler pipeline with automated rejection."
        ]
    ),
    Phase(
        code = "PH-02",
        name = "Runtime Durability & Security Hardening",
        start = "2025-Q2",
        end = "2025-Q3",
        intent = "Productionize runtime durability, continuation storage, and zero-trust enforcement.",
        milestones = [
            Milestone(
                id = "MS-007",
                title = "Continuation Store GA",
                description = "Implement hot/warm/cold tiers with cryptographic signing and resumption APIs.",
                owner = "RUNTIME",
                quarter = "2025-Q2",
                dependencies = ["MS-005"],
                deliverables = [
                    "packages/runtime/continuations persistent backends",
                    "docs/security/continuation-hardening.md playbook"
                ],
                acceptance = [
                    "Fault-injection tests resume 99% of continuations within SLA",
                    "No unsigned continuation accepted during security audits"
                ]
            ),
            Milestone(
                id = "MS-008",
                title = "Decision & Prompt Engine Integration",
                description = "Ship embedding-backed decision engine and constrained prompt router.",
                owner = "RUNTIME",
                quarter = "2025-Q3",
                dependencies = ["MS-006"],
                deliverables = [
                    "Runtime decision engine module with caching",
                    "Prompt router supporting grammar masks + verifier hooks"
                ],
                acceptance = [
                    "Decision operator passes semantic routing benchmark >90% accuracy",
                    "Prompt executions achieve <1% malformed output in stress tests"
                ]
            ),
            Milestone(
                id = "MS-009",
                title = "Security Validation Suite",
                description = "Automate capability fuzzing, prompt-injection tests, and Gem registry provenance checks.",
                owner = "SEC",
                quarter = "2025-Q3",
                dependencies = ["MS-007", "MS-008"],
                deliverables = [
                    "docs/security/red-team-playbook.md with tooling references",
                    "CI pipeline running security suite on every merge"
                ],
                acceptance = [
                    "Zero critical vulnerabilities outstanding before runtime beta release",
                    "Audit log coverage meets transparency policy"
                ]
            )
        ],
        risks = [
            "Continuation encryption impacting resumption latency.",
            "External model dependencies introducing availability risks."
        ],
        mitigation = [
            "Benchmark encryption overhead and cache decrypted segments securely.",
            "Provide on-prem SLM fallback and circuit breakers for external endpoints."
        ]
    ),
    Phase(
        code = "PH-03",
        name = "Ecosystem & Model Enablement",
        start = "2025-Q3",
        end = "2025-Q4",
        intent = "Finalize synthetic corpus, fine-tuned models, standard library batteries, and public release collateral.",
        milestones = [
            Milestone(
                id = "MS-010",
                title = "Synthetic Corpus GA",
                description = "Publish validated Diamond corpus with lineage metadata and licensing.",
                owner = "ML",
                quarter = "2025-Q3",
                dependencies = ["MS-006"],
                deliverables = [
                    "docs/bootstrapping/README.md updated with corpus release process",
                    "Release artifacts stored with checksums and provenance manifests"
                ],
                acceptance = [
                    "Compilation success ≥95% across nightly builds",
                    "Semantic drift ≤2% relative to source Python suites"
                ]
            ),
            Milestone(
                id = "MS-011",
                title = "Diamond-Llama Release",
                description = "Fine-tune instruction model for Diamond authoring with evaluation benchmarks.",
                owner = "ML",
                quarter = "2025-Q4",
                dependencies = ["MS-010"],
                deliverables = [
                    "Model card with bias & safety analysis",
                    "Benchmark report covering compile rate, task success, and security compliance"
                ],
                acceptance = [
                    "Model achieves ≥80% compile rate and ≥60% task success on curated suite",
                    "Security review signs off on prompt-injection resilience"
                ]
            ),
            Milestone(
                id = "MS-012",
                title = "Public Beta Launch",
                description = "Release documentation, examples, Gem registry, and onboarding tooling to community.",
                owner = "TOOLING",
                quarter = "2025-Q4",
                dependencies = ["MS-005", "MS-009", "MS-011"],
                deliverables = [
                    "docs/spec/ overview updated with stable APIs",
                    "examples/ directory populated with production-ready blueprints",
                    "Gem registry deployed with signing infrastructure"
                ],
                acceptance = [
                    "Community contributors complete onboarding within defined UX goals",
                    "Incident response runbook tested via tabletop exercise"
                ]
            )
        ],
        risks = [
            "Model release delayed due to safety concerns.",
            "Documentation drift as code stabilizes."
        ],
        mitigation = [
            "Institute safety review gates with fallback to restricted access release.",
            "Adopt docs freeze prior to beta launch with dedicated review squad."
        ]
    )
]

let DIAMOND_ROADMAP: Roadmap = Roadmap(
    version = ROADMAP_VERSION,
    updated_at = "2024-10-01",
    vision = "Deliver a diamond-hard agentic language that fuses probabilistic reasoning with deterministic execution.",
    principles = [
        "Goldilocks ergonomics for LLMs and human maintainers.",
        "Security by construction via object capabilities and Wasm sandboxing.",
        "Durable execution through algebraic effects and resumable continuations.",
        "Evidence-based evolution grounded in benchmarks and formal review."
    ],
    workstreams = PRIMARY_WORKSTREAMS,
    phases = PHASES,
    notes = [
        "Roadmap will be reviewed quarterly; updates require accepted design decisions.",
        "Milestone IDs map to tracking issues in the governance repository."
    ]
)

func active_milestones(roadmap: Roadmap, target_status: MilestoneStatus) -> List[Milestone]:
    return roadmap.phases
        .flat_map(phase -> phase.milestones)
        .filter(m -> m.status == target_status)

func roadmap_summary(roadmap: Roadmap) -> String:
    let planned = active_milestones(roadmap, "Planned").count()
    let inflight = active_milestones(roadmap, "InFlight").count()
    let complete = active_milestones(roadmap, "Complete").count()

    return """
        Diamond Roadmap v{roadmap.version.major}.{roadmap.version.minor}.{roadmap.version.patch}
        Planned: {planned}, In-Flight: {inflight}, Complete: {complete}
        Phases: {roadmap.phases.count()}
    """
