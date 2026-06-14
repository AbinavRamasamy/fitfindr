"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(description: str, size: str | None = None,
                    max_price: float | None = None,) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # Filter by price
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    # Filter by size (case-insensitive)
    if size is not None:
        size_upper = size.upper()
        listings = [l for l in listings
                   if size_upper in l["size"].upper()]

    # Score by keyword overlap
    desc_words = set(description.lower().split())
    scored = []
    for listing in listings:
        searchable = (
            listing["title"].lower() + " " +
            listing["description"].lower() + " " +
            " ".join(listing.get("style_tags", []))
        )
        searchable_words = set(searchable.split())
        score = len(desc_words & searchable_words)
        if score > 0:
            scored.append((score, listing))

    # Sort by score descending, return listings
    scored.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()
    item_name = new_item.get("title", "item")
    item_color = ", ".join(new_item.get("colors", ["unknown"])) if new_item.get("colors") else "unknown"
    item_category = new_item.get("category", "piece")
    style_tags = new_item.get("style_tags", [])

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        # Empty wardrobe: general styling advice
        prompt = f"""User found a {item_color} {item_category} ({item_name}).
They have an empty wardrobe.

Suggest 5-6 general clothing categories and types that would pair well with this item.
Focus on bottoms, shoes, outerwear, and accessories that match the vibe.
Keep it conversational and encouraging."""
    else:
        # Non-empty wardrobe: specific combinations
        wardrobe_list = "\n".join([
            f"- {item['name']} ({', '.join(item.get('colors', []))} {item['category']})"
            for item in wardrobe_items
        ])
        prompt = f"""User found: {item_name} ({item_color} {item_category})
Style tags: {', '.join(style_tags) if style_tags else 'none'}

Their wardrobe:
{wardrobe_list}

Suggest 1-2 specific outfit combinations using the new item with pieces from their wardrobe.
Be specific: "Pair with [item_name] and [item_name]..."
Keep it casual and encouraging."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against empty outfit
    if not outfit or not outfit.strip():
        title = new_item.get("title", "item")
        color = ", ".join(new_item.get("colors", [])) if new_item.get("colors") else "item"
        category = new_item.get("category", "piece")
        return f"Could not create fit card: outfit suggestion was empty. {title} is a {color} {category}. Try a different search or refresh your wardrobe."

    client = _get_groq_client()
    item_name = new_item.get("title", "item")
    price = new_item.get("price", "?")
    platform = new_item.get("platform", "online")
    colors = ", ".join(new_item.get("colors", [])) if new_item.get("colors") else "item"

    prompt = f"""Create an Instagram/TikTok-style outfit caption (2-4 sentences).

Item: {item_name}
Price: ${price}
Platform: {platform}
Colors: {colors}

Outfit suggestion: {outfit}

Requirements:
- Sound casual and authentic (like a real person posting, not marketing)
- Mention item name, price, and platform naturally (once each)
- Include vibe/style descriptor
- Use casual language, maybe an emoji or hashtag
- Do NOT sound like a product listing"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content
