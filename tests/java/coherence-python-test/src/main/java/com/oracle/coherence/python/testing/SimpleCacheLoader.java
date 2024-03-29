/*
 * Copyright (c) 2022 Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */


package com.oracle.coherence.python.testing;

import com.tangosol.net.cache.CacheLoader;

/**
 * A simple {@link CacheLoader} implementation to demonstrate basic functionality.
 *
 * @author Tim Middleton 2020.02.17
 */
public class SimpleCacheLoader
        implements CacheLoader<Integer, String> {

    private String cacheName;

    /**
     * Constructs a {@link SimpleCacheLoader}.
     *
     * @param cacheName cache name
     */
    public SimpleCacheLoader(String cacheName) {
        this.cacheName = cacheName;
    }

    /**
     * An implementation of a load which returns the String "Number " + the key.
     *
     * @param key key whose associated value is to be returned
     * @return the value for the given key
     */
    @Override
    public String load(Integer key) {  // <3>
        return "Number " + key;
    }
}
