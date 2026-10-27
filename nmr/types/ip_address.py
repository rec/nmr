from __future__ import annotations

import ipaddress
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, model_validator

from ..type_name import TypeNamer
from .bounded import bounded


class IP(BaseModel, TypeNamer, frozen=True):
    value: int
    use_ip6: bool = False
    label: ClassVar[str] = "ip"
    description: ClassVar[str] = "IPv4 or IPv6 address without an interface scope"

    @model_validator(mode="after")
    def validate_address(self) -> IP:
        if not 0 <= self.value < 2 ** (128 if self.use_ip6 else 32):
            raise ValueError("Address is outside the selected IP family")
        return self

    @staticmethod
    def str_to_index(value: str) -> int:
        if "%" in value:
            raise ValueError("Scoped IPv6 addresses are not supported")
        address = ipaddress.ip_address(value)
        return 2 * int(address) + (address.version == 6)

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        use_ip6 = bool(index & 1)
        address = IP(
            value=bounded(index // 2, 2 ** (128 if use_ip6 else 32), browse),
            use_ip6=use_ip6,
        )
        address_type = (
            ipaddress.IPv6Address if address.use_ip6 else ipaddress.IPv4Address
        )
        return str(address_type(address.value))

    model_config = ConfigDict(strict=True)
