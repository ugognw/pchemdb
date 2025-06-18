"""Utilities for parsin molar conductivity data from CRC."""

import re
from typing import Any

from pyEQL import Solution
from pyEQL.benchmark import BenchmarkEntry

from pchemdb.utils import formula_to_salt
from pchemdb.utils import salt_to_solutes

formula_re = re.compile(r"(?P<coeff>\d+/\d+)?(?P<formula>.+)")
ion_re1 = re.compile(r"(?P<ion>[A-Z][a-z]?)(?P<ion_sub>\d+)?")
ion_re2 = re.compile(r"\((?P<ion>[][A-Za-z0-9]+)\)(?P<ion_sub>\d+)?")
ion_re3 = re.compile(r"\[(?P<ion>[][A-Za-z0-9]+)\](?P<ion_sub>\d+)?")
# TODO: check universality
cond_temp_re = re.compile(
    r"<i>\u039B</i>/S cm<sup>2</sup> mol<sup>-1</sup><br/>(?P<temp>(?:-)?\d+)"
)
# TODO: check universality
cond_conc_re = re.compile(
    r"<i>\u039B</i>/S cm<sup>2</sup> mol<sup>-1</sup><br/>(?P<conc>\d+\.\d+)"
)
activity_conc_re = re.compile(r"<i>\u03B3</i>\((?P<conc>\d+\.\d+) m\)")
DEFAULT_TEMPERATURE = 298.15
ION_TO_OXIDATION_STATE = {
    "F": -1,
    "Cl": -1,
    "Br": -1,
    "I": -1,
    "NO3": -1,
    "NO2": -1,
    "ClO4": -1,
    "ClO3": -1,
    "ClO2": -1,
    "ClO": -1,
    "HCO3": -1,
    "OH": -1,
    "CO3": -2,
    "SO4": -2,
    "PO4": -3,
    "H": 1,
    "Li": 1,
    "Na": 1,
    "K": 1,
    "Rb": 1,
    "Cs": 1,
    "Fr": 1,
    "Be": 2,
    "Mg": 2,
    "Ca": 2,
    "Sr": 2,
    "Ba": 2,
    "Ra": 2,
    "NH4": 1,
}


def parse_crc(d: dict[str, Any]) -> list[dict]:
    """Parse data from CRC."""
    dataset: list[BenchmarkEntry] = []
    solution: str = d.get("Mol. form.", d.get("Compound"))
    solution = solution.replace("<sub>", "")
    match = formula_re.search(solution)

    if not match:
        msg = f"Unable to parse formula: {solution}"
        raise ValueError(msg)

    num, denom = (match.group("coeff") or "1/1").split("/")
    factor = int(num) / int(denom)
    formula = match.group("formula")
    salt = formula_to_salt(formula)

    for k, v in d.items():
        prop = "conductivity"
        temp = DEFAULT_TEMPERATURE

        if match := cond_temp_re.search(k):
            temp = float(match.group("temp")) + 273.15

        if conc_match := cond_conc_re.search(k):
            units = "mol/L"
        elif conc_match := activity_conc_re.search(k):
            units = "mol/kg"
            prop = "mean_activity"
        else:
            continue

        conc = float(conc_match.group("conc")) * factor, units
        solutes = salt_to_solutes(salt, conc)
        soln = Solution(solutes=solutes, temperature=f"{temp} K")
        soln_data = [(prop, float(v))]
        entry = BenchmarkEntry(solution=soln, solution_data=soln_data)
        dataset.append(entry)

    return dataset
