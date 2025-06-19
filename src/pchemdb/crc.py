"""Utilities for parsing CRC data.

Example: Parse CRC CSV into data structure

>>> from csv import DictReader
>>> from pchemdb.crc import parse_crc
>>> with Path(...).open(mode="r", encoding=...) as file:
...     reader = DictReader(file)
...     data = []
...     for row in reader:
...         data.extend(parse_crc)
"""

from importlib.resources import files
import json
import logging
import re
from typing import Any
from typing import NamedTuple

from pint import Quantity
from pyEQL import ureg

from pchemdb.utils import formula_to_salt

logger = logging.getLogger(__name__)

formula_re = re.compile(r"(?P<coeff>\d+/\d+)?(?P<formula>.+)")
# aqueous HBr/HCl
molar_cond_temp_re = re.compile(
    "<i>\u039b</i>/"
    r"S cm<sup>2</sup> mol<sup>-1</sup><br/>(?:(?P<sign>.)?(?P<temp>\d+.+C))"
)
# aqueous hydro-halogen acids
molar_cond_conc_re1 = re.compile(
    "<i>\u039b</i>/"
    r"S cm<sup>2</sup> mol<sup>-1</sup><br/>(?P<conc>\d+\.\d+)"
)
# aqueous electrolytes
molar_cond_conc_re2 = re.compile(
    "<i>\u039b</i>"
    r"<sup></sup>\((?P<conc>\d+\.\d+) M\)/S cm<sup>2 </sup>mol<sup>-1</sup>"
)
cond_conc_re = re.compile("<i>\u03ba</i>" r"\((?P<conc>\d+(\.\d+)?)%\)")
activity_conc_re = re.compile("<i>\u03b3</i>" r"\((?P<conc>\d+\.\d+) m\)")
xml_tags_re = re.compile(r"<(/)?[^>]+>")
DEFAULT_TEMPERATURE = "298.15 K"
_CONDUCTIVITY_CONC_KEY = "<i>c</i>/M"
_CONDUCTIVITY_UNITS = "S/m"
_CONCENTRATION_UNITS = "mol/L"
_TEMPERATURE_UNITS = "K"
DB_FILE = "crc.json"


class _ParseResult(NamedTuple):
    prop: str
    conc: Quantity
    temp: Quantity
    value: Quantity


def _parse_temperature_dependent_molar_conductivity(
    d: dict[str, str], factor: float, temp: str, v: str
) -> _ParseResult:
    conc_units = _CONCENTRATION_UNITS
    prop = "conductivity"
    prop_units = "S cm ** 2 /mol"

    conc_mag = float(d[_CONDUCTIVITY_CONC_KEY])
    conc = ureg.Quantity(conc_mag, conc_units) * factor
    value = conc * ureg.Quantity(float(v), prop_units)

    return _ParseResult(
        prop=prop,
        conc=conc,
        temp=ureg.Quantity(temp),
        value=value.to(_CONDUCTIVITY_UNITS),
    )


def _parse_concentration_dependent_molar_conductivity(
    factor: float, conc_mag: float, v: str
) -> _ParseResult:
    conc_units = _CONCENTRATION_UNITS
    prop = "conductivity"
    prop_units = "S cm ** 2 /mol"

    temp = DEFAULT_TEMPERATURE
    conc = ureg.Quantity(conc_mag, conc_units) * factor
    value = conc * ureg.Quantity(float(v), prop_units)

    return _ParseResult(
        prop=prop,
        conc=conc,
        temp=ureg.Quantity(temp),
        value=value.to(_CONDUCTIVITY_UNITS),
    )


def _parse_concentration_dependent_conductivity(
    factor: float, target_conc: float, v: str
) -> _ParseResult:
    conc_units = _CONCENTRATION_UNITS
    prop = "conductivity"
    prop_units = "mS / cm"

    temp = "20 degC"
    # Store concentration not as true weight percent, but as wt% of
    # solution required to be added to achieve reported wt%
    # This is required because when adding solutes based on weight
    # percent, pyEQL adds the solute in an amount equal to the weight
    # percent instead of adding the amount of solute required to for
    # the solute to attain the specified weight percent
    conc_mag = target_conc / (100 - target_conc)
    conc_units = "%"
    conc = ureg.Quantity(conc_mag, conc_units) * factor
    value = conc * ureg.Quantity(float(v), prop_units)

    return _ParseResult(
        prop=prop,
        conc=conc,
        temp=ureg.Quantity(temp),
        value=value.to(_CONDUCTIVITY_UNITS),
    )


