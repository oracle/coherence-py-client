/*
 * Copyright (c) 2022 Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

package com.oracle.coherence.python.testing;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import com.tangosol.net.CacheFactory;
import com.tangosol.net.Cluster;
import com.tangosol.net.DefaultCacheServer;
import com.tangosol.net.NamedCache;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import com.tangosol.net.management.MBeanServerProxy;

/**
 * A simple Http server that is deployed into a Coherence cluster
 * and can be used to perform various tests.
 *
 * @author jk  2019.08.09
 * @author tam  2022.02.08
 */
public class RestServer {

    /**
     * Private constructor.
     */
    private RestServer() {
    }

    /**
     * Program entry point.
     *
     * @param args the program command line arguments
     */
    public static void main(String[] args) {
        try {
            System.setProperty("coherence.cacheconfig", "test-cache-config.xml");
            int        port   = Integer.parseInt(System.getProperty("test.rest.port", "8080"));
            HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

            server.createContext("/ready", RestServer::ready);
            server.createContext("/env", RestServer::env);
            server.createContext("/props", RestServer::props);
            server.createContext("/suspend", RestServer::suspend);
            server.createContext("/resume", RestServer::resume);
            server.createContext("/populate", RestServer::populate);
            server.createContext("/edition", RestServer::edition);
            server.createContext("/version", RestServer::version);
            server.createContext("/cache", RestServer::cache);
            server.createContext("/balanced", RestServer::balanced);
            server.createContext("/checkCustomerCache", RestServer::checkCustomerCache);

            server.setExecutor(null); // creates a default executor
            server.start();

            System.out.println("REST server is UP! http://localhost:" + server.getAddress().getPort());

        }
        catch (Throwable thrown) {
            throw new RuntimeException("Failed to start http server", thrown);
        }


        DefaultCacheServer.main(args);
    }

    private static void send(HttpExchange t, int status, String body) throws IOException {
        t.sendResponseHeaders(status, body.length());
        OutputStream os = t.getResponseBody();
        os.write(body.getBytes());
        os.close();
    }

    private static void ready(HttpExchange t) throws IOException {
        send(t, 200, "OK");
    }

    private static void env(HttpExchange t) throws IOException {
        String data = System.getenv()
                            .entrySet()
                            .stream()
                            .map(e->String.format("{\"%s\":\"%s\"}", e.getKey(), e.getValue()))
                            .collect(Collectors.joining(",\n"));

        send(t, 200, "[" + data + "]");
    }

    private static void props(HttpExchange t) throws IOException {
        String data = System.getProperties()
                            .entrySet()
                            .stream()
                            .map(e->String.format("{\"%s\":\"%s\"}", e.getKey(), e.getValue()))
                            .collect(Collectors.joining(",\n"));

        send(t, 200, "[" + data + "]");
    }

    private static void cache(HttpExchange t) throws IOException {
        try {
            String query = t.getRequestURI().getQuery();
            if (query != null) {
                StringBuilder sb = new StringBuilder();
                NamedCache    nc = CacheFactory.getCache(query);
                sb.append("\nCache Name: " + nc.getCacheName() + ", Size: " + nc.size());

                for (Object e : nc.keySet()) {
                    sb.append("\nKey: ").append(e).append(" Value: ").append(nc.get(e)).append("\n");
                }
                send(t, 200, sb.toString());
                return;
            }
        }
        catch (Exception e) {
            System.out.println(e.getMessage());
            e.printStackTrace();
             send(t, 400, e.getMessage());
             return;
        }
    }

    private static void suspend(HttpExchange t) throws IOException {
        Cluster cluster = CacheFactory.ensureCluster();
        cluster.suspendService("PartitionedCache");
        send(t, 200, "OK");
    }

    private static void resume(HttpExchange t) throws IOException {
        Cluster cluster = CacheFactory.ensureCluster();
        cluster.resumeService("PartitionedCache");
        send(t, 200, "OK");
    }

    private static void populate(HttpExchange t) throws IOException {
        populateCache(CacheFactory.getCache("cache-1"), 100);
        populateCache(CacheFactory.getCache("cache-2"), 100);
        send(t, 200, "OK");
    }


    private static void checkCustomerCache(HttpExchange t) throws IOException {
        // validate that the customer object for key 1 is in fact a Customer object for the given cache
        try {
            String cacheName = t.getRequestURI().getPath().replace("/checkCustomerCache/", "");
            NamedCache<Integer, Customer> customers = CacheFactory.getCache(cacheName);
            Customer customer = customers.get(1);
            if (!"Tim".equals(customer.getCustomerName())) {
                throw new RuntimeException("Could not get customer name");
            }
            if (!"Iluka".equals(customer.getHomeAddress().getSuburb())) {
                throw new RuntimeException("Could not get home address");
            }
        }
        catch (Exception e) {
            e.printStackTrace();
            send(t, 400, "Unable to retrieve customer 1: " + e.getMessage());
        }
        send(t, 200, "");
    }

    private static void edition(HttpExchange t) throws IOException {
        send(t, 200, CacheFactory.getEdition());
    }

    private static void version(HttpExchange t) throws IOException {
        send(t, 200, CacheFactory.VERSION);
    }

    private static void populateCache(NamedCache<Integer, String> cache, int count) {
        cache.clear();
        Map<Integer, String> map = new HashMap<>();

        for (int i = 0; i < count; i++) {
            map.put(i, "value-" + i);
            if (count % 1000 == 0) {
                cache.putAll(map);
                map.clear();
            }
        }
        if (!map.isEmpty()) {
            cache.putAll(map);
        }
    }

    private static void balanced(HttpExchange t) throws IOException {
        boolean     isCommercial = !CacheFactory.getEdition().equalsIgnoreCase("CE");

        // always add Base services
        Set<String> setServices = BASE_SERVICES;

        CacheFactory.log("Checking for the following balanced services: " + setServices, CacheFactory.LOG_INFO);

        // check the status of each of the services and ensure they are not ENDANGERED
        MBeanServerProxy proxy = CacheFactory.ensureCluster().getManagement().getMBeanServerProxy();
        if (proxy == null) {
            send(t, 200, "MBeanServerProxy not ready");
        }

        for (String s : setServices) {
            String statusHA = (String) proxy.getAttribute("Coherence:type=Service,name=" + s + ",nodeId=1", "StatusHA");
            if (ENDANGERED.equals(statusHA)) {
                // fail fast
                send(t, 200, "Service " + s + " is still " + ENDANGERED + ".\nFull list is: " + setServices);
            }
        }

        CacheFactory.log("All services balanced", CacheFactory.LOG_INFO);
        // all ok, then success
        send(t, 200, "OK");
    }

    private static final Set<String> BASE_SERVICES =
            new HashSet<>(Arrays.asList("PartitionedCache", "PartitionedCacheTouch", "CanaryService"));
    private static final String ENDANGERED = "ENDANGERED";

}
