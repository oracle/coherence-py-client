# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations


class Address:
    def __init__(self, street: str, city: str, state: str, zipcode: int, country: str):
        self.street = street
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.country = country

    @classmethod
    def address(cls, street: str, city: str, state: str, zipcode: int, country: str) -> Address:
        return Address(street, city, state, zipcode, country)
