"""
Agent tool functions for VoteGuide.

Each tool retrieves structured election data and formats it
for injection into the LLM prompt as grounding context.
"""

from election_data import get_country_data, check_eligibility


def get_timeline_info(country: str, year: str = "2024") -> str:
    """Get election timeline for a country.

    Returns a markdown-formatted string with timeline phases and dates.
    """
    data = get_country_data(country)
    if not data:
        return f"Timeline data not available for '{country}'. Supported countries: India, USA, UK."

    timelines = data.get("timelines", {})
    result_parts = [f"## 📅 Election Timeline for {data['country']}"]

    # Specific year
    if year in timelines:
        for election_name, dates in timelines[year].items():
            if isinstance(dates, dict):
                result_parts.append(f"\n### {election_name} ({year})")
                for phase, date in dates.items():
                    result_parts.append(f"- **{phase.replace('_', ' ').title()}**: {date}")

    # General timeline
    general = timelines.get("general_timeline", {})
    if general:
        result_parts.append(f"\n### General Election Timeline")
        for phase, info in general.items():
            result_parts.append(f"- **{phase}**: {info}")

    return "\n".join(result_parts)


def get_registration_guide(country: str) -> str:
    """Get voter registration guide for a country.

    Returns a markdown-formatted string with registration steps,
    required documents, and portal links.
    """
    data = get_country_data(country)
    if not data:
        return f"Registration data not available for '{country}'. Supported countries: India, USA, UK."

    reg = data.get("registration", {})
    result_parts = [f"## 📝 Voter Registration Guide for {data['country']}"]

    if reg.get("steps"):
        result_parts.append("\n### Steps to Register:")
        for i, step in enumerate(reg["steps"], 1):
            result_parts.append(f"{i}. {step}")

    if reg.get("documents_required"):
        result_parts.append("\n### Documents Required:")
        for doc in reg["documents_required"]:
            result_parts.append(f"- {doc}")

    if reg.get("online_portal"):
        result_parts.append(f"\n🌐 **Online Portal**: {reg['online_portal']}")
    if reg.get("deadline"):
        result_parts.append(f"⏰ **Deadline**: {reg['deadline']}")
    if reg.get("processing_time"):
        result_parts.append(f"⏳ **Processing Time**: {reg['processing_time']}")

    return "\n".join(result_parts)


def get_voting_process(country: str) -> str:
    """Get step-by-step voting process for a country.

    Returns a markdown-formatted string with numbered voting steps
    and required identification.
    """
    data = get_country_data(country)
    if not data:
        return f"Voting process data not available for '{country}'. Supported countries: India, USA, UK."

    result_parts = [f"## 🗳️ How to Vote in {data['country']}"]

    if data.get("voting_process"):
        result_parts.append("\n### Step-by-Step Process:")
        for i, step in enumerate(data["voting_process"], 1):
            result_parts.append(f"{i}. {step}")

    if data.get("voter_id"):
        result_parts.append(f"\n🪪 **Required ID**: {data['voter_id']}")

    return "\n".join(result_parts)


def format_eligibility_result(result: dict) -> str:
    """Format eligibility check result into markdown.

    Renders eligible/ineligible status, reason, and next steps.
    """
    parts = []
    if result["eligible"]:
        parts.append("## ✅ You Are Eligible to Vote!")
    else:
        parts.append("## ❌ Eligibility Issues Found")

    parts.append(f"\n{result['reason']}")

    if result["next_steps"]:
        parts.append("\n### Next Steps:")
        for step in result["next_steps"]:
            parts.append(f"- {step}")

    return "\n".join(parts)


def execute_tools(
    intent: str,
    country: str | None,
    user_context: dict | None,
) -> list[str]:
    """Execute appropriate tool(s) based on intent and country.

    Returns a list of tool output strings for prompt injection.
    """
    tool_outputs: list[str] = []

    if intent == "timeline" and country:
        tool_outputs.append(get_timeline_info(country))
    elif intent == "eligibility":
        if user_context and user_context.get("age"):
            result = check_eligibility(
                country=country or user_context.get("country", "india"),
                age=user_context["age"],
                is_citizen=user_context.get("is_citizen", True),
                is_resident=user_context.get("is_resident", True),
            )
            tool_outputs.append(format_eligibility_result(result))
    elif intent == "registration" and country:
        tool_outputs.append(get_registration_guide(country))
    elif intent == "process" and country:
        tool_outputs.append(get_voting_process(country))

    return tool_outputs
