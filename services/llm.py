import json
import os
import re

from langchain_google_genai import ChatGoogleGenerativeAI


def _llm():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY or GEMINI_API_KEY is missing."
        )

    return ChatGoogleGenerativeAI(
        model=os.getenv(
            "GEMMA_MODEL",
            "gemma-4-26b-a4b-it"
        ),
        google_api_key=key,
        temperature=0.1,
        max_tokens=1600,
    )


def _clean_json_text(text):
    """
    Remove accidental markdown code fences from model output.
    """

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def _normalize_result(data):
    """
    Make sure the LLM response always has the expected structure.
    """

    if not isinstance(data, dict):
        return {
            "answer": str(data),
            "status": "unknown",
            "key_information": [],
            "steps": [],
            "important_notes": [],
        }

    return {
        "answer": str(data.get("answer", "")).strip(),
        "status": data.get("status", "unknown"),
        "key_information": (
            data.get("key_information", [])
            if isinstance(data.get("key_information", []), list)
            else []
        ),
        "steps": (
            data.get("steps", [])
            if isinstance(data.get("steps", []), list)
            else []
        ),
        "important_notes": (
            data.get("important_notes", [])
            if isinstance(data.get("important_notes", []), list)
            else []
        ),
    }


def answer_with_gemma(
    question,
    university,
    context,
    sources
):
    """
    Generate a structured, evidence-grounded answer.
    """

    source_blocks = []

    for i, source in enumerate(sources[:8], 1):

        source_blocks.append(
            f"""
SOURCE {i}
Tier: {source.get("tier", "Unknown")}
Officially verified: {source.get("is_valid_official", False)}
Title: {source.get("title", "")}
URL: {source.get("url", "")}
Detected date: {source.get("published_date") or "Not detected"}

Search snippet:
{source.get("snippet", "")}

Extracted page content:
{source.get("content", "")[:7000]}
"""
        )

    if source_blocks:
        evidence = "\n\n".join(source_blocks)
    else:
        evidence = "NO VALID OFFICIAL SOURCES FOUND."

    prompt = f"""
You are CampusSolve AI, a university information assistant.

Your job is to answer university-related questions using ONLY the
verified evidence provided below.

UNIVERSITY
Name: {university.get("name", "")}
Official domain: {university.get("domain", "")}

USER CONTEXT
{context}

USER QUESTION
{question}

VERIFIED EVIDENCE
{evidence}

STRICT RULES

1. Never invent information.

2. Never invent:
   - deadlines
   - fees
   - dates
   - procedures
   - exam rules
   - registration rules
   - office instructions
   - URLs
   - results
   - contact information

3. Only use sources marked:
   "Officially verified: True"

4. Do NOT treat search-engine snippets as reliable evidence
   when the linked official page does not support the claim.

5. If a source does not directly support a statement,
   do not use that source for that statement.

6. If multiple official sources contain conflicting information:
   prefer the newer dated official source and mention the conflict.

7. If the question asks for a procedure and the official source
   clearly provides steps, present them as numbered steps.

8. Exact dates, fees and deadlines must appear in the evidence.

9. If there is no valid official evidence supporting the requested
   information, use exactly this sentence:

   "এই তথ্যের জন্য বর্তমানে কোনো valid official source পাওয়া যায়নি।"

10. After that sentence, briefly mention what was searched.

11. Answer in the user's language whenever possible.

12. Keep the answer concise and practical.

13. Do not use markdown inside the JSON strings.

14. Source numbers may be included in factual claims like:
    [Source 1]

15. Return ONLY valid JSON.

EXPECTED JSON FORMAT

{{
    "answer": "Direct answer to the user's question.",
    "status": "verified",
    "key_information": [
        "Important verified fact",
        "Another verified fact"
    ],
    "steps": [
        "Step 1",
        "Step 2",
        "Step 3"
    ],
    "important_notes": [
        "Important note"
    ]
}}

If no valid official source supports the answer, return:

{{
    "answer": "এই তথ্যের জন্য বর্তমানে কোনো valid official source পাওয়া যায়নি।",
    "status": "not_found",
    "key_information": [],
    "steps": [],
    "important_notes": [
        "Briefly mention what was searched."
    ]
}}
"""

    result = _llm().invoke(prompt)

    raw_content = (
        result.content
        if hasattr(result, "content")
        else str(result)
    )

    # Some LangChain versions can return structured content.
    if isinstance(raw_content, list):
        parts = []

        for item in raw_content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
            else:
                parts.append(str(item))

        raw_content = "\n".join(parts)

    raw_content = _clean_json_text(raw_content)

    try:
        data = json.loads(raw_content)
        return _normalize_result(data)

    except json.JSONDecodeError:

        # Fallback if model returns plain text unexpectedly.
        return {
            "answer": raw_content,
            "status": "unknown",
            "key_information": [],
            "steps": [],
            "important_notes": [
                "The AI response could not be parsed into the expected structured format."
            ],
        }