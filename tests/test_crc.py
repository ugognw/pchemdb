import csv
import json
from pathlib import Path

import pytest

from pchemdb.crc.conductivity import parse_crc

CRC_SOURCES = [
    "Molar Electrical Conductivity of Aqueous HBr as a Function of Temperature and Concentration",
    "Molar Electrical Conductivity of Aqueous HCl as a Function of Temperature and Concentration",
    "Molar Electrical Conductivity of Aqueous Hydro-Halogen Acids at 25C as a Function of Concentration",
    "Molar Electrical Conductivity of Electrolytes in Aqueous Solution at 25C as a Function of Concentration",
]


class TestParseMolarElectricalConductivity:
    @staticmethod
    @pytest.fixture(
        name="source",
        params=CRC_SOURCES,
    )
    def fixture_source(request: pytest.FixtureRequest) -> Path:
        source = Path(__file__).parent.joinpath(
            "crc", "molar_conductivity", request.param + ".csv"
        )
        return source

    @staticmethod
    def test_should_parse_crc(source: Path) -> None:
        with source.open(mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            dataset = []
            for row in reader:
                try:
                    dataset.extend(parse_crc(row))
                except ValueError as err:
                    if "picrate" in err.args[0]:
                        pass
        assert dataset

    @staticmethod
    def test_should_create_json_database() -> None:
        dataset = []
        for filestem in CRC_SOURCES:
            source = Path(__file__).parent.joinpath(
                "crc", "molar_conductivity", filestem + ".csv"
            )
            with source.open(mode="r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        dataset.extend(parse_crc(row))
                    except ValueError as err:
                        if "picrate" in err.args[0]:
                            pass

        with Path("CRC.json").open(mode="w", encoding="utf-8") as file:
            json.dump(dataset, file, indent=4)
