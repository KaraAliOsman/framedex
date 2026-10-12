"""OGUC 4.1.10, DS15/2024; MINVU consolidated March 2026 pp253–272.

Literal transcription: no interpolation. The first upper U bound that includes
the *largest* window U in a facade is the applicable column (table 3).
East and west share a lookup row but are distinct facade groups (table 4).
"""

from decimal import Decimal

D = Decimal
RULE_VERSION = "OGUC-4.1.10-DS15-2024-v1"
RULE_SOURCE = "https://www.diariooficial.interior.gob.cl/publicaciones/2024/05/27/43860/01/2494861.pdf"
U_BOUNDS = tuple(map(D, ("0.6", "0.8", "1.2", "1.6", "2.0", "2.4", "2.8", "3.2", "3.6", "4.0", "4.4", "5.8")))
# Rows: Norte, Oriente/Poniente, Sur, OGT. DS15 pp6–7, table 3.
PERCENTAGES = {
    "A": ((100,100,100,100,100,98,97,95,94,91,88,50), (100,100,99,96,94,91,87,84,80,75,69,30), (94,93,91,89,85,82,78,74,69,63,57,25), (54,53,52,51,50,49,48,46,44,42,40,25)),
    "B": ((100,99,98,97,96,94,92,90,88,85,82,30), (92,91,89,87,84,81,78,75,71,66,60,20), (86,84,81,78,75,71,68,64,59,54,47,10), (52,51,49,47,46,45,43,42,40,38,35,10)),
    "C": ((96,95,94,93,91,90,88,85,83,79,75,40), (82,81,79,77,75,72,69,66,62,58,52,35), (75,73,70,67,64,61,58,54,49,44,38,15), (47,46,45,44,42,41,39,37,35,33,30,15)),
    "D": ((94,93,91,89,87,85,83,80,77,73,69,25), (73,72,70,68,65,63,60,57,53,49,44,15), (62,61,59,57,54,51,48,44,40,35,29,10), (43,42,41,40,38,37,35,33,31,28,25,10)),
    "E": ((90,89,87,85,83,80,78,75,71,67,61,10), (63,62,60,58,56,54,51,48,45,41,35,8), (51,50,48,46,44,41,38,35,31,26,20,5), (39,38,37,36,34,32,30,28,26,23,19,5)),
    "F": ((88,86,83,80,78,76,73,69,65,60,54,0), (54,53,51,49,47,45,42,40,36,32,27,0), (41,40,38,36,34,31,28,25,21,17,12,0), (36,35,33,31,30,28,26,24,21,17,13,0)),
    "G": ((84,82,79,76,74,71,67,64,59,54,46,0), (43,42,41,40,38,36,34,31,28,24,20,0), (31,30,28,26,24,21,19,16,13,8,0,0), (32,31,29,27,26,24,21,19,16,12,0,0)),
    "H": ((77,76,74,72,69,66,62,58,53,47,38,0), (34,33,32,31,29,27,25,23,20,16,12,0), (30,29,27,25,23,20,18,15,12,7,0,0), (31,30,28,26,25,23,20,18,15,11,0,0)),
    "I": ((75,73,70,67,64,61,57,52,46,39,30,0), (43,42,41,40,38,36,34,31,28,24,20,0), (28,27,25,23,21,18,16,13,10,5,0,0), (29,28,26,24,23,21,18,16,13,10,0,0)),
}
AIR_MINIMUM = {"A": None, "B": 1, "C": 1, "D": 2, "E": 2, "F": 2, "G": 3, "H": 3, "I": 3}
# DS15 table12 p15, uses education/health/hotels (not residential table3).
EQUIPMENT_U_MAX = dict(zip("ABCDEFGHI", map(D, ("5.8", "3.6", "3.6", "3.6", "3.0", "3.0", "3.0", "2.4", "3.0")), strict=True))


def maximum_percentage(zone: str, orientation: str, uw: Decimal) -> Decimal | None:
    if zone not in PERCENTAGES or orientation not in ("N", "E", "W", "S", "OGT") or uw <= 0:
        return None
    row = {"N": 0, "E": 1, "W": 1, "S": 2, "OGT": 3}[orientation]
    return next((D(PERCENTAGES[zone][row][index]) for index, bound in enumerate(U_BOUNDS) if uw <= bound), None)


def orientation_from_azimuth(degrees: Decimal) -> str:
    if not degrees.is_finite() or not 0 <= degrees < 360:
        raise ValueError("El azimut debe estar entre 0° y menos de 360°.")
    return "N" if degrees >= 315 or degrees < 45 else "E" if degrees < 135 else "S" if degrees < 225 else "W"
