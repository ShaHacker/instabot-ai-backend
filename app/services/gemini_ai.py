import google.generativeai as genai
from app.config import get_settings

settings = get_settings()


def get_gemini_model(api_key: str | None = None):
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        raise ValueError("Gemini API key not configured")
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-1.5-flash")


async def match_comment_to_keywords(comment_text: str, keywords: list[dict], api_key: str | None = None) -> dict | None:
    """Use Gemini to fuzzy-match a comment to keyword rules.
    Returns the matched keyword dict or None."""
    if not keywords:
        return None

    keyword_list = ", ".join([f'"{k["keyword"]}"' for k in keywords])

    prompt = f"""You are a keyword matcher for Instagram comment automation.

Given this Instagram comment: "{comment_text}"

And these trigger keywords: [{keyword_list}]

Does the comment match any of these keywords? Consider:
- Exact matches
- Typos and misspellings (e.g. "pricee" matches "price")
- Synonyms and similar meaning (e.g. "how much" matches "price", "where" matches "location")
- Different languages saying the same thing

Reply with ONLY the matched keyword exactly as written above, or "NONE" if no match.
Do not add any explanation."""

    try:
        model = get_gemini_model(api_key)
        response = model.generate_content(prompt)
        matched = response.text.strip().strip('"')

        for kw in keywords:
            if kw["keyword"].lower() == matched.lower():
                return kw
        return None
    except Exception:
        return None


async def match_comment_to_qa(comment_text: str, qa_pairs: list[dict], api_key: str | None = None) -> dict | None:
    """Use Gemini to match a comment to Q&A pairs using semantic similarity.
    Returns the matched QA dict or None."""
    if not qa_pairs:
        return None

    qa_list = "\n".join([f'{i+1}. Q: "{qa["question"]}"' for i, qa in enumerate(qa_pairs)])

    prompt = f"""You are a Q&A matcher for Instagram comment automation.

Given this Instagram comment: "{comment_text}"

And these saved questions:
{qa_list}

Does the comment match or ask something similar to any of these questions? Consider:
- Similar meaning even with different wording
- Typos and misspellings
- Slang and informal language
- Different languages asking the same thing

Reply with ONLY the number (1, 2, 3...) of the matching question, or "NONE" if no match.
Do not add any explanation."""

    try:
        model = get_gemini_model(api_key)
        response = model.generate_content(prompt)
        result = response.text.strip()

        if result.upper() == "NONE":
            return None

        idx = int(result) - 1
        if 0 <= idx < len(qa_pairs):
            return qa_pairs[idx]
        return None
    except Exception:
        return None


async def generate_smart_reply(
    comment_text: str,
    context: str,
    tone: str = "friendly",
    custom_tone: str | None = None,
    language: str = "English",
    api_key: str | None = None
) -> str:
    """Generate a smart AI reply for a comment."""
    tone_instruction = custom_tone if tone == "custom" and custom_tone else tone

    prompt = f"""You are an Instagram comment reply bot.

Comment: "{comment_text}"
Context: {context}
Tone: {tone_instruction}
Language: {language}

Generate a short, natural reply (1-2 sentences max). Be helpful and engaging.
Reply with ONLY the reply text, nothing else."""

    try:
        model = get_gemini_model(api_key)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Thanks for your comment! We'll get back to you soon. 🙏"
