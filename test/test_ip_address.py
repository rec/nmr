import pytest

from nmr.nmr import Nmr
from nmr.types.ip_address import IP


@pytest.mark.parametrize(
    "text,value,use_ip6",
    [
        ("0.0.0.0", 0, False),
        ("255.255.255.255", 2**32 - 1, False),
        ("::", 0, True),
        ("::1", 1, True),
        ("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", 2**128 - 1, True),
    ],
)
def test_ip_family_flag_distinguishes_the_full_address_domains(
    text: str, value: int, use_ip6: bool
) -> None:
    address = IP(value=value, use_ip6=use_ip6)
    index = IP.str_to_index(text)
    assert index == 2 * address.value + address.use_ip6
    assert IP.index_to_str(index) == text
    result = Nmr().encode(text, "ip")
    assert result.truename.startswith("ip:")
    assert Nmr().decode(result.truename).value == text


@pytest.mark.parametrize(
    "use_ip6,limit,text", [(False, 2**32, "0.0.0.0"), (True, 2**128, "::")]
)
def test_ip_browsing_wraps_within_the_selected_family(
    use_ip6: bool, limit: int, text: str
) -> None:
    index = 2 * limit + use_ip6
    with pytest.raises(ValueError, match="canonical domain"):
        IP.index_to_str(index)
    assert IP.index_to_str(index, browse=True) == text
    assert IP.str_to_index(text) == int(use_ip6)
    with pytest.raises(ValueError, match="selected IP family"):
        IP(value=limit, use_ip6=use_ip6)


def test_ip_versions_are_one_registered_type_without_the_old_labels() -> None:
    engine = Nmr()
    assert engine.find_type("ip")[0] == "data:computer:ip"
    for name in ["ipv4", "ipv6"]:
        with pytest.raises(ValueError, match="Unknown"):
            engine.find_type(name)


def test_ip_rejects_negative_indices_and_addresses() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        IP.index_to_str(-1)
    with pytest.raises(ValueError, match="selected IP family"):
        IP(value=-1)
