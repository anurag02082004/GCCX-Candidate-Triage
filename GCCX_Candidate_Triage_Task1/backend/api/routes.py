from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from services.triage_ai import generate_fit_summary
from services.triage_store import candidate_summary, init_db, list_candidates, update_candidate

router = APIRouter(prefix="/api", tags=["candidate-triage"])


class CandidateUpdateRequest(BaseModel):
    is_shortlisted: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def require_update(self) -> "CandidateUpdateRequest":
        if self.is_shortlisted is None and self.tags is None:
            raise ValueError("Provide is_shortlisted and/or tags")
        if self.tags is not None and any(len(tag) > 60 for tag in self.tags):
            raise ValueError("Each tag must be 60 characters or fewer")
        return self


class FitSummaryRequest(BaseModel):
    job_role: str = Field(default="", max_length=160)


@router.get("/candidates")
def get_triage_candidates(
    search: Annotated[str, Query(max_length=200)] = "",
    role: Annotated[str, Query(max_length=160)] = "",
    source: Annotated[str, Query(max_length=160)] = "",
    min_experience: Annotated[float | None, Query(ge=0, le=80)] = None,
    max_experience: Annotated[float | None, Query(ge=0, le=80)] = None,
    skill: Annotated[str, Query(max_length=100)] = "",
    shortlisted_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    if min_experience is not None and max_experience is not None and min_experience > max_experience:
        raise HTTPException(status_code=422, detail="min_experience cannot exceed max_experience")
    init_db()
    all_matches = list_candidates(search, role, source, min_experience, max_experience, skill, shortlisted_only)
    return {"items": all_matches[offset:offset + limit], "count": len(all_matches), "limit": limit, "offset": offset}


@router.get("/candidate-facets")
def get_candidate_facets() -> dict[str, list[str] | int]:
    init_db()
    items = list_candidates()
    return {
        "roles": sorted({x["target_role"] for x in items if x["target_role"]}),
        "sources": sorted({x["source"] for x in items if x["source"]}),
        "skills": sorted({skill for x in items for skill in x["skills"]}, key=str.casefold),
        "total_candidates": len(items),
        "shortlisted_count": sum(1 for x in items if x["is_shortlisted"]),
    }


@router.patch("/candidates/{candidate_id}")
def patch_triage_candidate(candidate_id: str, payload: CandidateUpdateRequest) -> dict[str, object]:
    init_db()
    updated = update_candidate(candidate_id, payload.is_shortlisted, payload.tags)
    if updated is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated


@router.post("/candidates/{candidate_id}/fit-summary")
def get_fit_summary(candidate_id: str, payload: FitSummaryRequest) -> dict[str, str]:
    init_db()
    candidate = candidate_summary(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return generate_fit_summary(candidate, payload.job_role)
