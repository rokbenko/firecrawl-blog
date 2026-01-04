from typing import Dict, Any
from dotenv import load_dotenv
import os
import requests
import json
import argparse

load_dotenv()


def scrape_ecommerce_product(url: str) -> Dict[str, Any]:
    """
    Scrape an e-commerce product page and extract structured product data using Firecrawl.

    The function sends the given product URL to the Firecrawl scraping API, applies a
    predefined JSON schema, and returns normalized product information such as title,
    price, reviews, availability, seller details, and images.

    The Firecrawl API key must be provided via the FIRECRAWL_API_KEY environment variable
    (e.g., loaded from a .env file).

    Args:
        url (str): URL of the e-commerce product page to scrape.

    Returns:
        Dict[str, Any]: A dictionary containing extracted product data on success,
        or a dictionary with an "error" key if the request fails or the API returns an error.

    Raises:
        ValueError: If the FIRECRAWL_API_KEY environment variable is not set.
    """

    # Get Firecrawl API key from environment variable
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

    if not firecrawl_api_key:
        raise ValueError(
            "Firecrawl API key is required. Set 'FIRECRAWL_API_KEY' environment variable!"
        )

    # Define the JSON schema for extraction
    extraction_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The product title."},
            "description": {
                "type": "string",
                "description": "The product description.",
            },
            "sku": {"type": "string", "description": "The product SKU or identifier."},
            "price": {
                "type": "number",
                "description": "The current price of the product.",
            },
            "discount": {
                "type": "number",
                "description": "Discount amount or percentage if applicable.",
            },
            "averageRating": {
                "type": "number",
                "description": "Average customer rating.",
            },
            "reviewCount": {
                "type": "integer",
                "description": "Number of customer reviews.",
            },
            "reviews": {
                "type": "array",
                "description": "List of customer reviews (limit to top 5-10 if many).",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "rating": {"type": "number"},
                    },
                },
            },
            "availability": {
                "type": "string",
                "description": "Availability status (e.g., 'In Stock', 'Out of Stock').",
            },
            "stockLevel": {
                "type": "integer",
                "description": "Stock quantity if available.",
            },
            "category": {"type": "string", "description": "Product category."},
            "taxonomy": {
                "type": "array",
                "description": "Product taxonomy or breadcrumb hierarchy.",
                "items": {"type": "string"},
            },
            "seller": {
                "type": "object",
                "description": "Seller information for marketplaces.",
                "properties": {
                    "name": {"type": "string"},
                    "rating": {"type": "number"},
                    "other": {"type": "string"},
                },
            },
            "productDetails": {
                "type": "object",
                "description": "Additional product details.",
                "properties": {
                    "asin": {"type": "string", "description": "ASIN code."},
                    "manufacturer": {
                        "type": "string",
                        "description": "Manufacturer name.",
                    },
                    "itemModelNumber": {
                        "type": "string",
                        "description": "Item model number.",
                    },
                    "packageDimensions": {
                        "type": "string",
                        "description": "Package dimensions and weight.",
                    },
                },
            },
        },
        "required": ["title", "price"],
    }

    # Prompt for LLM extraction
    extraction_prompt = (
        "Extract the product details from the page content. "
        "Focus on the main product information, pricing, reviews, and other requested fields. "
        "If a field is not found, omit it or use null. For reviews, extract a sample if many are present."
    )

    # Firecrawl API endpoint
    api_url = "https://api.firecrawl.dev/v2/scrape"

    # Request body
    body = {
        "url": url,
        "formats": [
            {"type": "markdown"},  # Get clean markdown content as backup
            {
                "type": "json",  # Get structured data using LLM extraction
                "schema": extraction_schema,
                "prompt": extraction_prompt,
            },
        ],
        "onlyMainContent": True,  # Focus on main content to avoid noise
        "blockAds": True,  # Block ads for cleaner data
        "removeBase64Images": True,  # Avoid large base64 strings
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {firecrawl_api_key}",
    }

    try:
        # Make the API request
        response = requests.post(
            api_url,
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            return {"error": data.get("error", "Unknown error")}

        scrape_data = data.get("data", {})
        result = scrape_data.get("json", {})

        # Return the extracted e-commerce product data
        return result

    except requests.RequestException as e:
        return {"Error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Product page URL")
    args = parser.parse_args()

    result = scrape_ecommerce_product(args.url)
    print(json.dumps(result, indent=2))
