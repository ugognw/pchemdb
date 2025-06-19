import csv
import json
from pathlib import Path

import pytest

from pchemdb.crc.conductivity import parse_crc

MOLAR_CONDUCTIVITY_SOURCES = [
    "Molar Electrical Conductivity of Aqueous HBr as a Function of Temperature and Concentration.csv",
    "Molar Electrical Conductivity of Aqueous HCl as a Function of Temperature and Concentration.csv",
    "Molar Electrical Conductivity of Aqueous Hydro-Halogen Acids at 25C as a Function of Concentration.csv",
    "Molar Electrical Conductivity of Electrolytes in Aqueous Solution at 25C as a Function of Concentration.csv",
]


@pytest.fixture(name="source", params=[])
def fixture_source(request: pytest.FixtureRequest, datadir: Path) -> Path:
    source: str = datadir.joinpath(request.param)
    return source


@pytest.fixture(name="sources", params=[])
def fixture_sources(
    request: pytest.FixtureRequest, datadir: Path
) -> list[Path]:
    sources = [datadir.joinpath(p) for p in request.param]
    return sources


class ParseCRC:
    _label = "CRC"

    @staticmethod
    def test_should_parse_sources(source: Path) -> None:
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

    def test_should_create_json_database(self, sources: list[Path]) -> None:
        dataset = []
        for filename in sources:
            with filename.open(mode="r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        dataset.extend(parse_crc(row))
                    except ValueError as err:
                        if "picrate" in err.args[0]:
                            pass

        with Path(f"{self._label}.json").open(
            mode="w", encoding="utf-8"
        ) as file:
            json.dump(dataset, file, indent=4)


class TestParseMolarElectricalConductivity(ParseCRC):
    _label = "molar_conductivity"

    @staticmethod
    @pytest.fixture(name="source", params=MOLAR_CONDUCTIVITY_SOURCES)
    def fixture_source(request: pytest.FixtureRequest, datadir: Path) -> Path:
        source: Path = datadir.joinpath(request.param)
        return source

    @staticmethod
    @pytest.fixture(name="sources", params=[MOLAR_CONDUCTIVITY_SOURCES])
    def fixture_sources(
        request: pytest.FixtureRequest, datadir: Path
    ) -> list[Path]:
        sources = [datadir.joinpath(p) for p in request.param]
        return sources
