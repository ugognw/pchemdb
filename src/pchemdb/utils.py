"""Utilities for parsin molar conductivity data from CRC."""

import re

from pyEQL.salt_ion_match import Salt
from pyEQL.utils import FormulaDict

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
}


def formula_to_salt(formula: str) -> Salt:
    """Convert a chemical formula into a Salt.

    Args:
        formula: A chemical formula written with the cation first (e.g., KCl,
            Na2SO4, etc.).

    Warning:
        This function does not work for formulas with polyatomic cations.
    """

    def _parse_ion(ion: str, res: list[re.Pattern]) -> re.Match[str] | None:
        match = None
        for ion_re in res:
            match = ion_re.match(ion) or match

        return match

    cation_match = _parse_ion(formula, [ion_re1, ion_re2, ion_re3])

    if cation_match is None:
        msg = f"Unable to parse formula: {formula} to salt"
        raise ValueError(msg)

    cation = cation_match.group("ion")
    cation_sub = int(cation_match.group("ion_sub") or 1)
    anion = formula.removeprefix(cation_match[0])
    cation_match = _parse_ion(formula, [ion_re1, ion_re2, ion_re3])
    anion_match = _parse_ion(
        anion, [re.compile(ion_re1.pattern + "$"), ion_re2, ion_re3]
    )

    if anion_match:
        anion = anion_match.group("ion")
        anion_sub = int(anion_match.group("ion_sub") or 1)
    else:
        anion_sub = 1

    cation_ox_state = ION_TO_OXIDATION_STATE.get(cation, 0)

    if cation_ox_state != 0:
        anion_ox_state = -int(cation_ox_state * cation_sub / anion_sub)
    else:
        anion_ox_state = ION_TO_OXIDATION_STATE.get(anion, 0)

    if anion_ox_state != 0:
        cation_ox_state = -int(anion_ox_state * anion_sub / cation_sub)
    else:
        msg = f"Unable to determine oxidation states for formulat: {formula}"
        raise ValueError(msg)

    return Salt(
        cation=f"{cation}{cation_ox_state:+}",
        anion=f"{anion}{anion_ox_state:+}",
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
