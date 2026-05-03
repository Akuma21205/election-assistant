"""
RAG (Retrieval-Augmented Generation) module using ChromaDB for election data.
Provides semantic search over election FAQs and country-specific election information.
"""

import chromadb
from election_data import ELECTION_DATA, FAQ_DATA
import json
import logging

logger = logging.getLogger("voteguide.rag")

# Use in-memory client (no external DB server needed)
chroma_client = chromadb.Client()

# Create or get collection
collection = chroma_client.get_or_create_collection(
    name="election_knowledge",
    metadata={"hnsw:space": "cosine"}
)

_initialized = False


def _flatten_country_data(country_key: str, data: dict) -> list[dict]:
    """Flatten country election data into searchable documents."""
    docs = []
    country = data["country"]

    # Registration steps
    reg = data.get("registration", {})
    if reg.get("steps"):
        docs.append({
            "id": f"{country_key}_registration",
            "text": f"How to register to vote in {country}: " + " → ".join(reg["steps"]),
            "metadata": {"country": country_key, "category": "registration", "type": "process"}
        })
    if reg.get("documents_required"):
        docs.append({
            "id": f"{country_key}_documents",
            "text": f"Documents required for voter registration in {country}: " + ", ".join(reg["documents_required"]),
            "metadata": {"country": country_key, "category": "registration", "type": "documents"}
        })

    # Voting process
    if data.get("voting_process"):
        docs.append({
            "id": f"{country_key}_voting_process",
            "text": f"How to vote in {country} step by step: " + " → ".join(data["voting_process"]),
            "metadata": {"country": country_key, "category": "voting", "type": "process"}
        })

    # Election types
    for i, et in enumerate(data.get("election_types", [])):
        docs.append({
            "id": f"{country_key}_election_type_{i}",
            "text": f"{et['type']} in {country}: {et['description']}. Frequency: {et['frequency']}.",
            "metadata": {"country": country_key, "category": "election_types", "type": "info"}
        })

    # Eligibility
    elig = data.get("eligibility", {})
    if elig:
        elig_text = f"Voting eligibility in {country}: Age requirement: {elig.get('age', 'N/A')}. Citizenship: {elig.get('citizenship', 'N/A')}. Residency: {elig.get('residency', 'N/A')}."
        if elig.get("disqualifications"):
            elig_text += " Disqualifications: " + "; ".join(elig["disqualifications"])
        docs.append({
            "id": f"{country_key}_eligibility",
            "text": elig_text,
            "metadata": {"country": country_key, "category": "eligibility", "type": "info"}
        })

    # Timelines
    timelines = data.get("timelines", {})
    for year, elections in timelines.items():
        if isinstance(elections, dict):
            for election_name, dates in elections.items():
                if isinstance(dates, dict):
                    timeline_text = f"{election_name} in {country} ({year}): " + ", ".join(
                        [f"{k}: {v}" for k, v in dates.items()]
                    )
                    docs.append({
                        "id": f"{country_key}_timeline_{year}_{election_name.replace(' ', '_').lower()}",
                        "text": timeline_text,
                        "metadata": {"country": country_key, "category": "timeline", "type": "dates", "year": year}
                    })

    # Electoral College (USA specific)
    if "electoral_college" in data:
        ec = data["electoral_college"]
        docs.append({
            "id": f"{country_key}_electoral_college",
            "text": f"The Electoral College in the {country}: {ec['explanation']} Total votes: {ec['total_votes']}. Votes needed to win: {ec['to_win']}.",
            "metadata": {"country": country_key, "category": "electoral_system", "type": "info"}
        })

    return docs


def initialize_rag() -> int:
    """Load all election data into ChromaDB for semantic search.

    Returns:
        Number of documents indexed.
    """
    global _initialized
    if _initialized:
        return collection.count()

    all_docs = []

    # Flatten country data
    for country_key, country_data in ELECTION_DATA.items():
        all_docs.extend(_flatten_country_data(country_key, country_data))

    # Add FAQ data
    for i, faq in enumerate(FAQ_DATA):
        all_docs.append({
            "id": f"faq_{i}",
            "text": f"Q: {faq['question']} A: {faq['answer']}",
            "metadata": {"country": faq.get("country", "general"), "category": faq.get("category", "general"), "type": "faq"}
        })

    # Upsert into ChromaDB
    if all_docs:
        collection.upsert(
            ids=[d["id"] for d in all_docs],
            documents=[d["text"] for d in all_docs],
            metadatas=[d["metadata"] for d in all_docs],
        )
        logger.info(f"✅ RAG initialized with {len(all_docs)} documents")

    _initialized = True
    return len(all_docs)


def search(query: str, n_results: int = 5, country: str | None = None) -> list[dict]:
    """Search the election knowledge base with semantic search.

    Args:
        query: The search query
        n_results: Number of results to return
        country: Optional country filter

    Returns:
        List of relevant documents with scores
    """
    initialize_rag()

    where_filter = None
    if country:
        key = country.lower().strip()
        aliases = {
            "us": "usa", "united states": "usa", "america": "usa",
            "britain": "uk", "united kingdom": "uk", "england": "uk",
            "bharat": "india"
        }
        key = aliases.get(key, key)
        where_filter = {"$or": [{"country": key}, {"country": "general"}]}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
    except Exception:
        # Fallback without filter if it fails
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )

    docs = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results.get("distances") else None
            docs.append({
                "content": doc,
                "metadata": metadata,
                "relevance_score": 1 - (distance or 0),  # Convert distance to similarity
            })

    return docs