def _parse_mean_activity_coefficient(
    factor: float, conc_mag: float, v: str
) -> _ParseResult:
    conc_units = "mol/kg"
    prop = "mean_activity_coefficient"
    prop_units = "dimensionless"

    temp = DEFAULT_TEMPERATURE
    conc = ureg.Quantity(conc_mag, conc_units) * factor
    value = ureg.Quantity(float(v), prop_units)

    return _ParseResult(
        prop=prop,
        conc=conc,
        temp=ureg.Quantity(temp),
        value=value,
    )


def parse_crc(
    d: dict[str, Any],
) -> list[
    tuple[
        dict[str, Any], dict[str, list[tuple[str, str]]], list[tuple[str, str]]
    ]
]:
    """Parse data from CRC.

    Args:
        d: A dictionary corresponding to a row in a CRC .csv file.

    Returns:
        A list of 3-tuples (``solution``, ``solute_data``, ``solution_data``),
        where each item represents a property entry. ``solution`` is a
        dictionary mapping :class:`pyEQL.solution.Solution` constructor
        parameter names to their values. ``solute_data`` is a dictionary mapping
        solutes formulae to list of property-value pairs. ``solution_data`` is a
        list of property-value pairs.
    """
    dataset: list[
        tuple[
            dict[str, Any],
            dict[str, list[tuple[str, str]]],
            list[tuple[str, str]],
        ]
    ] = []
    compound = str(d.get("Mol. form.", d.get("Compound")))
    solution = xml_tags_re.sub("", compound)
    match = formula_re.search(solution)

    if not match:
        msg = f"Unable to parse formula: {solution}"
        raise ValueError(msg)

    num, denom = (match.group("coeff") or "1/1").split("/")
    factor = int(num) / int(denom)
    formula = match.group("formula")
    salt = formula_to_salt(formula)

    for k, v in d.items():
        if k is None or not v:
            continue

        # If data key in temperature-dependent dataset,
        # read concentration from "<i>c,<\i>/M" key
        # read temperature from cond_temp_re
        if match := molar_cond_temp_re.search(k):
            res = _parse_temperature_dependent_molar_conductivity(
                d, factor, match.group("temp"), v
            )

        # If data key in concentration-dependent dataset,
        # read concentration from conc_re (activity or conductivity)
        # use dataset temperature
        elif (conc_match := molar_cond_conc_re1.search(k)) or (
            conc_match := molar_cond_conc_re2.search(k)
        ):
            res = _parse_concentration_dependent_molar_conductivity(
                factor, float(conc_match.group("conc")), v
            )
        elif conc_match := cond_conc_re.search(k):
            res = _parse_concentration_dependent_conductivity(
                factor, float(conc_match.group("conc")), v
            )
        elif conc_match := activity_conc_re.search(k):
            res = _parse_mean_activity_coefficient(
                factor, float(conc_match.group("conc")), v
            )
        else:
            continue

        solutes = {
            salt.cation: f"{res.conc.m * salt.nu_cation} {res.conc.units}",
            salt.anion: f"{res.conc.m * salt.nu_anion} {res.conc.units}",
        }
        soln = {
            "solutes": solutes,
            "temperature": str(res.temp.to(_TEMPERATURE_UNITS)),
        }
        solute_data: dict[str, list[tuple[str, str]]] = {}
        soln_data = [(res.prop, f"{res.value.m} {res.value.units}")]
        entry = (soln, solute_data, soln_data)
        dataset.append(entry)

    return dataset


def load_crc_database() -> list[
    tuple[dict[str, str], dict[str, list[str]], list[str]]
]:
    """Load the CRC database."""
    json_db_file = files("pchemdb").joinpath("_database", DB_FILE)

    with json_db_file.open(mode="r", encoding="utf-8") as file:
        return json.load(file)
