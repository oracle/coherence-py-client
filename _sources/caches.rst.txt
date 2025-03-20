..
   Copyright (c) 2022, 2024, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Caches
======

Once a Session has been obtained, it is now possible to begin working with
`NamedMap` and/or `NamedCache` instances.  This is done by calling either
`Session.get_map(name: str, cache_options: Optional[CacheOptions] = None)` or
`Session.get_cache(name: str, cache_options: Optional[CacheOptions] = None)`.
The `name` argument is the logical name for this cache.  The optional `cache_options`
argument accepts a `CacheOptions` to configure the default time-to-live (ttl)
for entries placed in the cache as well as allowing the configuration of near
caching (discussed later in this section).

Here are some examples:

.. code-block:: python

  # obtain NamedCache 'person'
  cache: NamedCache[int, Person] = await session.get_cache("person")

.. code-block:: python

  # obtain NamedCache 'person' with a default ttl of 2000 millis
  # any entry inserted into this cache, unless overridden by a put call
  # with a custom ttl, will have a default ttl of 2000
  options: CacheOptions = CacheOptions(2000)
  cache: NamedCache[int, Person] = await session.get_cache("person", options)

Near Caches
===========

Near caches are a local cache within the `NamedMap` or `NamedCache`
that will store entries as they are obtained from the remote cache.  By doing
so, it is possible to reduce the number of remote calls made to the Coherence
cluster by returning the locally cached value.  This local cache also
ensures updates made to, or removal of, an entry are properly
reflected thus ensuring stale data isn't mistakenly returned.

.. note::
  Near caching will only work with Coherence CE `24.09` or later.  Attempting
  to use near caching features with older versions will have no effect.

A near cache is configured via `NearCacheOptions` which provides several
options for controlling how entries will be cached locally.

    - `ttl` - configures the time-to-live of locally cached entries (this has no
      impact on entries stored within Coherence).  If not specified, or the
      `ttl` is `0`, entries in the near cache will not expire
    - `high_units` - configures the max number of entries that may be locally
       cached.  Once the number of locally cached entries exceeds the configured
       value, the cache will be pruned down (least recently used entries first)
       to a target size based on the configured `prune_factor`
       (defaults to `0.80` meaning the prune operation would retain 80% of
       the entries)
    - `high_units_memory` - configures the maximum memory size, in bytes, the
       locally cached entries may use.  If total memory exceeds the configured
       value, the cache will be pruned down (least recently used entries first)
       to a target size based on the configured `prune_factor` (defaults to
       `0.80` meaning the prune operation would retain 80% the cache memory)
    - `prune_factor` - configures the target near cache size after exceeding
       either `high_units` or `high_units_memory` high-water marks

.. note::
  `high_units` and `high_units_memory` are mutually exclusive

Examples of configuring near caching:

.. code-block:: python

  # obtain NamedCache 'person' and configure near caching with a local
  # ttl of 20_000 millis
  near_options: NearCacheOptions = NearCacheOptions(20_000)
  cache_options: CacheOptions = CacheOptions(near_cache_options=near_options)
  cache: NamedCache[int, Person] = await session.get_cache("person", options)


.. code-block:: python

  # obtain NamedCache 'person' and configure near caching with a max
  # number of entries of 1_000 and when pruned, it will be reduced
  # to 20%
  near_options: NearCacheOptions = NearCacheOptions(high_units=1_000, prune_factor=0.20)
  cache_options: CacheOptions = CacheOptions(near_cache_options=near_options)
  cache: NamedCache[int, Person] = await session.get_cache("person", options)

To verify the effectiveness of a near cache, several statistics are monitored
and may be obtained from the `CacheStats` instance returned by the
`near_cache_stats` property of the `NamedMap` or `NamedCache`

The following statistics are available (the statistic name given is the same
property name on the `CacheStats` instance)

    - hits - the number of times an entry was found in the near cache
    - misses - the number of times an entry was not found in the near cache
    - misses_duration - The accumulated time, in millis, spent for a cache miss
      (i.e., having to make a remote call and update the local cache)
    - hit_rate - the ratio of hits to misses
    - puts - the total number of puts that have been made against the near cache
    - gets - the total number of gets that have been made against the near cache
    - prunes - the number of times the cache was pruned due to exceeding the
      configured `high_units` or `high_units_memory` high-water marks
    - expires - the number of times the near cache's expiry logic expired entries
    - num_pruned - the total number of entries that were removed due to exceeding the
      configured `high_units` or `high_units_memory` high-water marks
    - num_expired - the total number of entries that were removed due to
      expiration
    - prunes_duration - the accumulated time, in millis, spent pruning
      the near cache
    - expires_duration - the accumulated time, in millis, removing
      expired entries from the near cache
    - size - the total number of entries currently held by the near cache
    - bytes - the total bytes the near cache entries consume

.. note::
  The `near_cache_stats` option will return `None` if near caching isn't
  configured or available

The following example demonstrates the value that near caching can provide:

.. literalinclude:: ../examples/near_caching.py
    :language: python
    :linenos:
