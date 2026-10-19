
from typing import Any


def rank_candidates(
    candidates: list[dict[str, Any]],
    required_skills: list[str],
) -> list[dict[str, Any]]:
    """Rank candidates by required-skill coverage."""

    required = {
        skill.strip().casefold()
        for skill in required_skills
        if isinstance(skill, str) and skill.strip()
    }

    if not required:
        return []

    ranked = []

    for candidate in candidates:
        raw_skills = candidate.get("skills", [])

        if not isinstance(raw_skills, (list, tuple, set)):
            raw_skills = []

        candidate_skills = {
            skill.strip().casefold()
            for skill in raw_skills
            if isinstance(skill, str) and skill.strip()
        }

        matched_skills = candidate_skills & required
        score = len(matched_skills)

        if score > 0:
            ranked.append({
                "name": str(candidate.get("name", "Unknown")),
                "score": score,
                "matched_skills": sorted(matched_skills),
                "match_percentage": round(
                    score / len(required) * 100, 1
                ),
            })

    ranked.sort(
        key=lambda item: (
            -item["score"],
            item["name"].casefold(),
        )
    )

    return ranked
