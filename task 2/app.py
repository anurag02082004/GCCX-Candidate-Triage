
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ranking import rank_candidates


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="GCCX Candidate Ranking Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# LOAD OFFICIAL GCCX CANDIDATE DATA
# --------------------------------------------------

DATA_FILE = (
    Path(__file__).resolve().parent
    / ".."
    / "GCCX_Candidate_Triage_Task1"
    / "backend"
    / "data"
    / "candidates.json"
).resolve()


@st.cache_data
def load_gccx_candidates():
    """Load and validate the original GCCX candidate dataset."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "The GCCX candidate dataset could not be found.\n\n"
            f"Expected file: {DATA_FILE}\n\n"
            "Check that the task 2 folder and "
            "GCCX_Candidate_Triage_Task1 folder are "
            "inside the same parent folder."
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        candidates = json.load(file)

    if not isinstance(candidates, list):
        raise ValueError(
            "The candidates.json file must contain a JSON list."
        )

    if len(candidates) != 48:
        raise ValueError(
            f"Expected 48 original candidates, "
            f"but found {len(candidates)}."
        )

    return candidates


# --------------------------------------------------
# NORMALIZE DATA FOR DISPLAY
# --------------------------------------------------

def normalize_candidate(candidate):
    """Convert a candidate record into a consistent format."""

    skills = candidate.get("skills", [])

    if not isinstance(skills, list):
        skills = []

    skills = [
        str(skill).strip()
        for skill in skills
        if skill is not None and str(skill).strip()
    ]

    try:
        experience = float(candidate.get("years_experience", 0) or 0)
    except (TypeError, ValueError):
        experience = 0.0

    return {
        "id": str(candidate.get("id", "")),
        "name": str(candidate.get("name", "Unknown")),
        "target_role": str(candidate.get("target_role", "Not specified")),
        "years_experience": experience,
        "source": str(candidate.get("source", "Unknown")),
        "skills": skills,
        "notes": str(candidate.get("notes", "")),
        "applied_date": str(candidate.get("applied_date", "")),
    }


# --------------------------------------------------
# MATCHING AND SCORING
# --------------------------------------------------

def calculate_candidate_matches(candidates, required_skills):
    """
    Calculate skill match scores.

    The percentage represents the proportion of selected required
    skills present in a candidate's skill list. It is not a
    prediction of job performance or hiring suitability.
    """

    required = {
        skill.strip().casefold()
        for skill in required_skills
        if isinstance(skill, str) and skill.strip()
    }

    results = []

    for candidate in candidates:
        candidate_skills = {
            skill.strip().casefold()
            for skill in candidate["skills"]
        }

        matched = candidate_skills.intersection(required)
        missing = required.difference(candidate_skills)

        match_count = len(matched)

        if required:
            match_percentage = round(
                match_count / len(required) * 100,
                1,
            )
        else:
            match_percentage = 0.0

        results.append(
            {
                **candidate,
                "matched_skills": sorted(matched),
                "missing_skills": sorted(missing),
                "match_count": match_count,
                "match_percentage": match_percentage,
            }
        )

    return results


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

st.title("🎯 GCCX Candidate Ranking Dashboard")
st.caption(
    "Explore the original candidate dataset, compare required skills, "
    "and prioritize candidates for further review."
)

try:
    raw_candidates = load_gccx_candidates()
    candidates = [
        normalize_candidate(candidate)
        for candidate in raw_candidates
    ]
except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
    st.error("Unable to load the GCCX candidate dataset.")
    st.code(str(error))
    st.stop()


# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("🔎 Candidate Filters")

all_skills = sorted(
    {
        skill
        for candidate in candidates
        for skill in candidate["skills"]
    },
    key=str.casefold,
)

all_roles = sorted(
    {candidate["target_role"] for candidate in candidates},
    key=str.casefold,
)

all_sources = sorted(
    {candidate["source"] for candidate in candidates},
    key=str.casefold,
)

required_skills = st.sidebar.multiselect(
    "Required skills",
    options=all_skills,
    help="Choose skills to calculate candidate match percentages.",
)

selected_roles = st.sidebar.multiselect(
    "Target roles",
    options=all_roles,
    default=all_roles,
)

selected_sources = st.sidebar.multiselect(
    "Application sources",
    options=all_sources,
    default=all_sources,
)

min_experience = st.sidebar.number_input(
    "Minimum years of experience",
    min_value=0.0,
    max_value=50.0,
    value=0.0,
    step=1.0,
)

max_experience = st.sidebar.number_input(
    "Maximum years of experience",
    min_value=0.0,
    max_value=50.0,
    value=50.0,
    step=1.0,
)

candidate_search = st.sidebar.text_input(
    "Search candidates",
    placeholder="Name, skill, ID, or notes...",
)

minimum_match = st.sidebar.slider(
    "Minimum skill match (%)",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
)

sort_option = st.sidebar.selectbox(
    "Sort candidates by",
    options=[
        "Highest skill match",
        "Most matched skills",
        "Most experience",
        "Name A–Z",
        "Most recent application",
    ],
)

st.sidebar.divider()
st.sidebar.caption(
    "Skill matching is rule-based. Review candidate experience "
    "and notes before making hiring decisions."
)


# --------------------------------------------------
# CALCULATE MATCHES FOR ALL CANDIDATES
# --------------------------------------------------

scored_candidates = calculate_candidate_matches(
    candidates,
    required_skills,
)


# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_candidates = []

search_text = candidate_search.strip().casefold()

for candidate in scored_candidates:
    if candidate["target_role"] not in selected_roles:
        continue

    if candidate["source"] not in selected_sources:
        continue

    if not (
        min_experience
        <= candidate["years_experience"]
        <= max_experience
    ):
        continue

    if candidate["match_percentage"] < minimum_match:
        continue

    if search_text:
        searchable_text = " ".join(
            [
                candidate["id"],
                candidate["name"],
                candidate["target_role"],
                candidate["source"],
                candidate["notes"],
                " ".join(candidate["skills"]),
            ]
        ).casefold()

        if search_text not in searchable_text:
            continue

    filtered_candidates.append(candidate)


# --------------------------------------------------
# SORT RESULTS
# --------------------------------------------------

if sort_option == "Highest skill match":
    filtered_candidates.sort(
        key=lambda candidate: (
            -candidate["match_percentage"],
            -candidate["years_experience"],
            candidate["name"].casefold(),
        )
    )

elif sort_option == "Most matched skills":
    filtered_candidates.sort(
        key=lambda candidate: (
            -candidate["match_count"],
            candidate["name"].casefold(),
        )
    )

elif sort_option == "Most experience":
    filtered_candidates.sort(
        key=lambda candidate: (
            -candidate["years_experience"],
            candidate["name"].casefold(),
        )
    )

elif sort_option == "Name A–Z":
    filtered_candidates.sort(
        key=lambda candidate: candidate["name"].casefold()
    )

elif sort_option == "Most recent application":
    filtered_candidates.sort(
        key=lambda candidate: (
            candidate["applied_date"],
            candidate["name"].casefold(),
        ),
        reverse=True,
    )


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

total_candidates = len(candidates)
visible_candidates = len(filtered_candidates)

if required_skills and filtered_candidates:
    average_match = round(
        sum(
            candidate["match_percentage"]
            for candidate in filtered_candidates
        )
        / visible_candidates,
        1,
    )

    top_match = max(
        candidate["match_percentage"]
        for candidate in filtered_candidates
    )
else:
    average_match = 0.0
    top_match = 0.0

candidates_with_matches = sum(
    candidate["match_count"] > 0
    for candidate in filtered_candidates
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Original Candidates",
    total_candidates,
)

kpi2.metric(
    "Candidates After Filters",
    visible_candidates,
)

kpi3.metric(
    "Average Skill Match",
    f"{average_match:.1f}%" if required_skills else "Select skills",
)

kpi4.metric(
    "Candidates With Matches",
    candidates_with_matches if required_skills else "Select skills",
)

st.divider()


# --------------------------------------------------
# TABS
# --------------------------------------------------

tab_rankings, tab_charts, tab_details, tab_data = st.tabs(
    [
        "🏆 Rankings",
        "📊 Analytics",
        "👤 Candidate Details",
        "📁 Dataset",
    ]
)


# --------------------------------------------------
# TAB 1: RANKINGS
# --------------------------------------------------

with tab_rankings:
    st.subheader("Candidate Rankings")

    if not required_skills:
        st.info(
            "Select one or more required skills from the sidebar "
            "to calculate skill-based rankings."
        )

    if not filtered_candidates:
        st.warning(
            "No candidates match the current filters. "
            "Try lowering the minimum match percentage or "
            "changing the selected filters."
        )
    else:
        st.caption(
            f"Showing {visible_candidates} of {total_candidates} "
            "candidates. Ranking uses exact, case-insensitive "
            "skill-name matching."
        )

        ranking_rows = []

        for rank, candidate in enumerate(filtered_candidates, start=1):
            ranking_rows.append(
                {
                    "Rank": rank,
                    "Candidate ID": candidate["id"],
                    "Name": candidate["name"],
                    "Target Role": candidate["target_role"],
                    "Experience (Years)": candidate["years_experience"],
                    "Match (%)": candidate["match_percentage"],
                    "Matched Skills": ", ".join(
                        candidate["matched_skills"]
                    ),
                    "Missing Skills": ", ".join(
                        candidate["missing_skills"]
                    ),
                    "Source": candidate["source"],
                    "Applied Date": candidate["applied_date"],
                }
            )

        ranking_df = pd.DataFrame(ranking_rows)

        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Match (%)": st.column_config.ProgressColumn(
                    "Match (%)",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
                "Experience (Years)": st.column_config.NumberColumn(
                    "Experience (Years)",
                    format="%.1f",
                ),
            },
        )

        csv_data = ranking_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Rankings as CSV",
            data=csv_data,
            file_name="gccx_candidate_rankings.csv",
            mime="text/csv",
        )


# --------------------------------------------------
# TAB 2: ANALYTICS
# --------------------------------------------------

with tab_charts:
    st.subheader("Candidate Analytics")

    if not filtered_candidates:
        st.info("No candidates are available for analytics.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Candidates by Target Role**")

            role_counts = (
                pd.DataFrame(filtered_candidates)
                ["target_role"]
                .value_counts()
                .rename_axis("Target Role")
                .reset_index(name="Candidates")
            )

            st.bar_chart(
                role_counts.set_index("Target Role")
            )

        with chart_col2:
            st.markdown("**Candidates by Application Source**")

            source_counts = (
                pd.DataFrame(filtered_candidates)
                ["source"]
                .value_counts()
                .rename_axis("Source")
                .reset_index(name="Candidates")
            )

            st.bar_chart(
                source_counts.set_index("Source")
            )

        st.markdown("**Experience Distribution**")

        experience_df = pd.DataFrame(
            {
                "Experience (Years)": [
                    candidate["years_experience"]
                    for candidate in filtered_candidates
                ]
            }
        )

        st.bar_chart(
            experience_df["Experience (Years)"]
            .value_counts()
            .sort_index()
        )

        if required_skills:
            st.markdown("**Top Candidate Skill Matches**")

            top_candidates = filtered_candidates[:10]

            match_chart_df = pd.DataFrame(
                {
                    "Candidate": [
                        candidate["name"]
                        for candidate in top_candidates
                    ],
                    "Match (%)": [
                        candidate["match_percentage"]
                        for candidate in top_candidates
                    ],
                }
            )

            st.bar_chart(
                match_chart_df.set_index("Candidate")
            )


# --------------------------------------------------
# TAB 3: CANDIDATE DETAILS
# --------------------------------------------------

with tab_details:
    st.subheader("Candidate Profile")

    if not filtered_candidates:
        st.info("No candidates are available to display.")
    else:
        candidate_options = {
            (
                f'{candidate["name"]} '
                f'({candidate["id"]})'
            ): candidate
            for candidate in filtered_candidates
        }

        selected_candidate_label = st.selectbox(
            "Choose a candidate",
            options=list(candidate_options.keys()),
        )

        selected_candidate = candidate_options[
            selected_candidate_label
        ]

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("#### Basic Information")
            st.write("**Candidate ID:**", selected_candidate["id"])
            st.write("**Name:**", selected_candidate["name"])
            st.write("**Target Role:**", selected_candidate["target_role"])
            st.write(
                "**Experience:**",
                f'{selected_candidate["years_experience"]:g} years',
            )
            st.write("**Application Source:**", selected_candidate["source"])
            st.write("**Applied Date:**", selected_candidate["applied_date"])

        with right_col:
            st.markdown("#### Skill Match")

            if required_skills:
                st.metric(
                    "Required Skill Match",
                    f'{selected_candidate["match_percentage"]:.1f}%',
                )

                st.progress(
                    selected_candidate["match_percentage"] / 100
                )

                st.write(
                    "**Matched skills:**",
                    ", ".join(selected_candidate["matched_skills"])
                    or "None",
                )

                st.write(
                    "**Missing skills:**",
                    ", ".join(selected_candidate["missing_skills"])
                    or "None",
                )
            else:
                st.info(
                    "Select required skills in the sidebar "
                    "to calculate this candidate's match."
                )

        st.markdown("#### Candidate Skills")

        if selected_candidate["skills"]:
            st.write(", ".join(selected_candidate["skills"]))
        else:
            st.write("No skills listed.")

        st.markdown("#### Original Candidate Notes")

        st.write(
            selected_candidate["notes"]
            or "No notes available."
        )


# --------------------------------------------------
# TAB 4: ORIGINAL DATASET
# --------------------------------------------------

with tab_data:
    st.subheader("Original GCCX Candidate Dataset")

    st.write(
        "This view displays the candidate records loaded from "
        "`candidates.json`. The original dataset is not modified."
    )

    original_df = pd.DataFrame(candidates)

    display_df = original_df.copy()
    display_df["skills"] = display_df["skills"].apply(
        lambda skills: ", ".join(skills)
        if isinstance(skills, list)
        else ""
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    original_csv = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Original Dataset as CSV",
        data=original_csv,
        file_name="gccx_original_candidates.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "GCCX Candidate Ranking Dashboard | "
    "Rule-based skill matching | "
    "Use results as decision support, not as an automated hiring decision."
)
