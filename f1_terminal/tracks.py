"""
Central Track Database — single source of truth for all modules.
Fixes duplicate-country ambiguity (USA x3, Spain x2) by using unique fastf1_name.
Re-exported for both packages.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Track:
    round_num: int
    country: str
    city: str
    name: str
    fastf1_name: str

TRACKS: Dict[int, Track] = {
    1:  Track(1,  "Australia",     "Melbourne",       "Albert Park",                     "Australia"),
    2:  Track(2,  "China",         "Shanghai",        "Shanghai International Circuit",  "China"),
    3:  Track(3,  "Japan",         "Suzuka",          "Suzuka",                          "Japan"),
    4:  Track(4,  "USA",           "Miami",           "Miami International Autodrome",   "Miami"),
    5:  Track(5,  "Canada",        "Montreal",        "Circuit Gilles Villeneuve",       "Canada"),
    6:  Track(6,  "Monaco",        "Monaco",          "Monaco",                          "Monaco"),
    7:  Track(7,  "Spain",         "Barcelona",       "Circuit de Catalunya",            "Spain"),
    8:  Track(8,  "Austria",       "Spielberg",       "Red Bull Ring",                   "Austria"),
    9:  Track(9,  "Great Britain", "Silverstone",     "Silverstone",                     "Great Britain"),
    10: Track(10, "Belgium",       "Spa-Francorchamps","Spa-Francorchamps",              "Belgium"),
    11: Track(11, "Hungary",       "Budapest",        "Hungaroring",                     "Hungary"),
    12: Track(12, "Netherlands",   "Zandvoort",       "Zandvoort",                       "Netherlands"),
    13: Track(13, "Italy",         "Monza",           "Monza",                           "Italy"),
    14: Track(14, "Spain",         "Madrid",          "Madring",                         "Madrid"),
    15: Track(15, "Azerbaijan",    "Baku",            "Baku City Circuit",               "Azerbaijan"),
    16: Track(16, "Singapore",     "Singapore",       "Singapore",                       "Singapore"),
    17: Track(17, "USA",           "Austin",          "Circuit of the Americas",         "United States"),
    18: Track(18, "Mexico",        "Mexico City",     "Mexico City",                     "Mexico"),
    19: Track(19, "Brazil",        "São Paulo",       "Interlagos",                      "Brazil"),
    20: Track(20, "USA",           "Las Vegas",       "Las Vegas Strip Circuit",         "Las Vegas"),
    21: Track(21, "Qatar",         "Lusail",          "Lusail",                          "Qatar"),
    22: Track(22, "Abu Dhabi",     "Yas Marina",      "Yas Marina",                      "Abu Dhabi"),
}

TRACKS_LEGACY = {k: {"country": v.country, "city": v.city, "name": v.name, "fastf1_name": v.fastf1_name} for k, v in TRACKS.items()}

def get_track(n: int) -> Track:
    if n not in TRACKS:
        raise KeyError(f"Track {n} not found (valid 1-22)")
    return TRACKS[n]

def all_tracks():
    return TRACKS
