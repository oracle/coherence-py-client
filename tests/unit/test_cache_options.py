import pytest

from coherence.client import CacheOptions, NearCacheOptions


def test_cache_options_default_expiry() -> None:
    options: CacheOptions = CacheOptions(-10)
    assert options.default_expiry == -1

    options = CacheOptions(10000)
    assert options.default_expiry == 10000


def test_near_cache_options_no_explicit_params() -> None:
    with pytest.raises(ValueError) as err:
        NearCacheOptions()

    assert str(err.value) == "at least one option must be specified and non-zero"


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


def test_near_cache_options_ttl() -> None:
    options: NearCacheOptions = NearCacheOptions(ttl=-10)
    assert options.ttl == -1

    options = NearCacheOptions(ttl=10)
    assert options.ttl == 10


def test_near_cache_options_high_units() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units=10000)
    assert options.high_units == 10000


def test_near_cache_options_high_units_memory() -> None:
    options: NearCacheOptions = NearCacheOptions(high_units_memory=10000)
    assert options._high_units_memory == 10000


def test_cache_options_str() -> None:
    options: CacheOptions = CacheOptions(10000)
    assert str(options) == "CacheOptions(default_expiry=10000)"

    options = CacheOptions(5000, NearCacheOptions(high_units=10000))
    assert (
        str(options) == "CacheOptions(default_expiry=5000, near_cache_options=NearCacheOptions(ttl=0,"
        " high_units=10000, high_units_memory=0))"
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
