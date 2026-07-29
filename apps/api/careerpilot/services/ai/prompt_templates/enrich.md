Review the verified PROFILE. Return JSON with a suggestions array.
Allowed suggestion types: normalize_skill, categorize_skill, add_skill,
extract_achievement, duplicate. Any add_skill must cite explicit evidence already
present in PROFILE. Do not invent facts.
Each suggestion must have: type, source_type, source_id, original, proposed,
rationale, confidence (0 to 1).

PROFILE:
{{PROFILE}}
