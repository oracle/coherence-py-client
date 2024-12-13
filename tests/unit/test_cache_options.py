import pytest

from coherence.client import CacheOptions
from coherence.local_cache import NearCacheOptions


def test_cache_options_default_expiry() -> None:
    options: CacheOptions = CacheOptions(-10)
    assert options.default_expiry == -1

    options = CacheOptions(10000)
    assert options.default_expiry == 10000


def test_near_cache_options_no_explicit_params() -> None:
    with pytest.raises(ValueError) as err:
        NearCacheOptions()

    assert str(err.value) == "at least one option must be specified"


def test_near_cache_options_negative_units() -> None:
    message: str = "values for high_units and high_units_memory must be positive"

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=-1)

    assert str(err.value) == message

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units_memory=-1)

    assert str(err.value) == message


def test_near_cache_options_both_units() -> None:
    message: str = "high_units and high_units_memory cannot be used together; specify one or the other"

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=1000, high_units_memory=10000)

    assert str(err.value) == message

    with pytest.raises(ValueError) as err:
        NearCacheOptions(ttl=10000, high_units=1000, high_units_memory=10000)

    assert str(err.value) == message


def test_near_cache_options_prune_factor() -> None:
    message: str = "prune_factor must be between .1 and 1"

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=100, prune_factor=-1)

    assert str(err.value) == message

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=100, prune_factor=0)

    assert str(err.value) == message

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=100, prune_factor=0.05)

    assert str(err.value) == message

    with pytest.raises(ValueError) as err:
        NearCacheOptions(high_units=100, prune_factor=1.001)

    assert str(err.value) == message


def test_near_cache_options_str() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=100)
    assert str(options) == "NearCacheOptions(ttl=0ms, high-units=100, high-units-memory=0, prune-factor=0.80)"

    options = NearCacheOptions(high_units=100, ttl=1000)
    assert str(options) == "NearCacheOptions(ttl=1000ms, high-units=100, high-units-memory=0, prune-factor=0.80)"

    options = NearCacheOptions(high_units_memory=100 * 1024)
    assert str(options) == "NearCacheOptions(ttl=0ms, high-units=0, high-units-memory=102400, prune-factor=0.80)"

    options = NearCacheOptions(high_units_memory=100 * 1024, prune_factor=0.25)
    assert str(options) == "NearCacheOptions(ttl=0ms, high-units=0, high-units-memory=102400, prune-factor=0.25)"


def test_near_cache_eq() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=100)
    options2: NearCacheOptions = NearCacheOptions(high_units=100, ttl=1000)
    options3: NearCacheOptions = NearCacheOptions(high_units=100)

    assert options == options
    assert options != options2
    assert options == options3
    assert options != "some string"


def test_near_cache_options_ttl() -> None:
    options = NearCacheOptions(ttl=1000)
    assert options.ttl == 1000

    # ensure minimum can be set
    options = NearCacheOptions(ttl=250)
    assert options.ttl == 250


def test_near_cache_ttl_negative() -> None:
    with pytest.raises(ValueError) as err:
        NearCacheOptions(ttl=-1)

    assert str(err.value) == "ttl cannot be less than zero"

    with pytest.raises(ValueError) as err:
        NearCacheOptions(ttl=100)

    assert str(err.value) == "ttl has 1/4 second resolution;  minimum TTL is 250"


def test_near_cache_options_high_units() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=10000)
    assert options.high_units == 10000


def test_near_cache_options_high_units_memory() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units_memory=10000)
    assert options._high_units_memory == 10000


def test_cache_options_str() -> None:
    options: CacheOptions = CacheOptions(10000)
    assert str(options) == "CacheOptions(default-expiry=10000)"

    options = CacheOptions(5000, NearCacheOptions(high_units=10000))
    assert (
        str(options) == "CacheOptions(default-expiry=5000, near-cache-options=NearCacheOptions(ttl=0ms,"
        " high-units=10000, high-units-memory=0, prune-factor=0.80))"
    )


def test_cache_options_eq() -> None:
    options: CacheOptions = CacheOptions(10000)
    options2: CacheOptions = CacheOptions(10000)
    options3: CacheOptions = CacheOptions(1000)

    assert options == options
    assert options == options2
    assert options != options3

    options = CacheOptions(10000, NearCacheOptions(high_units=10000))
    options2 = CacheOptions(10000, NearCacheOptions(high_units=10000))
    options3 = CacheOptions(10000, NearCacheOptions(high_units=1000))

    assert options == options
    assert options == options2
    assert options != options3
