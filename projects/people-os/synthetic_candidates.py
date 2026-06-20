"""Portfolio excerpt, adapted. Synthetic candidate generator for evals.

Real hiring data is PII-sensitive. Synthetic profiles with known labels let us
score evals automatically and hand-pick edge cases (e.g. non-traditional
backgrounds) instead of waiting for them to show up; a fixed seed reproduces the
same dataset across runs.

The building blocks below are scaffolding; real label thresholds and rubric
mappings are not part of this excerpt.
"""

import random
from dataclasses import dataclass, field


@dataclass
class SyntheticCandidate:
    """A generated candidate carrying ground-truth labels for eval scoring."""
    id: str
    name: str
    resume_text: str
    expected_decision: str  # "recommend" | "maybe" | "reject"
    expected_scores: dict[str, int]  # dimension -> 1..5
    tags: list[str] = field(default_factory=list)  # e.g. ["non-traditional"]


COMPANY_TIERS = {
    "strong": ["BigTech A", "BigTech B", "AI Lab C"],
    "mid": ["Scaleup D", "Scaleup E"],
    "weak": ["Local Agency", "Freelance", "University Lab"],
}

ROLE_SKILLS = {
    "must_have": ["Python", "TypeScript", "React", "LLM integration"],
    "nice_to_have": ["MCP", "LangChain", "evals"],
    "unrelated": ["VHDL", "COBOL", "Fortran"],
}

EXPERIENCE_TEMPLATES = {
    "strong": (
        "Senior Software Engineer at {company} (4 yrs). Shipped LLM-native "
        "internal tooling to hundreds of users. Stack: Python, TypeScript, React."
    ),
    "borderline": (
        "Software Engineer at {company} (2 yrs). Full-stack with React and a "
        "backend framework; some exposure to model serving."
    ),
    "weak": (
        "Junior Developer at {company} (1 yr). Maintained an existing codebase "
        "and fixed bugs; limited independent feature work."
    ),
    "non_traditional": (
        "Career changer from {prev_field}. Self-taught with {n_projects} GitHub "
        "projects. Strong problem-solving from a prior career. Skills: {skills}."
    ),
}

# category, ground-truth decision, score range, fraction of dataset
DISTRIBUTION_PLAN = [
    ("strong", "recommend", (4, 5), 0.30),
    ("borderline", "maybe", (2, 4), 0.30),
    ("weak", "reject", (1, 2), 0.25),
    ("non_traditional", "maybe", (2, 4), 0.15),
]

FIRST_NAMES = ["Alice", "Bob", "Clara", "David", "Elena", "Farid", "Grace",
               "Hiro", "Ines", "James", "Keiko", "Maya", "Noah", "Priya"]
LAST_NAMES = ["Johnson", "Martinez", "Wei", "Park", "Rossi", "Shah",
              "Tanaka", "Santos", "Kim", "Patel", "Garcia", "Chen"]


def _build_distribution(n: int) -> list[tuple[str, str, tuple[int, int]]]:
    """Allocate n candidates across categories per DISTRIBUTION_PLAN."""
    slots: list[tuple[str, str, tuple[int, int]]] = []
    for category, decision, score_range, share in DISTRIBUTION_PLAN:
        slots += [(category, decision, score_range)] * int(n * share)
    return slots


def _render_resume(name: str, category: str, company: str, rng: random.Random) -> str:
    """Assemble a resume for the given category and source company."""
    if category == "non_traditional":
        body = EXPERIENCE_TEMPLATES["non_traditional"].format(
            prev_field=rng.choice(["finance", "teaching", "mechanical eng"]),
            n_projects=rng.randint(3, 8),
            skills=", ".join(rng.sample(ROLE_SKILLS["must_have"], 2)),
        )
    else:
        body = EXPERIENCE_TEMPLATES[category].format(company=company)
    return (
        f"{name}\n"
        f"Email: {name.lower().replace(' ', '.')}@example.com\n\n"
        f"## Experience\n{body}\n"
    )


def generate_dataset(n_candidates: int = 30, seed: int = 42) -> list[SyntheticCandidate]:
    """Return a stratified, reproducible set of labeled candidates.

    Same seed always yields the same dataset.
    """
    rng = random.Random(seed)
    plan = _build_distribution(n_candidates)
    rng.shuffle(plan)

    candidates: list[SyntheticCandidate] = []
    for i, (category, decision, score_range) in enumerate(plan[:n_candidates]):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        tier = "strong" if category == "strong" else (
            "mid" if category == "borderline" else "weak"
        )
        company = rng.choice(COMPANY_TIERS[tier])
        scores = {s: rng.randint(*score_range) for s in ROLE_SKILLS["must_have"]}
        tags = ["non-traditional", "career-changer"] if category == "non_traditional" else []

        candidates.append(SyntheticCandidate(
            id=f"synth_{i:03d}",
            name=name,
            resume_text=_render_resume(name, category, company, rng),
            expected_decision=decision,
            expected_scores=scores,
            tags=tags,
        ))
    return candidates


DATASET = generate_dataset(n_candidates=30, seed=42)
