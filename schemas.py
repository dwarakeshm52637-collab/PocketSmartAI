from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128
    )


class HomeRequest(BaseModel):
    budget: float = Field(gt=0)

    rooms: list[str] = Field(
        min_length=1
    )

    quantities: dict[str, int] = {}

    style: str = "Modern"

    priorities: list[str] = []


class PartyRequest(BaseModel):
    budget: float = Field(gt=0)

    guests: int = Field(gt=0)

    event_type: str = Field(
        min_length=2,
        max_length=80
    )

    venue: str = "Any"

    city: str = ""

    preferences: list[str] = []


class JewelryRequest(BaseModel):
    budget: float = Field(gt=0)

    occasion: str = Field(
        min_length=2,
        max_length=80
    )

    style: str = "Elegant"

    metal: str = "Any"

    outfit_notes: str = ""