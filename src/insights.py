import re
from collections import Counter
from typing import Dict, List


SECTION_STOP_WORDS = {
    "professional summary",
    "professional experience",
    "education",
    "certifications",
    "projects",
    "technical tools",
    "soft skills",
    "awards",
    "languages",
}


def _normalize_heading(line: str) -> str:
    cleaned = re.sub(r"^[#\-*\s]+", "", line or "").strip().lower()
    cleaned = re.sub(r":\s*$", "", cleaned)
    return cleaned


def _collect_skills_section(lines: List[str]) -> List[str]:
    collected: List[str] = []
    for i, line in enumerate(lines):
        cleaned_line = re.sub(r"^[#\-*\s]+", "", line or "").strip()
        heading = _normalize_heading(line)
        has_inline_prefix = bool(re.match(r"^(core\s+skills|skills)\s*:\s*", cleaned_line, flags=re.IGNORECASE))
        if heading not in {"skills", "core skills"} and not has_inline_prefix:
            continue

        inline_value = re.sub(r"^(core\s+skills|skills)\s*:\s*", "", cleaned_line, flags=re.IGNORECASE).strip()
        if inline_value and inline_value.lower() not in {"skills", "core skills"}:
            collected.append(inline_value)

        for next_line in lines[i + 1 : i + 30]:
            if not next_line.strip():
                continue

            if next_line.strip().startswith("---"):
                break

            next_heading = _normalize_heading(next_line)
            if next_heading in SECTION_STOP_WORDS:
                break

            if next_line.strip().startswith("#") and next_heading not in {"skills", "core skills"}:
                break

            value = re.sub(r"^[\-*•\s]+", "", next_line).strip()
            if value:
                collected.append(value)

        break

    return collected


def build_talent_insights_from_texts(texts: List[str]) -> Dict[str, object]:
    experience_levels = Counter({"entry": 0, "mid": 0, "senior": 0, "unknown": 0})
    education_levels = Counter({"phd": 0, "masters": 0, "bachelors": 0, "diploma_or_other": 0, "unknown": 0})
    skill_counter: Counter[str] = Counter()

    for raw_text in texts:
        raw_text = (raw_text or "").strip()
        if not raw_text:
            continue

        lowered = raw_text.lower()

        years_match = re.search(r"(\d{1,2})\s*\+?\s*years", lowered)
        if years_match:
            years = int(years_match.group(1))
            if years < 3:
                experience_levels["entry"] += 1
            elif years < 8:
                experience_levels["mid"] += 1
            else:
                experience_levels["senior"] += 1
        else:
            experience_levels["unknown"] += 1

        if any(keyword in lowered for keyword in ["phd", "doctorate"]):
            education_levels["phd"] += 1
        elif any(keyword in lowered for keyword in ["m.e", "m.tech", "master", "mba", "mca", "m.sc"]):
            education_levels["masters"] += 1
        elif any(keyword in lowered for keyword in ["b.e", "b.tech", "bachelor", "bca", "b.sc"]):
            education_levels["bachelors"] += 1
        elif any(keyword in lowered for keyword in ["diploma", "associate degree"]):
            education_levels["diploma_or_other"] += 1
        else:
            education_levels["unknown"] += 1

        lines = [line.rstrip() for line in raw_text.splitlines()]
        section_values = _collect_skills_section(lines)
        merged = ",".join(section_values)
        for token in re.split(r"[,;/|]", merged):
            skill = token.strip().lower().strip(".-")
            if len(skill) >= 2:
                skill_counter[skill] += 1

    return {
        "experience_levels": {
            "entry": int(experience_levels["entry"]),
            "mid": int(experience_levels["mid"]),
            "senior": int(experience_levels["senior"]),
            "unknown": int(experience_levels["unknown"]),
        },
        "education_levels": {
            "phd": int(education_levels["phd"]),
            "masters": int(education_levels["masters"]),
            "bachelors": int(education_levels["bachelors"]),
            "diploma_or_other": int(education_levels["diploma_or_other"]),
            "unknown": int(education_levels["unknown"]),
        },
        "top_skills": [
            {"skill": skill, "count": count}
            for skill, count in skill_counter.most_common(20)
        ],
    }


def build_resume_insights(raw_text: str) -> Dict[str, object]:
    return build_talent_insights_from_texts([raw_text])