package com.oracle.coherence.python.testing;


import com.tangosol.util.Base;
import com.tangosol.util.InvocableMap;
import java.util.Map;
import java.util.Set;


public class LongRunningProcessor
        implements InvocableMap.EntryProcessor<Object, Object, Void>
    {
    public Void process(InvocableMap.Entry<Object, Object> entry)
        {
        Base.sleep(5000);
        return null;
        }

    public Map<Object, Void> processAll(Set<? extends InvocableMap.Entry<Object, Object>> setEntries)
        {
        Base.sleep(5000);
        return InvocableMap.EntryProcessor.super.processAll(setEntries);
        }
    }
