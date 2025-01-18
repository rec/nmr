from __future__ import annotations

import ipaddress

from ..categories import Computer
from ..nameable_type import NameableType


class IPv4Address(NameableType[ipaddress.IPv4Address]):
    category = Computer.IP_V4_ADDRESS


class IPv6Address(NameableType[ipaddress.IPv6Address]):
    category = Computer.IP_V6_ADDRESS
