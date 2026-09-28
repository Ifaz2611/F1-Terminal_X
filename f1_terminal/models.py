"""Pydantic models for Track, SessionParams, DriverResult (backlog)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Track(BaseModel):
    round_num: int = Field(ge=1, le=30)
    country: str
    city: str
    name: str
    fastf1_name: str


class SessionParams(BaseModel):
    year: int = Field(ge=2018, le=2030)
    track: str
    session: str = Field(pattern="^(FP1|FP2|FP3|Q|R|S|SQ)$")
    driver: str | None = None


class DriverResult(BaseModel):
    code: str
    team: str = "Unknown"
    lap_time: str = "N/A"
    color: str = "#E10600"
