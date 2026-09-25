import json

from urllib.parse import quote_plus

from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from .config import get_settings


settings = get_settings()


PLATFORMS = {
    "Amazon": "https://www.amazon.in/s?k={q}",
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={q}",
    "Swiggy": "https://www.swiggy.com/search?query={q}",
    "Zomato": "https://www.zomato.com/search?query={q}",
    "OYO": "https://www.oyorooms.com/search?location={q}",
}


class RecommendationItem(BaseModel):

    name: str

    category: str

    platform: str

    estimated_price: float = Field(
        ge=0
    )

    reason: str


class BudgetAllocation(BaseModel):

    category: str

    percentage: float = Field(
        ge=0,
        le=100
    )


class RecommendationResult(BaseModel):

    category: str

    title: str

    summary: str

    budget: float

    items: list[RecommendationItem]

    budget_plan: list[BudgetAllocation]


def search_url(
    platform: str,
    name: str
) -> str:

    template = PLATFORMS.get(
        platform,
        PLATFORMS["Amazon"]
    )

    return template.format(
        q=quote_plus(name)
    )


def fallback_home(d):

    budget = float(
        d["budget"]
    )

    rooms = d["rooms"]

    per_room = (
        budget / len(rooms)
    )

    items = []

    for room in rooms:

        items += [
            RecommendationItem(
                name=(
                    f"{d['style']} ceiling "
                    f"light for {room}"
                ),
                category="Lighting",
                platform="Amazon",
                estimated_price=per_room * 0.12,
                reason=(
                    "Practical lighting within "
                    "the room allocation."
                )
            ),

            RecommendationItem(
                name=(
                    f"{d['style']} storage "
                    f"unit for {room}"
                ),
                category="Furniture",
                platform="IKEA",
                estimated_price=per_room * 0.30,
                reason=(
                    "Useful storage while protecting "
                    "the overall budget."
                )
            ),

            RecommendationItem(
                name=(
                    f"Decor accent set for {room}"
                ),
                category="Decor",
                platform="Flipkart",
                estimated_price=per_room * 0.10,
                reason=(
                    "Adds style without using "
                    "a large part of the room budget."
                )
            ),
        ]

    return RecommendationResult(

        category="home",

        title="Home Interior Budget Plan",

        summary=(
            f"A ₹{budget:,.0f} plan for "
            f"{len(rooms)} room(s)."
        ),

        budget=budget,

        items=items[:10],

        budget_plan=[

            BudgetAllocation(
                category="Furniture & storage",
                percentage=45
            ),

            BudgetAllocation(
                category="Lighting",
                percentage=20
            ),

            BudgetAllocation(
                category="Decor",
                percentage=20
            ),

            BudgetAllocation(
                category="Buffer",
                percentage=15
            )
        ]
    )


def fallback_party(d):

    budget = float(
        d["budget"]
    )

    guests = int(
        d["guests"]
    )

    event = d["event_type"]

    return RecommendationResult(

        category="party",

        title=f"{event} Party Budget Plan",

        summary=(
            f"A ₹{budget:,.0f} outline "
            f"for {guests} guests."
        ),

        budget=budget,

        items=[

            RecommendationItem(
                name=(
                    f"{event} catering "
                    f"for {guests} guests"
                ),
                category="Food",
                platform="Swiggy",
                estimated_price=budget * 0.45,
                reason=(
                    "Food is a major event cost "
                    "influenced by guest count."
                )
            ),

            RecommendationItem(
                name=(
                    f"{event} decoration package"
                ),
                category="Decoration",
                platform="Zomato",
                estimated_price=budget * 0.18,
                reason=(
                    "A moderate decoration allowance "
                    "keeps the event complete."
                )
            ),

            RecommendationItem(
                name=(
                    f"{d['venue']} venue option "
                    f"{d['city']}"
                ).strip(),
                category="Venue",
                platform="OYO",
                estimated_price=budget * 0.22,
                reason=(
                    "A venue allowance protects "
                    "the total event budget."
                )
            )
        ],

        budget_plan=[

            BudgetAllocation(
                category="Food",
                percentage=45
            ),

            BudgetAllocation(
                category="Venue",
                percentage=22
            ),

            BudgetAllocation(
                category="Decoration",
                percentage=18
            ),

            BudgetAllocation(
                category="Entertainment & buffer",
                percentage=15
            )
        ]
    )


