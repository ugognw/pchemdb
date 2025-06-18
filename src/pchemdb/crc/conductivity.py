"""Utilities for parsin molar conductivity data from CRC."""

import re
from typing import Any

from pyEQL import Solution
from pyEQL.benchmark import BenchmarkEntry
from pyEQL.salt_ion_match import Salt
from pyEQL.utils import FormulaDict

formula_re = re.compile(r"(?P<coeff>\d+/\d+)?(?P<formula>.+)")
salt_re = re.compile(
    r"(?P<cation>[A-Z][a-z]{0,2})(?P<cation_sub>\d+)?(?P<anion>[A-Za-z0-9,()]+)"
)
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
    "pO4": -3,
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
}


def formula_to_salt(formula: str) -> Salt:
    """Convert a chemical formula into a Salt.

    Args:
        formula: A chemical formula (e.g., KCl, Na2SO4, etc.)

    Warning:
        This function does not work for formulas with polyatomic cations.
    """
    match = salt_re.match(formula)

    if match is None:
        msg = f"Unable to parse formula: {formula} to salt"
        raise ValueError(msg)

    cation = match.group("cation")
    cation_sub = int(match.group("cation_sub") or 1)
    anion = match.group("anion")
    anion_sub = 1

    if anion.startswith("("):
        anion_sub = int(anion[anion.index(")") + 1 :])
        anion = anion[1 : anion.index(")")]

    cation_ox_state = ION_TO_OXIDATION_STATE.get(cation, 0)

    if cation_ox_state != 0:
        anion_ox_state = cation_ox_state * cation_sub / anion_sub
    else:
        anion_ox_state = ION_TO_OXIDATION_STATE.get(cation, 0)

    if anion_ox_state != 0:
        cation_ox_state = anion_ox_state * anion_sub / cation_sub
    else:
        msg = f"Unable to determine oxidation states for formulat: {formula}"
        raise ValueError(msg)

    return Salt(
        cation=f"{cation}+{cation_ox_state}", anion=f"{anion}-{anion_ox_state}"
    )


def salt_to_solutes(salt: Salt, conc: tuple[float, str]) -> FormulaDict:
    """Create a dictionary mapping solute ions to concentration quantities as required by the Solution constructor.

    Args:
        salt: A Salt object
        conc: A tuple (magnitude, unit) representing the concentration of the salt to be used when creating the solute.
    """
    mag, unit = conc
    solutes = {
        salt.cation: f"{mag * salt.nu_cation} {unit}",
        salt.anion: f"{mag * salt.nu_anion} {unit}",
    }
    return FormulaDict(**solutes)


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
