# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from tests.address import Address


class Person:
    def __init__(self, name: str, gender: str, age: int, weight: float, address: Address, sports: list[str]):
        self.name = name
        self.gender = gender
        self.age = age
        self.weight = weight
        self.address = address
        self.sports = sports

    def __str__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Person):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @classmethod
    def person(cls, name: str, gender: str, age: int, weight: float, address: Address, sports: list[str]) -> Person:
        return Person(name, gender, age, weight, address, sports)

    @classmethod
    def Fred(cls) -> Person:
        addr = Address.address("1597 Olive Street", "San Francisco", "CA", 94102, "USA")
        return cls.person("Fred", "Male", 58, 185.5, addr, ["soccer", "tennis", "cricket"])

    @classmethod
    def Fiona(cls) -> Person:
        addr = Address.address("2382 Palm Ave", "Daly City", "CA", 94014, "USA")
        return cls.person("Fiona", "Female", 29, 118.5, addr, ["tennis", "hiking"])

    @classmethod
    def Pat(cls) -> Person:
        addr = Address.address("2038 Helford Lane", "Carmel", "IN", 46032, "USA")
        return cls.person("Pat", "Male", 62, 205.0, addr, ["golf", "pool", "curling"])

    @classmethod
    def Paula(cls) -> Person:
        addr = Address.address("4218 Daniel St", "Champaign", "IL", 61820, "USA")
        return cls.person("Paula", "Female", 35, 125.0, addr, ["swimming", "golf", "skiing"])

    @classmethod
    def Andy(cls) -> Person:
        addr = Address.address("1228 West Ave", "Miami", "FL", 33139, "USA")
        return cls.person("Andy", "Male", 25, 155.0, addr, ["soccer", "triathlon", "tennis"])

    @classmethod
    def Alice(cls) -> Person:
        addr = Address.address("2208 4th Ave", "Phoenix", "AZ", 85003, "USA")
        return cls.person("Alice", "Female", 22, 110.0, addr, ["golf", "running", "tennis"])

    @classmethod
    def Jim(cls) -> Person:
        addr = Address.address("37 Bowdoin St", "Boston", "MA", 2114, "USA")
        return cls.person("Jim", "Male", 36, 175.5, addr, ["golf", "football", "badminton"])