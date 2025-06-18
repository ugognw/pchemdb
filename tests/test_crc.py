import csv
from pathlib import Path

import pytest

from pchemdb.crc.conductivity import parse_crc


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