def fallback_jewelry(d):

    budget = float(
        d["budget"]
    )

    occasion = d["occasion"]

    style = d["style"]

    return RecommendationResult(

        category="jewelry",

        title=f"{occasion} Jewelry Suggestions",

        summary=(
            f"{style} ideas within "
            f"₹{budget:,.0f}."
        ),

        budget=budget,

        items=[

            RecommendationItem(
                name=(
                    f"{style} earrings "
                    f"for {occasion}"
                ),
                category="Earrings",
                platform="Amazon",
                estimated_price=budget * 0.22,
                reason=(
                    "A versatile accessory "
                    "for the selected occasion."
                )
            ),

            RecommendationItem(
                name=(
                    f"{style} necklace set "
                    f"for {occasion}"
                ),
                category="Necklace",
                platform="Flipkart",
                estimated_price=budget * 0.38,
                reason=(
                    "A central piece aligned "
                    "with the chosen style."
                )
            ),

            RecommendationItem(
                name=(
                    f"{d['metal']} bracelet "
                    f"for {occasion}"
                ),
                category="Bracelet",
                platform="Amazon",
                estimated_price=budget * 0.15,
                reason=(
                    "A smaller accessory leaves "
                    "budget flexibility."
                )
            )
        ],

        budget_plan=[

            BudgetAllocation(
                category="Necklace",
                percentage=40
            ),

            BudgetAllocation(
                category="Earrings",
                percentage=25
            ),

            BudgetAllocation(
                category="Bracelet/Ring",
                percentage=15
            ),

            BudgetAllocation(
                category="Buffer",
                percentage=20
            )
        ]
    )


def prompt(
    category,
    data
):

    return (

        "You are PocketSmart AI, "
        "a budget-aware recommendation assistant.\n"

        f"Category: {category}\n"

        f"User input: "
        f"{json.dumps(data, ensure_ascii=False)}\n\n"

        "Return practical recommendations. "
        "Respect the budget. "

        "Do not claim live stock, exact current "
        "prices, confirmed availability, "
        "or official affiliation. "

        "estimated_price is only a planning estimate. "

        "Use only these platform names when "
        "appropriate: Amazon, Flipkart, IKEA, "
        "Swiggy, Zomato, OYO. "

        "Return 5-10 items and budget percentages "
        "totaling 100."
    )


def generate(
    category,
    data,
    image_bytes=None,
    image_mime=None
):

    fallbacks = {

        "home": fallback_home,

        "party": fallback_party,

        "jewelry": fallback_jewelry,
    }

    if (
        not settings.ai_enabled
        or not settings.gemini_api_key
    ):

        return fallbacks[category](
            data
        )

    try:

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        if image_bytes and image_mime:

            contents = [

                types.Part.from_text(
                    text=prompt(
                        category,
                        data
                    )
                ),

                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_mime
                )
            ]

        else:

            contents = prompt(
                category,
                data
            )

        response = client.models.generate_content(

            model=settings.gemini_model,

            contents=contents,

            config=types.GenerateContentConfig(

                response_mime_type="application/json",

                response_schema=RecommendationResult,
            )
        )

        result = (
            RecommendationResult
            .model_validate_json(
                response.text
            )
        )

        result.category = category

        result.budget = float(
            data["budget"]
        )

        for item in result.items:

            if item.platform not in PLATFORMS:

                item.platform = "Amazon"

        return result

    except Exception:

        return fallbacks[category](
            data
        )


def to_dict(result):

    data = result.model_dump()

    for item in data["items"]:

        item["search_url"] = search_url(
            item["platform"],
            item["name"]
        )

    return data