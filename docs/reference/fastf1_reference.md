# FastF1 Session Lookup Cheat Sheet

This guide serves as a quick reference for session codes and track names when working with the `fastf1` library.

---

## 1. Session Codes

Use these short codes to specify the type of session you want to load.

| Session | Code |
| :--- | :--- |
| Practice Session 1 | `FP1` |
| Practice Session 2 | `FP2` |
| Practice Session 3 | `FP3` |
| Qualifying | `Q` |
| Main Race | `R` |

---

## 2. Track Names & Locations

When calling the API, you can generally use the **Country** or **City** name as the track identifier.

| Country | City / Track Name |
| :--- | :--- |
| Australia | Melbourne (Albert Park) |
| China | Shanghai (Shanghai International Circuit) |
| Japan | Suzuka |
| Miami | USA (Miami International Autodrome) |
| Canada | Montreal (Circuit Gilles Villeneuve) |
| Monaco | Monaco |
| Spain | Barcelona (Circuit de Catalunya) |
| Austria | Spielberg (Red Bull Ring) |
| Great Britain | Silverstone |
| Belgium | Spa-Francorchamps |
| Hungary | Budapest (Hungaroring) |
| Netherlands | Zandvoort |
| Italy | Monza |
| Spain | Madrid (New Race) |
| Azerbaijan | Baku |
| Singapore | Singapore |
| USA | Austin (Circuit of the Americas) |
| Mexico | Mexico City |
| Brazil | São Paulo (Interlagos) |
| USA | Las Vegas (Las Vegas Strip Circuit) |
| Qatar | Lusail |
| Abu Dhabi | Yas Marina |

---

## 3. Code Template

Update the year, track, and session arguments in the function template below:

```python
import fastf1

# Format: fastf1.get_session(Year, 'Track Name', 'Session Code')
session = fastf1.get_session(2026, 'Austria', 'FP1')
session.load()

```