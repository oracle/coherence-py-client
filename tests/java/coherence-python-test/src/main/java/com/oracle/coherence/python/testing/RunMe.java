/*
 * Copyright (c) 2022 Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */


package com.oracle.coherence.python.testing;


import com.oracle.coherence.io.json.JsonObject;
import com.oracle.coherence.io.json.JsonSerializer;

import com.tangosol.io.ByteArrayWriteBuffer;


import com.tangosol.net.CacheFactory;
import com.tangosol.net.NamedMap;
import com.tangosol.util.processor.VersionedPutAll;
import java.io.IOException;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.Map;

public class RunMe {
    public static void main(String[] args) throws IOException {
        JsonSerializer serializer = new JsonSerializer();
        Map<Integer, String> map = new HashMap<>();
        map.put(1, "one");
        map.put(2, "two");

        System.setProperty("coherence.io.json.debug", "true");

//                BigInteger val = new BigInteger("100");
//                BigDecimal val = new BigDecimal(100);
                Integer val = 100;

                ByteArrayWriteBuffer buf = new ByteArrayWriteBuffer(512);
                serializer.serialize(buf.getBufferOutput(), val);
                System.out.println(new String(buf.toByteArray()));

        String value = "{\"@class\":\"processor.VersionedPutAll\",\"entries\":{\"@class\":\"java.util.HashMap\",\"entries\":[{\"key\":4,\"value\":{\"@version\":1,\"id\":4,\"name\":\"Steve\",\"age\":40,\"salary\":0}},{\"key\":1,\"value\":{\"@version\":1,\"id\":1,\"name\":\"Tim\",\"age\":10,\"salary\":0}},{\"key\":2,\"value\":{\"@version\":1,\"id\":2,\"name\":\"Andrew\",\"age\":20,\"salary\":0}},{\"key\":3,\"value\":{\"@version\":1,\"id\":3,\"name\":\"John\",\"age\":30,\"salary\":0}}]},\"insert\":true}";

        VersionedPutAll obj = (VersionedPutAll) serializer.underlying().deserialize(value, Object.class);
        System.out.println(obj);

    }
}
