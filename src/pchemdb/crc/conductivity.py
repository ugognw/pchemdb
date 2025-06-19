"""Utilities for parsin molar conductivity data from CRC."""

import logging
import re
from typing import Any

from pyEQL import Solution
from pyEQL import ureg
from pyEQL.benchmark import BenchmarkEntry

from pchemdb.utils import formula_to_salt

logger = logging.getLogger(__name__)

formula_re = re.compile(r"(?P<coeff>\d+/\d+)?(?P<formula>.+)")
# aqueous HBr/HCl
cond_temp_re = re.compile(
    "<i>\u039b</i>/"
    r"S cm<sup>2</sup> mol<sup>-1</sup><br/>(?:(?P<sign>.)?(?P<temp>\d+.+C))"
)
# aqueous hydro-halogen acids
cond_conc_re1 = re.compile(
    "<i>\u039b</i>/"
    r"S cm<sup>2</sup> mol<sup>-1</sup><br/>(?P<conc>\d+\.\d+)"
)
# aqueous electrolytes
cond_conc_re2 = re.compile(
    "<i>\u039b</i>"
    r"<sup></sup>\((?P<conc>\d+\.\d+) M\)/S cm<sup>2 </sup>mol<sup>-1</sup>"
)
activity_conc_re = re.compile("<i>\u03b3</i>" r"\((?P<conc>\d+\.\d+) m\)")
xml_tags_re = re.compile(r"<(/)?[^>]+>")
DEFAULT_TEMPERATURE = "298.15 K"
_CONDUCTIVITY_CONC_KEY = "<i>c</i>/M"
_CONDUCTIVITY_UNITS = "S/m"
_CONCENTRATION_UNITS = "mol/L"


def parse_crc(d: dict[str, Any]) -> list[BenchmarkEntry]:
    """Parse data from CRC."""
    dataset: list[BenchmarkEntry] = []
    solution = xml_tags_re.sub("", d.get("Mol. form.", d.get("Compound")))
    match = formula_re.search(solution)

    if not match:
        msg = f"Unable to parse formula: {solution}"
        raise ValueError(msg)

    num, denom = (match.group("coeff") or "1/1").split("/")
    factor = int(num) / int(denom)
    formula = match.group("formula")
    salt = formula_to_salt(formula)
    temp = DEFAULT_TEMPERATURE
    conc_units = _CONCENTRATION_UNITS

    for k, v in d.items():
        if k is None or not v:
            continue

        # If data key in temperature-dependent dataset,
        # read concentration from "<i>c,<\i>/M" key
        # read temperature from cond_temp_re
        if match := cond_temp_re.search(k):
            prop = "conductivity"
            conc_mag = float(d[_CONDUCTIVITY_CONC_KEY])
            conc = ureg.Quantity(conc_mag, conc_units) * factor
            temp = match.group("temp")
            prop_units = "S cm ** 2 /mol"
            value = conc * ureg.Quantity(float(v), prop_units)
            value = value.to(_CONDUCTIVITY_UNITS)

        # If data key in concentration-dependent dataset,
        # read concentration from conc_re (activity or conductivity)
        # use default temperature
        elif (conc_match := cond_conc_re1.search(k)) or (
            conc_match := cond_conc_re2.search(k)
        ):
            prop = "conductivity"
            conc_mag = float(conc_match.group("conc"))
            conc = ureg.Quantity(conc_mag, conc_units) * factor
            prop_units = "S cm ** 2 /mol"
            value = conc * ureg.Quantity(float(v), prop_units)
            value = value.to(_CONDUCTIVITY_UNITS)
        elif conc_match := activity_conc_re.search(k):
            prop = "mean_activity"
            conc_mag = float(conc_match.group("conc"))
            conc_units = "mol/kg"
            conc = ureg.Quantity(conc_mag, conc_units)
            value = ureg.Quantity(float(v), prop_units)
        else:
            continue

        solutes = {
            salt.cation: f"{conc.magnitude * salt.nu_cation} {conc.units}",
            salt.anion: f"{conc.magnitude * salt.nu_anion} {conc.units}",
        }
        soln = Solution(solutes=solutes, temperature=temp)
        soln_data = [(prop, value)]
        entry = BenchmarkEntry(solution=soln, solution_data=soln_data)
        dataset.append(entry)

    return dataset
