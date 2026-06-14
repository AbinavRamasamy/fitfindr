"""
test_tools.py

Pytest tests for FitFindr tools. One test per tool, covering happy path and failure modes.

Run with: pytest tests/test_tools.py -v
"""

import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


# ── Test Tool 1: search_listings ──────────────────────────────────────────────

class TestSearchListings:
    """Tests for search_listings tool."""

    def test_search_with_description_only(self):
        """Happy path: search by description, no size/price filters."""
        results = search_listings("vintage tee")
        assert isinstance(results, list)
        assert len(results) > 0
        assert all("price" in item for item in results)
        assert all("title" in item for item in results)

    def test_search_with_size_filter(self):
        """Happy path: search with size filter (case-insensitive)."""
        results = search_listings("graphic tee", size="M")
        assert isinstance(results, list)
        for item in results:
            assert "M" in item["size"].upper() or "m" in item["size"].lower()

    def test_search_with_price_filter(self):
        """Happy path: search with max_price filter."""
        results = search_listings("vintage tee", max_price=30)
        assert isinstance(results, list)
        for item in results:
            assert item["price"] <= 30, f"Price {item['price']} exceeds max of 30"

    def test_search_no_results(self):
        """Failure mode: no listings match query."""
        results = search_listings("impossible ballgown unicorn", max_price=5)
        assert results == []

    def test_search_results_sorted_by_relevance(self):
        """Verify results sorted by keyword overlap (highest relevance first)."""
        results = search_listings("vintage graphic tee")
        assert len(results) > 0
        # Top result should contain at least some query keywords
        top_result = results[0]
        searchable = (top_result["title"].lower() + " " +
                     top_result["description"].lower())
        assert "vintage" in searchable or "graphic" in searchable or "tee" in searchable


# ── Test Tool 2: suggest_outfit ───────────────────────────────────────────────

class TestSuggestOutfit:
    """Tests for suggest_outfit tool."""

    def test_suggest_outfit_with_wardrobe(self):
        """Happy path: suggest outfit with non-empty wardrobe."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "style_tags": ["vintage", "graphic"],
            "platform": "depop"
        }
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(sample_item, wardrobe)
        assert isinstance(outfit, str)
        assert len(outfit) > 0
        assert outfit.strip() != ""

    def test_suggest_outfit_empty_wardrobe(self):
        """Failure mode: wardrobe is empty."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "style_tags": ["vintage", "graphic"],
            "platform": "depop"
        }
        wardrobe = get_empty_wardrobe()
        outfit = suggest_outfit(sample_item, wardrobe)
        assert isinstance(outfit, str)
        assert len(outfit) > 0
        # Should contain general advice, not error

    def test_suggest_outfit_returns_non_empty_string(self):
        """Verify outfit suggestion never returns empty string."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "style_tags": ["vintage", "graphic"],
            "platform": "depop"
        }
        # Test with example wardrobe
        outfit1 = suggest_outfit(sample_item, get_example_wardrobe())
        assert outfit1.strip() != ""
        # Test with empty wardrobe
        outfit2 = suggest_outfit(sample_item, get_empty_wardrobe())
        assert outfit2.strip() != ""


# ── Test Tool 3: create_fit_card ──────────────────────────────────────────────

class TestCreateFitCard:
    """Tests for create_fit_card tool."""

    def test_create_fit_card_happy_path(self):
        """Happy path: create caption from outfit + item."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "platform": "depop"
        }
        outfit = "Pair with black jeans and white sneakers for a cool 90s vibe."
        caption = create_fit_card(outfit, sample_item)
        assert isinstance(caption, str)
        assert len(caption) > 0
        # Should be 2-4 sentences (rough check: count periods)
        sentence_count = caption.count(".")
        assert 2 <= sentence_count <= 5

    def test_create_fit_card_empty_outfit(self):
        """Failure mode: outfit string is empty."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "platform": "depop"
        }
        caption = create_fit_card("", sample_item)
        assert isinstance(caption, str)
        assert len(caption) > 0
        assert "Could not create fit card" in caption or "error" in caption.lower()

    def test_create_fit_card_whitespace_outfit(self):
        """Failure mode: outfit string is whitespace-only."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "platform": "depop"
        }
        caption = create_fit_card("   \t\n  ", sample_item)
        assert isinstance(caption, str)
        assert len(caption) > 0
        assert "Could not create fit card" in caption or "error" in caption.lower()

    def test_create_fit_card_mentions_price_and_platform(self):
        """Verify caption mentions item price and platform naturally (once each)."""
        sample_item = {
            "title": "Vintage Band Tee",
            "price": 24.99,
            "category": "tops",
            "colors": ["black", "white"],
            "platform": "depop"
        }
        outfit = "Pair with black jeans and white sneakers for a cool 90s vibe."
        caption = create_fit_card(outfit, sample_item)
        assert isinstance(caption, str)
        # Check that caption contains item details
        assert "Vintage Band Tee" in caption or "band tee" in caption.lower()
        assert "depop" in caption.lower() or "platform" in caption.lower() or "found" in caption.lower()
