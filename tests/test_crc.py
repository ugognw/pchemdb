import csv
from pathlib import Path

from pyEQL.salt_ion_match import Salt
import pytest

from pchemdb.crc.conductivity import formula_to_salt
from pchemdb.crc.conductivity import parse_crc


@pytest.fixture(
    name="salt",
)
def fixture_salt(formula: str) -> Salt:
    return formula_to_salt(formula)


class TestFormulaToSalt:
    @staticmethod
    @pytest.mark.parametrize(
        ("formula", "cation", "anion"),
        [
            ("NaCl", ("Na", 1), ("Cl", -1)),
            ("KBr", ("K", 1), ("Br", -1)),
            ("CsI", ("Cs", 1), ("I", -1)),
        ],
    )
    def test_should_create_salts_with_monovalent_ions(
        cation: tuple[str, int], anion: tuple[str, int], salt: Salt
    ) -> None:
        assert f"{cation[0]}[{cation[1]:+}]" in salt.cation
        assert cation[1] == salt.z_cation
        assert f"{anion[0]}[{anion[1]:+}]" in salt.anion
        assert anion[1] == salt.z_anion

    @staticmethod
    @pytest.mark.parametrize(
        ("formula", "cation", "anion"),
        [
            ("CaCl2", ("Ca", 2), ("Cl", -1)),
            ("MgCl2", ("Mg", 2), ("Cl", -1)),
        ],
    )
    def test_should_create_salts_with_polyvalent_ions(
        cation: tuple[str, int], anion: tuple[str, int], salt: Salt
    ) -> None:
        assert f"{cation[0]}[{cation[1]:+}]" in salt.cation
        assert cation[1] == salt.z_cation
        assert f"{anion[0]}[{anion[1]:+}]" in salt.anion
        assert anion[1] == salt.z_anion

    @staticmethod
    @pytest.mark.parametrize(
        ("formula", "cation", "anion"),
        [
            ("Na2CO3", ("Na", 1), ("CO3", -2)),
            ("AgNO3", ("Ag", 1), ("NO3", -1)),
            ("Ca(OH)2", ("Ca", 2), ("OH", -1)),
            ("MgCl2", ("Mg", 2), ("Cl", -1)),
            ("KSCN", ("K", 1), ("SCN", -1)),
            ("LiClO4", ("Li", 1), ("ClO4", -1)),
            ("H2SO4", ("H", 1), ("SO4", -2)),
        ],
    )
    def test_should_create_salts_with_polyatomic_ions(
        cation: tuple[str, int], anion: tuple[str, int], salt: Salt
    ) -> None:
        assert f"{cation[0]}[{cation[1]:+}]" in salt.cation
        assert cation[1] == salt.z_cation
        assert f"{anion[0]}[{anion[1]:+}]" in salt.anion
        assert anion[1] == salt.z_anion

    @staticmethod
    @pytest.mark.xfail
    @pytest.mark.parametrize(
        ("formula", "cation", "anion"), [("NH4Cl", ("NH4", 1), ("Cl", 1))]
    )
    def test_should_create_salts_with_polyatomic_cations(
        cation: tuple[str, int], anion: tuple[str, int], salt: Salt
    ) -> None:
        assert f"{cation[0]}[{cation[1]:+}]" in salt.cation
        assert cation[1] == salt.z_cation
        assert f"{anion[0]}[{anion[1]:+}]" in salt.anion
        assert anion[1] == salt.z_anion


class TestParseMolarElectricalConductivity:
    @staticmethod
    @pytest.fixture(
        name="source",
        params=[
            "Molar Electrical Conductivity of Aqueous HBr as a Function of Temperature and Concentration",
            "Molar Electrical Conductivity of Aqueous HCl as a Function of Temperature and Concentration",
            "Molar Electrical Conductivity of Aqueous Hydro-Halogen Acids at 25C as a Function of Concentration",
            "Molar Electrical Conductivity of Electrolytes in Aqueous Solution at 25C as a Function of Concentration",
        ],
    )
    def fixture_source(request: pytest.FixtureRequest) -> Path:
        source = Path(__file__).parent.joinpath(
            "crc", "molar_conductivity", request.param + ".csv"
        )
        return source

    @staticmethod
    def test_should_parse_crc(source: Path) -> None:
        with source.open(mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            dataset = []
            for row in reader:
                dataset.extend(parse_crc(row))
        assert dataset
