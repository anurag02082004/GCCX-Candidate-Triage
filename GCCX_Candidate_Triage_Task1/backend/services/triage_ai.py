
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
)

# Always load the .env file located inside the backend folder.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
).strip()

PLACEHOLDER_KEYS = {
    "",
    "replace_with_your_own_key",
    "your_groq_api_key_here",
    "your_api_key_here",
}


def generate_fit_summary(
    candidate: dict[str, Any],
    job_role: str = "",
) -> dict[str, str]:
    """
    Generate an evidence-based candidate-fit summary using Groq.

    Returns:
        {
            "summary": "...",
            "provider": "groq",
            "message": ""
        }
    """

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    # Validate configuration without exposing the secret key.
    if api_key.lower() in PLACEHOLDER_KEYS:
        return {
            "summary": "",
            "provider": "not_configured",
            "message": (
                "Groq API key is missing. Add a valid GROQ_API_KEY "
                "to backend/.env."
            ),
        }

    if not GROQ_MODEL:
        return {
            "summary": "",
            "provider": "not_configured",
            "message": "GROQ_MODEL is empty. Configure it in backend/.env.",
        }

    # Normalize candidate fields before building the prompt.
    skills = candidate.get("skills", [])

    if isinstance(skills, str):
        skills_text = skills
    elif isinstance(skills, (list, tuple, set)):
        skills_text = ", ".join(str(skill) for skill in skills)
    else:
        skills_text = str(skills) if skills else "Not provided"

    name = str(candidate.get("name") or "Not provided")
    target_role = str(candidate.get("target_role") or "Not provided")
    experience = candidate.get("years_experience", "Not provided")
    notes = str(candidate.get("notes") or "Not provided")
    role = job_role.strip() or target_role

    prompt = f"""
Prepare a concise candidate-fit summary for a recruiter.

Candidate evidence:
- Name: {name}
- Target role: {target_role}
- Experience in years: {experience}
- Skills: {skills_text}
- Recruiter notes: {notes}

Role being evaluated: {role}

Requirements:
1. Write 2-4 concise sentences.
2. Explain which listed skills or experience relate to the role.
3. Mention a relevant area to verify during an interview, if appropriate.
4. Use only the evidence supplied above.
5. Do not invent qualifications or experience.
6. Do not infer protected personal characteristics.
7. Do not make the final hiring decision.
8. If evidence is limited, clearly state that limitation.

Return only the summary text, without a heading or markdown.
""".strip()

    try:
        client = Groq(
            api_key=api_key,
            timeout=45.0,
            max_retries=1,
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful recruiting assistant. "
                        "Summarize candidate evidence accurately and "
                        "concisely. Never invent facts or make hiring "
                        "decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_completion_tokens=600,
        )

        # Check the response structure before reading its text.
        if not response.choices:
            print("Groq returned no choices.")
            return {
                "summary": "",
                "provider": "error",
                "message": (
                    "Groq returned no response choices. "
                    "Check the model and try again."
                ),
            }

        choice = response.choices[0]
        message = choice.message
        summary = (message.content or "").strip()

        # Safe diagnostic information; never print the API key.
        print("Groq model:", response.model)
        print("Groq finish reason:", choice.finish_reason)
        print("Groq content present:", bool(summary))

        if not summary:
            if choice.finish_reason == "length":
                error_message = (
                    "Groq reached its token limit before producing "
                    "a text summary. Try increasing the completion "
                    "token limit or using a different model."
                )
            elif getattr(message, "refusal", None):
                error_message = (
                    "Groq declined to generate the summary. "
                    "Review the request and try again."
                )
            else:
                error_message = (
                    "Groq returned no summary text. Check the backend "
                    "terminal for the finish reason and model details."
                )

            return {
                "summary": "",
                "provider": "error",
                "message": error_message,
            }

        return {
            "summary": summary,
            "provider": "groq",
            "message": "",
        }

    except APITimeoutError:
        return {
            "summary": "",
            "provider": "error",
            "message": "Groq timed out. Please retry shortly.",
        }

    except APIConnectionError:
        return {
            "summary": "",
            "provider": "error",
            "message": (
                "Could not connect to Groq. Check your internet connection."
            ),
        }

    except APIStatusError as exc:
        status = exc.status_code

        # Log only the HTTP status, never secrets or request headers.
        print("Groq HTTP status:", status)

        if status in (401, 403):
            error_message = (
                "Groq rejected the API key or access. "
                "Check the key and account permissions."
            )
        elif status == 404:
            error_message = (
                f"Groq model '{GROQ_MODEL}' was not found or is unavailable. "
                "Verify the model ID in your Groq Console."
            )
        elif status == 429:
            error_message = (
                "Groq rate limit or quota reached. "
                "Check your account limits and retry later."
            )
        elif status >= 500:
            error_message = (
                "Groq is temporarily experiencing a server issue. "
                "Please retry shortly."
            )
        else:
            error_message = (
                f"Groq returned HTTP {status}. "
                "Check the model and request configuration."
            )

        return {
            "summary": "",
            "provider": "error",
            "message": error_message,
        }

    except (IndexError, AttributeError, TypeError, ValueError) as exc:
        # Log the exception type only, avoiding accidental secret exposure.
        print("Groq response parsing error:", type(exc).__name__)

        return {
            "summary": "",
            "provider": "error",
            "message": (
                "Groq returned an unexpected response. "
                "Check the backend terminal for diagnostic details."
            ),
        }

    except Exception as exc:
        # Keep the API usable while logging a limited diagnostic.
        print("Unexpected Groq integration error:", type(exc).__name__)

        return {
            "summary": "",
            "provider": "error",
            "message": (
                "An unexpected error occurred while generating the summary. "
                "Check the backend terminal."
            ),
        }
