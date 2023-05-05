Search.setIndex({docnames:["aggregation","api_reference","api_reference/aggregator","api_reference/event","api_reference/extractor","api_reference/filter","api_reference/processor","basics","entryprocessing","events","index","installation","querying","serialization","sessions"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":5,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,sphinx:56},filenames:["aggregation.rst","api_reference.rst","api_reference/aggregator.rst","api_reference/event.rst","api_reference/extractor.rst","api_reference/filter.rst","api_reference/processor.rst","basics.rst","entryprocessing.rst","events.rst","index.rst","installation.rst","querying.rst","serialization.rst","sessions.rst"],objects:{"coherence.Aggregators":[[1,1,1,"","average"],[1,1,1,"","count"],[1,1,1,"","distinct"],[1,1,1,"","group_by"],[1,1,1,"","max"],[1,1,1,"","min"],[1,1,1,"","priority"],[1,1,1,"","record"],[1,1,1,"","reduce"],[1,1,1,"","script"],[1,1,1,"","sum"],[1,1,1,"","top"]],"coherence.Filters":[[1,1,1,"","all"],[1,1,1,"","always"],[1,1,1,"","any"],[1,1,1,"","array_contains"],[1,1,1,"","array_contains_all"],[1,1,1,"","array_contains_any"],[1,1,1,"","between"],[1,1,1,"","contains"],[1,1,1,"","contains_all"],[1,1,1,"","contains_any"],[1,1,1,"","equals"],[1,1,1,"","event"],[1,1,1,"","greater"],[1,1,1,"","greater_equals"],[1,1,1,"","is_in"],[1,1,1,"","is_none"],[1,1,1,"","is_not_none"],[1,1,1,"","less"],[1,1,1,"","less_equals"],[1,1,1,"","like"],[1,1,1,"","negate"],[1,1,1,"","never"],[1,1,1,"","not_equals"],[1,1,1,"","present"],[1,1,1,"","regex"]],"coherence.NamedCache":[[1,1,1,"","put"],[1,1,1,"","put_if_absent"]],"coherence.NamedMap":[[1,1,1,"","add_map_listener"],[1,1,1,"","aggregate"],[1,1,1,"","clear"],[1,1,1,"","contains_key"],[1,1,1,"","contains_value"],[1,1,1,"","destroy"],[1,1,1,"","entries"],[1,1,1,"","get"],[1,1,1,"","get_all"],[1,1,1,"","get_or_default"],[1,1,1,"","invoke"],[1,1,1,"","invoke_all"],[1,1,1,"","is_empty"],[1,1,1,"","keys"],[1,2,1,"","name"],[1,1,1,"","on"],[1,1,1,"","put"],[1,1,1,"","put_all"],[1,1,1,"","put_if_absent"],[1,1,1,"","release"],[1,1,1,"","remove"],[1,1,1,"","remove_map_listener"],[1,1,1,"","remove_mapping"],[1,1,1,"","replace"],[1,1,1,"","replace_mapping"],[1,1,1,"","size"],[1,1,1,"","truncate"],[1,1,1,"","values"]],"coherence.Options":[[1,3,1,"","DEFAULT_ADDRESS"],[1,3,1,"","DEFAULT_FORMAT"],[1,3,1,"","DEFAULT_REQUEST_TIMEOUT"],[1,3,1,"","DEFAULT_SCOPE"],[1,3,1,"","ENV_REQUEST_TIMEOUT"],[1,3,1,"","ENV_SERVER_ADDRESS"],[1,1,1,"","__init__"],[1,2,1,"","address"],[1,2,1,"","channel_options"],[1,2,1,"","format"],[1,2,1,"","request_timeout_seconds"],[1,2,1,"","scope"],[1,2,1,"","tls_options"]],"coherence.Processors":[[1,1,1,"","conditional_put"],[1,1,1,"","conditional_put_all"],[1,1,1,"","conditional_remove"],[1,1,1,"","extract"],[1,1,1,"","increment"],[1,1,1,"","invoke_accessor"],[1,1,1,"","invoke_mutator"],[1,1,1,"","multiply"],[1,1,1,"","nop"],[1,1,1,"","preload"],[1,1,1,"","script"],[1,1,1,"","touch"],[1,1,1,"","update"],[1,1,1,"","versioned_put"],[1,1,1,"","versioned_put_all"]],"coherence.Session":[[1,3,1,"","DEFAULT_FORMAT"],[1,1,1,"","__init__"],[1,2,1,"","channel"],[1,1,1,"","close"],[1,2,1,"","closed"],[1,2,1,"","format"],[1,2,1,"","options"],[1,2,1,"","scope"]],"coherence.TlsOptions":[[1,3,1,"","ENV_CA_CERT"],[1,3,1,"","ENV_CLIENT_CERT"],[1,3,1,"","ENV_CLIENT_KEY"],[1,1,1,"","__init__"],[1,2,1,"","ca_cert_path"],[1,2,1,"","client_cert_path"],[1,2,1,"","client_key_path"],[1,2,1,"","enabled"],[1,1,1,"","locked"]],"coherence.aggregator":[[2,0,1,"","AbstractComparableAggregator"],[2,0,1,"","AbstractDoubleAggregator"],[2,0,1,"","Aggregators"],[2,0,1,"","AverageAggregator"],[2,0,1,"","CompositeAggregator"],[2,0,1,"","CountAggregator"],[2,0,1,"","DistinctValuesAggregator"],[2,0,1,"","EntryAggregator"],[2,0,1,"","GroupAggregator"],[2,0,1,"","MaxAggregator"],[2,0,1,"","MinAggregator"],[2,0,1,"","PriorityAggregator"],[2,0,1,"","QueryRecorder"],[2,0,1,"","ReducerAggregator"],[2,0,1,"","Schedule"],[2,0,1,"","SumAggregator"],[2,0,1,"","Timeout"],[2,0,1,"","TopAggregator"]],"coherence.aggregator.AbstractComparableAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.AbstractDoubleAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.Aggregators":[[2,1,1,"","average"],[2,1,1,"","count"],[2,1,1,"","distinct"],[2,1,1,"","group_by"],[2,1,1,"","max"],[2,1,1,"","min"],[2,1,1,"","priority"],[2,1,1,"","record"],[2,1,1,"","reduce"],[2,1,1,"","script"],[2,1,1,"","sum"],[2,1,1,"","top"]],"coherence.aggregator.AverageAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.CompositeAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.CountAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.DistinctValuesAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.EntryAggregator":[[2,1,1,"","__init__"],[2,1,1,"","and_then"]],"coherence.aggregator.GroupAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.MaxAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.MinAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.PriorityAggregator":[[2,1,1,"","__init__"],[2,2,1,"","execution_timeout_in_millis"],[2,2,1,"","request_timeout_in_millis"],[2,2,1,"","scheduling_priority"]],"coherence.aggregator.QueryRecorder":[[2,3,1,"","EXPLAIN"],[2,3,1,"","TRACE"],[2,1,1,"","__init__"]],"coherence.aggregator.ReducerAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.Schedule":[[2,3,1,"","FIRST"],[2,3,1,"","IMMEDIATE"],[2,3,1,"","STANDARD"]],"coherence.aggregator.SumAggregator":[[2,1,1,"","__init__"]],"coherence.aggregator.Timeout":[[2,3,1,"","DEFAULT"],[2,3,1,"","NONE"]],"coherence.aggregator.TopAggregator":[[2,1,1,"","__init__"],[2,2,1,"","ascending"],[2,2,1,"","descending"],[2,1,1,"","extract"],[2,1,1,"","order_by"]],"coherence.event":[[1,0,1,"","MapEvent"],[1,0,1,"","MapListener"]],"coherence.event.MapEvent":[[1,2,1,"","description"],[1,2,1,"","key"],[1,2,1,"","name"],[1,2,1,"","new"],[1,2,1,"","old"],[1,2,1,"","source"],[1,2,1,"","type"]],"coherence.event.MapListener":[[1,1,1,"","__init__"],[1,1,1,"","on_any"],[1,1,1,"","on_deleted"],[1,1,1,"","on_inserted"],[1,1,1,"","on_updated"]],"coherence.extractor":[[4,0,1,"","AbstractCompositeExtractor"],[4,0,1,"","ChainedExtractor"],[4,0,1,"","CompositeUpdater"],[4,0,1,"","IdentityExtractor"],[4,0,1,"","UniversalExtractor"],[4,0,1,"","UniversalUpdater"],[4,0,1,"","ValueExtractor"],[4,0,1,"","ValueManipulator"],[4,0,1,"","ValueUpdater"]],"coherence.extractor.AbstractCompositeExtractor":[[4,1,1,"","__init__"]],"coherence.extractor.ChainedExtractor":[[4,1,1,"","__init__"]],"coherence.extractor.CompositeUpdater":[[4,1,1,"","__init__"],[4,1,1,"","get_extractor"],[4,1,1,"","get_updator"]],"coherence.extractor.IdentityExtractor":[[4,1,1,"","__init__"]],"coherence.extractor.UniversalExtractor":[[4,1,1,"","__init__"],[4,1,1,"","create"]],"coherence.extractor.UniversalUpdater":[[4,1,1,"","__init__"]],"coherence.extractor.ValueExtractor":[[4,1,1,"","__init__"],[4,1,1,"","and_then"],[4,1,1,"","compose"],[4,1,1,"","extract"]],"coherence.extractor.ValueManipulator":[[4,1,1,"","__init__"],[4,1,1,"","get_extractor"],[4,1,1,"","get_updator"]],"coherence.extractor.ValueUpdater":[[4,1,1,"","__init__"]],"coherence.filter":[[5,0,1,"","AllFilter"],[5,0,1,"","AlwaysFilter"],[5,0,1,"","AndFilter"],[5,0,1,"","AnyFilter"],[5,0,1,"","ArrayFilter"],[5,0,1,"","BetweenFilter"],[5,0,1,"","ComparisonFilter"],[5,0,1,"","ContainsAllFilter"],[5,0,1,"","ContainsAnyFilter"],[5,0,1,"","ContainsFilter"],[5,0,1,"","EqualsFilter"],[5,0,1,"","ExtractorFilter"],[5,0,1,"","Filter"],[5,0,1,"","Filters"],[5,0,1,"","GreaterEqualsFilter"],[5,0,1,"","GreaterFilter"],[5,0,1,"","InFilter"],[5,0,1,"","IsNoneFilter"],[5,0,1,"","IsNotNoneFilter"],[5,0,1,"","LessFilter"],[5,0,1,"","LikeFilter"],[5,0,1,"","MapEventFilter"],[5,0,1,"","NeverFilter"],[5,0,1,"","NotEqualsFilter"],[5,0,1,"","NotFilter"],[5,0,1,"","OrFilter"],[5,0,1,"","PredicateFilter"],[5,0,1,"","PresentFilter"],[5,0,1,"","RegexFilter"],[5,0,1,"","XorFilter"]],"coherence.filter.AllFilter":[[5,1,1,"","__init__"]],"coherence.filter.AlwaysFilter":[[5,1,1,"","__init__"]],"coherence.filter.AndFilter":[[5,1,1,"","__init__"]],"coherence.filter.AnyFilter":[[5,1,1,"","__init__"]],"coherence.filter.ArrayFilter":[[5,1,1,"","__init__"]],"coherence.filter.BetweenFilter":[[5,1,1,"","__init__"]],"coherence.filter.ComparisonFilter":[[5,1,1,"","__init__"]],"coherence.filter.ContainsAllFilter":[[5,1,1,"","__init__"]],"coherence.filter.ContainsAnyFilter":[[5,1,1,"","__init__"]],"coherence.filter.ContainsFilter":[[5,1,1,"","__init__"]],"coherence.filter.EqualsFilter":[[5,1,1,"","__init__"]],"coherence.filter.ExtractorFilter":[[5,1,1,"","__init__"]],"coherence.filter.Filter":[[5,1,1,"","And"],[5,1,1,"","Or"],[5,1,1,"","Xor"]],"coherence.filter.Filters":[[5,1,1,"","all"],[5,1,1,"","always"],[5,1,1,"","any"],[5,1,1,"","array_contains"],[5,1,1,"","array_contains_all"],[5,1,1,"","array_contains_any"],[5,1,1,"","between"],[5,1,1,"","contains"],[5,1,1,"","contains_all"],[5,1,1,"","contains_any"],[5,1,1,"","equals"],[5,1,1,"","event"],[5,1,1,"","greater"],[5,1,1,"","greater_equals"],[5,1,1,"","is_in"],[5,1,1,"","is_none"],[5,1,1,"","is_not_none"],[5,1,1,"","less"],[5,1,1,"","less_equals"],[5,1,1,"","like"],[5,1,1,"","negate"],[5,1,1,"","never"],[5,1,1,"","not_equals"],[5,1,1,"","present"],[5,1,1,"","regex"]],"coherence.filter.GreaterEqualsFilter":[[5,1,1,"","__init__"]],"coherence.filter.GreaterFilter":[[5,1,1,"","__init__"]],"coherence.filter.InFilter":[[5,1,1,"","__init__"]],"coherence.filter.IsNoneFilter":[[5,1,1,"","__init__"]],"coherence.filter.IsNotNoneFilter":[[5,1,1,"","__init__"]],"coherence.filter.LessFilter":[[5,1,1,"","__init__"]],"coherence.filter.LikeFilter":[[5,1,1,"","__init__"]],"coherence.filter.MapEventFilter":[[5,3,1,"","ALL"],[5,3,1,"","DELETED"],[5,3,1,"","INSERTED"],[5,3,1,"","KEY_SET"],[5,3,1,"","UPDATED"],[5,3,1,"","UPDATED_ENTERED"],[5,3,1,"","UPDATED_LEFT"],[5,3,1,"","UPDATED_WITHIN"],[5,1,1,"","__init__"],[5,1,1,"","from_filter"],[5,1,1,"","from_mask"]],"coherence.filter.NeverFilter":[[5,1,1,"","__init__"]],"coherence.filter.NotEqualsFilter":[[5,1,1,"","__init__"]],"coherence.filter.NotFilter":[[5,1,1,"","__init__"]],"coherence.filter.OrFilter":[[5,1,1,"","__init__"]],"coherence.filter.PredicateFilter":[[5,1,1,"","__init__"]],"coherence.filter.PresentFilter":[[5,1,1,"","__init__"]],"coherence.filter.RegexFilter":[[5,1,1,"","__init__"]],"coherence.filter.XorFilter":[[5,1,1,"","__init__"]],"coherence.processor":[[6,0,1,"","CompositeProcessor"],[6,0,1,"","ConditionalProcessor"],[6,0,1,"","ConditionalPut"],[6,0,1,"","ConditionalPutAll"],[6,0,1,"","ConditionalRemove"],[6,0,1,"","EntryProcessor"],[6,0,1,"","ExtractorProcessor"],[6,0,1,"","MethodInvocationProcessor"],[6,0,1,"","NullProcessor"],[6,0,1,"","NumberIncrementor"],[6,0,1,"","NumberMultiplier"],[6,0,1,"","PreloadRequest"],[6,0,1,"","Processors"],[6,0,1,"","PropertyManipulator"],[6,0,1,"","PropertyProcessor"],[6,0,1,"","ScriptProcessor"],[6,0,1,"","TouchProcessor"],[6,0,1,"","UpdaterProcessor"],[6,0,1,"","VersionedPut"],[6,0,1,"","VersionedPutAll"]],"coherence.processor.CompositeProcessor":[[6,1,1,"","__init__"],[6,1,1,"","and_then"],[6,1,1,"","when"]],"coherence.processor.ConditionalProcessor":[[6,1,1,"","__init__"]],"coherence.processor.ConditionalPut":[[6,1,1,"","__init__"]],"coherence.processor.ConditionalPutAll":[[6,1,1,"","__init__"]],"coherence.processor.ConditionalRemove":[[6,1,1,"","__init__"]],"coherence.processor.EntryProcessor":[[6,1,1,"","__init__"],[6,1,1,"","and_then"],[6,1,1,"","when"]],"coherence.processor.ExtractorProcessor":[[6,1,1,"","__init__"]],"coherence.processor.MethodInvocationProcessor":[[6,1,1,"","__init__"]],"coherence.processor.NullProcessor":[[6,1,1,"","__init__"]],"coherence.processor.NumberIncrementor":[[6,1,1,"","__init__"]],"coherence.processor.NumberMultiplier":[[6,1,1,"","__init__"]],"coherence.processor.PreloadRequest":[[6,1,1,"","__init__"]],"coherence.processor.Processors":[[6,1,1,"","conditional_put"],[6,1,1,"","conditional_put_all"],[6,1,1,"","conditional_remove"],[6,1,1,"","extract"],[6,1,1,"","increment"],[6,1,1,"","invoke_accessor"],[6,1,1,"","invoke_mutator"],[6,1,1,"","multiply"],[6,1,1,"","nop"],[6,1,1,"","preload"],[6,1,1,"","script"],[6,1,1,"","touch"],[6,1,1,"","update"],[6,1,1,"","versioned_put"],[6,1,1,"","versioned_put_all"]],"coherence.processor.PropertyManipulator":[[6,1,1,"","__init__"],[6,1,1,"","get_extractor"],[6,1,1,"","get_updator"]],"coherence.processor.PropertyProcessor":[[6,1,1,"","__init__"]],"coherence.processor.ScriptProcessor":[[6,1,1,"","__init__"]],"coherence.processor.TouchProcessor":[[6,1,1,"","__init__"]],"coherence.processor.UpdaterProcessor":[[6,1,1,"","__init__"]],"coherence.processor.VersionedPut":[[6,1,1,"","__init__"]],"coherence.processor.VersionedPutAll":[[6,1,1,"","__init__"]],coherence:[[1,0,1,"","Aggregators"],[1,0,1,"","Filters"],[1,0,1,"","MapEntry"],[1,0,1,"","NamedCache"],[1,0,1,"","NamedMap"],[1,0,1,"","Options"],[1,0,1,"","Processors"],[1,0,1,"","Session"],[1,0,1,"","TlsOptions"]]},objnames:{"0":["py","class","Python class"],"1":["py","method","Python method"],"2":["py","property","Python property"],"3":["py","attribute","Python attribute"]},objtypes:{"0":"py:class","1":"py:method","2":"py:property","3":"py:attribute"},terms:{"0":[0,1,2,5,7,8,9,10,12,13,14],"0001":[],"0002":[],"0003":[],"06":10,"0b1":[],"0ebd49":13,"1":[0,1,2,5,7,8,9,10,12],"10":[8,10],"100":[],"1000":13,"111":[0,8],"112":8,"12":9,"1408":[1,7,10,14],"142":[],"15":12,"16":5,"1669671978888":13,"17":[7,12],"1992":5,"2":[0,2,5,8,9,10],"20":12,"2022":10,"2023":[0,7,8,9,10,12],"21":[7,12],"22":10,"25":[9,12],"28":0,"29":[1,5],"3":[0,10],"30":[1,12,14],"32":5,"34":7,"36":0,"37":8,"38":0,"39":9,"4":[0,5,10,12],"40":[0,12],"41":12,"44":8,"4444":14,"45":9,"46":[9,12],"47":0,"48":[],"49":[],"5":[0,2],"50":[0,7,8,9,12],"51":8,"53":0,"54":9,"55":12,"56":0,"57":8,"58":8,"6":13,"60":[0,9],"62":8,"66":9,"7":5,"71":9,"77":9,"8":5,"9":9,"9075":5,"abstract":[1,2,4],"boolean":[1,13],"case":[1,2,5,6,13,14],"class":[0,1,2,3,4,5,6,8,12,13],"default":[1,2,10,14],"do":[1,2,11],"enum":[2,3],"final":[0,1,7,8,9,12],"float":[1,6],"function":[1,2,6,13],"import":[0,1,2,7,8,9,10,12,13,14],"int":[0,1,2,5,6,7,8,9,10,12,13],"long":13,"new":[1,2,3,4,5,6,7,8,9,10,14],"null":[1,2,4,5,6,13],"public":[10,13],"return":[0,1,2,3,4,5,6,7,8,9,12,13],"short":5,"static":[1,2,5,6],"super":[4,13],"throw":[4,5],"true":[1,5,6,13,14],"try":[0,7,8,9,12],"while":[1,6],A:[0,1,2,3,4,5,6,8,12,14],AND:[1,5],And:[5,12],Being:12,By:2,For:[0,1,2,6,9,10,13],If:[1,2,4,6,10,12,13,14],In:[2,5,6,9,13],It:[1,13,14],No:[1,6],ONE:7,OR:[1,5],Or:5,Such:1,That:13,The:[0,1,2,3,4,5,6,8,9,10,12,13,14],Then:[2,9],There:2,To:[10,11,13,14],With:13,_:5,__eq__:13,__hash__:13,__init__:[1,2,3,4,5,6,13],__str__:13,_base_channel:1,abc:[1,2,4,5,6],abil:[2,8,9,10],abl:[12,14],about:[10,13],abov:[13,14],absenc:1,abstractaggreg:2,access:[8,10,12,13],accessor:13,accomplish:1,accord:5,achiev:13,across:[0,1],act:[1,10],activ:2,actual:[0,1,2,4],ad:[1,3,9,12],add:[1,8,9],add_map_listen:[1,9],addit:[1,2,6,9],addition:2,addmaplisten:1,addr:14,address:[1,14],advanc:2,advantag:5,affect:[1,5],affili:[0,7,8,9,10,12],affin:2,afilt:2,after:[1,2,4,6,10],ag:[0,6,8,12],against:[0,1,2,5,6,7,8,12],agent:[1,2,6],aggreg:10,aio:1,algorithm:1,alia:13,alias:13,all:[0,1,2,5,6,8,9,12,14],allow:[1,2,6,7,10,12],allow_insert:[1,6],alreadi:[1,6,13],also:[1,2,4,5,8,13,14],alwai:[1,2,5,9],amount:[1,6],an:[0,1,2,3,4,5,6,7,8,9,10,12,13,14],analog:2,and_then:[2,4,6],ani:[1,2,3,4,5,6,9,12,13],annot:13,anoth:5,answer:2,anyth:4,aperson:6,api:[2,6,10],append:8,appli:[1,2,4,5,6],applic:[10,13],approach:5,appropri:13,ar:[0,1,2,4,5,6,7,8,9,10,14],arg:[1,2,6],argument:[1,2,6,14],arrai:[1,2,4,5,6],array_contain:[1,5],array_contains_al:[1,5],array_contains_ani:[1,5],arriv:2,ascend:2,ask:10,assembl:1,associ:[1,12,13],assum:[1,2,4,6,14],assumpt:1,async:[0,1,7,8,9,10,12],asyncgener:1,asynchron:[],asyncio:[0,1,7,8,9,10,12,14],asynciter:1,attribut:[2,5,6,12,13],avail:[2,10],averag:[0,1,2],avg:2,avg_under_forti:0,avoid:[1,6,12,14],await:[0,1,7,8,9,10,12],awar:5,back:[1,2,6],base:[0,1,2,3,4,5,6,12],basic:13,bear:0,becaus:[],becom:2,been:[1,3,6,14],befor:[1,4,6,10],begin:13,behavior:13,behind:1,being:[1,13],belong:[2,5],below:11,best:13,between:[1,5,12,13],bilbo:[0,8],bill:12,binari:5,bind:[13,14],blob:1,bool:[1,2,5,6,13],both:[4,5],bound:[1,5],box:[0,8,12,13],bread:13,bring:[],buckland:12,built:12,bullet:14,burglar:0,by_pag:1,c:[0,7,8,9,10,12],ca:[1,14],ca_cert_path:[1,14],cach:[1,2,3,6,9,10,14],cacheord:2,calcul:[0,1,2,6],call:[1,2,3,6,13],callabl:[1,3],callback:[1,3],caller:[1,4,5,6],camel:13,can:[0,1,2,5,8,10,13,14],cannot:[],care:8,cast:13,ce:10,certif:[1,14],chain:[],chainedextractor:[2,5],chang:[1,3,5,9],channel:[1,10,14],channel_argu:1,channel_opt:[1,14],channelopt:1,charact:5,characterist:[1,2],check:[5,6],circuit:5,classmethod:[4,5],classnam:13,classpath:13,claus:2,clear:[0,1,8,9,10,12],cli:10,client:[0,1,2,3,5,6,8,11,12,13,14],client_cert_path:[1,14],client_key_path:[1,14],close:[0,1,7,8,9,10,12],cluster:[1,6,7,8,13],code:[1,2,8],coher:[0,1,7,8,9,11,12,13,14],coherence_client_request_timeout:[1,14],coherence_server_address:[1,14],coherence_tls_:14,coherence_tls_certs_path:[1,14],coherence_tls_client_cert:[1,14],coherence_tls_client_kei:[1,14],collect:[1,2,5,6],com:[0,1,7,8,9,10,12,13,14],combin:[2,5],come:[0,2,10],common:[2,6,13],commun:10,compar:[1,2,5],complet:[1,2,13],compos:[4,5],composit:[1,4,5],compris:[1,2,6],concept:[2,14],concurr:[1,6,8],condit:[5,6],condition:6,conditional_put:[1,6],conditional_put_al:[1,6],conditional_remov:[1,6],conditionalprocessor:[1,5],conditionalput:1,conditionalremov:1,configur:[1,2,10,14],configurablecachefactori:1,connect:[1,7,10,14],consid:4,constant:2,construct:[1,2,3,4,5,6,13,14],constructor:[1,4,6,13,14],consult:10,contain:[1,2,5,10],contains_al:[1,5],contains_ani:[1,5],contains_kei:[1,10],contains_valu:[1,10],content:[1,3,5],contract:5,contriv:13,control:[1,2,6,8,14],convent:6,convert:13,copi:1,copyright:[0,7,8,9,10,12],correctli:10,correspond:[1,2,4,5,6],cost:[1,2,6],could:[1,2,3,4,6],count:[0,1,2],cours:13,cover:[2,13],creat:[1,2,4,6,7,9,10,13,14],created_at:13,createdat:13,creation:13,criteria:[1,5],crud:7,current:[1,5,6,7,14],currenttimemilli:13,d:10,data:[0,1,2,7,8,12,13,14],databas:1,dataclass:[0,8,12],date:13,decim:[0,1,2,6],decor:13,def:[0,7,8,9,10,12,13],default_address:1,default_format:[1,14],default_request_timeout:[1,14],default_scop:[1,14],default_valu:1,defaultvalu:1,defin:[1,3,5,8,9,12,13,14],delet:[1,3,5,9,10],delimit:[2,4,5],deliv:1,demonstr:[0,7,8,9,12,13],depend:6,deriv:0,descend:2,describ:13,descript:[1,3,13],deseri:[12,13,14],desir:[13,14],destroi:[1,3,9,10],detail:[6,7,10],detect:1,determin:14,develop:10,dict:[0,1,2,6,7],did:[1,6],differ:[1,3,9,14],direct:[1,2,6],disabl:[1,14],disclosur:10,disconnect:[1,10],disk:1,displai:8,distinct:[0,1,2],distinct_hobbi:0,distinctvalu:2,do_run:[0,7,8,9,12],doc:5,docker:10,document:[1,7],doe:[1,4,6,14],doesn:12,don:0,done:6,dot:[2,4,5],doubl:2,dsl:[1,2],dump:2,durat:8,dure:[1,5,6],e:[1,2,4,5,6,9],e_:5,each:[0,1,2,6,8,9],easili:1,ed:5,edit:10,effect:[1,6],effici:[6,14],egg:13,either:[1,4,5,6],element:1,els:1,email:10,emit:[1,5],empti:2,enabl:[1,14],encourag:[1,2],end:4,endpoint:[1,14],enforc:6,enough:9,ensur:[2,9,10],entir:[1,2,6],entri:[0,1,2,3,5,6,9,10,12,13],entry_delet:[1,3],entry_insert:[1,3],entry_upd:[1,3],entryaggreg:1,entryprocessor:[1,8,10],enumer:2,env_ca_cert:1,env_client_cert:1,env_client_kei:1,env_request_timeout:1,env_server_address:1,environ:[1,14],equal:[1,2,5,12,13],equat:13,equival:[1,5,10,13],escap:[1,5],escape_char:5,especi:[1,2],estim:[1,2],evalu:[1,2,4,5,6],even:[6,12,13],event:[1,5,10],everi:1,everyth:10,exactli:[4,5],exampl:[0,1,2,4,6,7,8,9,12,13,14],except:[1,4,5,13],exclus:8,execut:[0,1,2,6,8,12],execution_timeout:[1,2],execution_timeout_in_milli:2,executiontimeout:2,exist:[1,2,5,6],expect:1,expiri:[1,6],explain:[1,2],explicit:[1,6],explicitli:[1,2],express:[1,5,6],extern:1,extract:[1,2,4,5,6],extractor:[1,2,5,6],extractor_or_method:[1,5],extractor_or_properti:[1,2],extractorprocessor:1,extractors_or_method:4,factor:[1,6],factori:[1,2],fairli:13,fals:[1,2,5,6,13,14],familiar:10,featur:[0,2,8],feedback:10,few:[],field:[4,13],file:13,filter:[0,2,4,6,9,10,12],filterleft:5,filterright:5,find:12,fine:[6,13],fire:5,first:[2,4],fit:12,flag:[1,5,6],flexibl:6,foe:14,follow:[0,1,2,7,8,9,10,12,13,14],form:[2,13],format:[1,13,14],fragment:5,framework:10,fred:[],frodo:[0,8],frogmorton:12,from:[0,1,2,3,4,5,6,7,8,9,10,12,13,14],from_field_or_method:4,from_filt:5,from_mask:5,from_rang:[1,5],front:2,full:13,further:[1,2],futur:8,g:[1,2],garden:[],gener:[1,2,3,4,5,6,9,14],genson:13,get:[1,4,6,7,8,10,13],get_al:[1,8,10],get_cach:[1,10],get_extractor:[4,6],get_map:[0,7,8,9,12],get_or_default:[1,10],get_upd:[4,6],getal:2,getclass:13,getcomplet:13,getcreatedat:13,getcreatedatd:13,getdescript:13,getid:13,getter:6,ghcr:10,github:[1,10],give:10,given:[1,2,3,5,6,9,12],glossari:1,go:13,golf:[],googl:10,got:10,graal:6,great:12,greater:[0,1,5,9],greater_equ:[1,5],greaterequalfilt:5,grid:[0,8],group:[1,2],group_bi:[0,1,2],groupaggreg:1,grpc:[1,10,14],grpc_type:1,grpcproxi:10,guid:10,h:1,ha:[1,2,3,6,8,14],handi:0,handl:5,hash:13,hashcod:13,have:[1,2,4,5,6,10,13,14],he:[],hear:10,hello:10,here:[10,13],hobbi:0,hobbit2:8,hobbit:[0,8,12],hobbiton:12,hold:1,home:12,host:1,how:[2,8,10,13],howev:[2,13],html:1,http:[0,1,7,8,9,10,12],i:[9,12],id:[0,8,12,13],idempot:1,ident:4,identifi:[1,6,7],identityextractor:[1,2,6],idl:2,iec:5,ignore_cas:[1,5],imag:10,immedi:2,impact:8,impl:1,implement:[1,2,4,5,6,13],impli:[1,2,6],impos:1,improv:10,includ:[1,2,5,10,12,13],include_lower_bound:[1,5],include_upper_bound:[1,5],inclus:[1,5],increment:[1,6,8],incur:[1,6],indefinit:2,independ:2,index:[5,10,12],indic:[1,2,3,5,6],individu:[1,2,6],inequ:5,inf:13,inform:2,input:4,insensit:5,insert:[1,3,5,6,8,9,10,12,13],instanc:[1,2,4,6,13,14],instant:13,instead:[1,2,6,13],intend:5,intenum:2,interceptor:[1,6],interest:[0,5],interfac:[1,2,3,6,10],interoper:13,intersect:2,invalid:1,invers:2,invert:6,invit:10,invoc:[1,5,6,9,14],invocablemap:6,invok:[1,2,3,5,6,8],invoke_accessor:[1,6],invoke_al:[1,8],invoke_mut:[1,6],invokeal:6,io:[1,10,13],ipv4:1,is_empti:[1,10],is_in:[1,5,12],is_non:[1,5],is_not_non:[1,5],isinst:13,isn:13,iso:5,issu:10,item:[0,5],iter:1,its:[0,1,4,6,7,8,9,10,12,13],itself:4,jakarta:13,jane:[],java:[1,2,5,6,10,13],javabean:[4,6],javascript:[1,6,13],join:10,jone:[],js:[1,6],json:[1,2,10,13,14],jsonbindingexcept:13,jsonbproperti:13,jsonbtransi:13,judici:2,just:[4,13],k1:10,k:[1,2,3,5,6,10],kei:[0,1,2,3,4,6,7,8,9,10,12,14],key1:[],key2:[],key3:[],key_set:5,keyset:5,kick:0,knowledg:2,known:13,lambda:9,languag:[1,2,6,10,13],larger:9,later:10,least:1,leav:5,left:[4,5],length:[2,4,9],less:[0,1,5],less_equ:[1,5],let:[2,13],librari:1,licens:[0,7,8,9,12],lieu:[1,2],lifecycl:[3,9,10],like:[1,5,7,10],limit:[0,9,10],line:[0,7,8,9,12],link:[1,2,4,5,13],list:[0,1,2,4,5,8,12,13],listen:[1,3,5,9,10],listener1:9,listener_for:1,lite:1,live:12,load:1,loader:[1,6],local:[1,3,10],localdatetim:13,localhost:[1,7,14],lock:[1,6],log:10,logic:[1,5],longer:[2,5],loop:9,love:10,lower:[1,2,5],m:[10,11],made:[1,9],magnitud:[1,6],mai:[1,2,3,5,6,13,14],maintain:[],make:[1,2,5],manag:[1,14],manipul:[6,10],map:[1,2,3,4,5,6,7,9,10,13,14],map_destroi:3,map_releas:3,map_trunc:3,mapentri:6,mapev:5,mapeventfilt:9,mapeventrespons:[1,3],mapeventtyp:1,maplifecycleev:[1,9],maplisten:[5,9],mark:13,marshal:14,mask:[1,5],master:1,match:[1,5,6,14],max:[0,1,2],maximum:[1,2],md:[],mdinclud:[],mean:[1,6,14],member:13,memori:1,meriadoc:0,messages_pb2:[1,3],meta:13,metadata:13,method:[1,2,4,5,6,13],method_nam:[1,6],method_or_extractor:4,methodinvocationprocessor:1,methodinvoctionprocessor:6,milk:13,milli:1,millisecond:2,min:[1,2],minimum:[1,2],model:[12,13],modif:8,modifi:[1,4,6],modul:10,more:[1,2,5,6,7,8,12],most:[1,2],move:8,much:8,multi:6,multiextractor:2,multipl:[2,6,13],multipli:[1,6],must:[1,2,4,5,6,10,13,14],mutat:[1,6,10],my:7,n:[1,2,5,6,9],nad:9,name:[0,1,2,3,4,5,6,8,12,13],name_or_manipul:[1,6],namedcach:[7,10,14],namedmap:[0,2,3,5,6,7,8,9,12],natur:[1,2],necessari:10,need:[0,1,2,6,8,11,12,13],negat:[1,5],network:[1,6,10],never:[1,5],new_valu:1,next:[2,4,6],nnamedmap:9,node:9,non:[2,10],none:[0,1,2,3,4,5,6,7,8,9,10,12,13,14],nop:[1,6],not_equ:[1,5],note:[2,13,14],notfilt:6,noth:[1,6],notic:13,notif:[1,5,9],notifi:10,now:[5,14],num_hobbit:12,number:[0,1,2,5,6],numberincrementor:1,numbermultipli:1,numer:[1,2,6],o:13,object:[0,1,2,4,5,6,10,13,14],obtain:[2,7],obvious:6,occur:[1,2,3,9],ofepochmilli:13,ofinst:13,often:1,old:[1,3,5,6],old_valu:1,older:0,oldest:0,on_ani:[1,3,9],on_delet:[1,3],on_insert:[1,3],on_upd:[1,3],onc:[1,9,14],one:[1,2,3,4,6,7,8,9,10,11,12],ones:[6,12],onli:[1,2,4,5,6,8,9,10,13,14],op:5,open:10,oper:[0,1,2,5,6,7,8,10,12],opt:14,optim:[1,12],option:[2,3,4,6,14],oracl:[0,7,8,9,10,12,13],order:[1,2,6,13],order_bi:2,origin:[1,3],oss:[0,7,8,9,10,12],other:[2,5,10,13,14],otherwis:[1,6,13],our:10,out:[0,1,2,8,12,13],over:[0,1,6,8],over_forti:0,overrid:[2,13],overriden:13,own:[1,12],p:10,packag:[11,13],page:[1,10],paint:[],pair:[1,4],parallel:1,param:[1,4,6,13],paramet:[1,2,3,4,5,6],part:[1,2,4],partial:2,particular:[2,5,9,13],partit:2,pass:[1,2,4,5,6,9,13,14],path:[1,14],pattern:[1,2,5,6],payload:13,per:14,peregrin:0,perform:[1,2,6],permiss:[0,7,8,9,10,12],persist:1,person_data:0,pertain:9,photographi:[],pip:[10,11],place:1,pleas:10,pof:13,point:3,port:[1,10],portableobject:13,portion:2,possibl:[1,3,6,9,13,14],post_incr:[1,6],post_multipl:[1,6],predefin:5,predic:[2,5],prefix:[4,6],preload:[1,6],preloadrequest:1,presenc:1,present:[1,2,5,6,12,13],presentfilt:6,prevent:1,previou:[1,4],previous:[1,5,13],primit:[],print:[0,1,2,7,8,9,10,12],prioriti:[1,2],priorityagg:2,priorityaggreg:1,privat:13,process:[1,2,6,10],processor:[5,8],produc:[1,2],programmat:14,progress:[1,9],project:10,properti:[1,2,3,4,6,13],property_nam:[2,6],provid:[1,2,4,6,8,9,13,14],proxi:[10,13,14],pull:10,purpos:[1,2],push:[],put:[1,6,7,8,9,10,12],put_al:[0,1,10],put_if_abs:[1,10],putallifabs:6,py:10,python3:[10,11],python:[1,11,13,14],qualifi:13,queri:[0,1,2,5,10],query_filt:12,query_typ:[1,2],queryrecord:1,question:10,queu:2,r:[1,2,4,6,10],race:[],rais:[1,3,9,10],random:12,randomuuid:13,rang:[5,9,12],rather:6,re:[1,6,13],read:[1,13],readabl:[1,2],readm:[],receiv:[1,3],recommend:10,reconnect:[1,10],record:[1,2],recordtyp:[1,2],reduc:[1,2,6],refer:[4,6],reflect:[1,2,4,5,6],reflectionextractor:5,regex:[1,5],regist:1,registr:[9,10],regular:5,relai:[4,5],relat:14,releas:[1,3,9,10],remain:3,remot:[1,7],remov:[1,3,6,7,8,9,10],remove_map:1,remove_map_listen:[1,9],renam:13,replac:[1,6,10],replace_map:[1,10],replaceal:6,report:[1,6],repres:[0,1,2,4,5,6,8,12,13],request:[1,2,10,14],request_timeout:[1,2],request_timeout_in_milli:2,request_timeout_second:[1,14],requesttimeout:2,requir:[1,2],resolv:1,resourc:[1,3,14],respons:[1,3,10,14],restrict:[1,5],result:[0,1,2,3,4,5,6,8,9,13],retriev:[1,4,6,12],return_curr:[1,6],return_valu:[1,6],returnvalu:13,review:10,rich:[],right:[4,5],run:[0,2,7,8,9,10,12],run_test:10,s:[1,2,3,4,5,6,9,10,13,14],safeti:[1,2],sai:10,sam:0,same:[2,6,13,14],satisfi:[1,6],save:13,scan:2,scene:1,schedul:1,scheduling_prior:[1,2],scope:1,script:[1,2,6],script_nam:[1,2],scriptprocessor:1,search:10,second:[1,2,8,14],section:9,see:[0,1,6,7,8,10,12,14],sei:[],select:1,self:13,semant:5,send:[1,6,8],sent:[1,5],separ:2,sequenc:[1,2,4,5],sequenti:[4,6],ser_format:1,serial:[1,2,3,10,14],serializ:13,serv:4,server:[1,2,10,13,14],servic:2,session:[0,7,8,9,10,12],session_opt:1,sessionlifecycleev:1,set:[0,1,2,4,5,6,8,13,14],setcomplet:13,setdescript:13,setter:6,should:[1,2,3,4,5,6,9,13],shouldn:13,show:14,shown:[0,7,8,9,10,11,12],side:[0,10,13,14],sign:[1,6],signifi:1,signific:1,significantli:[1,6,8],similar:2,similarli:[9,13],simpi:[1,6],simpl:[0,1,2,6,7,8,12,13],simplest:14,sinc:1,singl:[2,5],site:10,size:[1,2,7,8,10,12],slack:10,sleep:9,smith:[],snake:13,sname:6,so:[1,2,4,14],sole:5,some:[1,2,9],somefilt:2,someinternalvalu:13,sometim:[0,12],somewhat:[2,13],soon:2,sort:[2,4],sourc:[1,3,10],span:2,speak:2,special:2,specif:[1,6,9,14],specifi:[1,2,4,5,6],split:2,sql:[2,5],src:[],standard:[1,2,5,6,13],state:[1,4,6],statu:13,step:[1,2],still:13,stock:12,storag:3,store:[0,1,2,7,8,10,12,13],str:[0,1,2,3,4,5,6,7,8,9,10,12,13,14],string:[1,2,5,6,10,13],strongli:[1,2],structur:[1,7],submit:10,subscrib:9,subsequ:14,subset:[0,1,2,5,9],substr:13,suggest:10,sum:[1,2],sumaggr:2,suppli:[1,6],support:[0,1,6,8,9,10,12,14],system:[1,13],systemdefault:13,t:[0,1,2,4,5,6,12,13],take:[5,6,8,13],target:[1,4,6],task:[2,13],tbc:[],ten:8,tend:[1,2],term:1,test:[0,1,5,10],than:[0,6,9,12,14],the_map:6,thei:[0,1,2,9],them:[0,2],thi:[0,1,2,3,4,5,6,8,9,10,12,13,14],those:[2,13],though:13,thread:[1,2],three:14,through:1,thrown:[5,13],thu:[1,13],time:[1,2,6,9,13],timeout:[1,14],tl:[1,14],tls_option:[1,14],to_rang:[1,5],todo:[5,13],top:[1,2],topaggreg:1,tostr:13,touch:[1,6,10],trace:2,traffic:[1,6],transpar:1,transport:10,treat:2,trigger:[1,6,9],trivial:4,truncat:[1,3,9,10],ttl:1,tune:6,tupl:[1,2],twenti:12,two:[1,2,10],type:[0,1,2,3,4,5,6,8,12,13],typevar:1,typic:[1,14],undefin:1,under:[0,7,8,9,10,12],underli:[1,2,4,6],underscor:5,understood:13,union:[1,2,4,5,6],uniqu:2,univers:[0,4,7,8,9,10,12],universalextractor:[2,5],unless:[1,4],unlik:1,unnecessari:[5,12],untouch:3,up:2,updat:[1,3,4,5,6,7,8,9,10],updated_ent:5,updated_left:5,updated_within:5,updater_or_property_nam:[1,6],updaterprocessor:1,upl:[0,7,8,9,10,12],upper:[1,5],us:[0,1,2,4,5,6,7,8,9,10,12,13,14],usabl:2,usag:[6,13],use_i:6,user:7,usual:3,util:[0,8,12,13],uuid4:13,uuid:13,v1:10,v:[0,1,3,4,5,6,7,8,9,10,12],valid:1,valu:[1,2,3,4,5,6,7,8,9,10,12,13,14],value1:[],value2:[],value_extractor:6,valueerror:1,valueextractor:[1,2,5,6],valuemanipul:[1,6],valueupdat:[1,6],variabl:[1,5,14],variou:[0,1,2,5,7,8,12],versa:1,version:[1,6,13],versioned_put:[1,6],versioned_put_al:[1,6],versionedput:1,via:[1,2,5,6,14],vice:1,view:1,visit:10,vm:6,vulner:10,wa:[1,5,6,13],wai:[2,5],wait:2,warn:1,we:[2,5,10],welcom:10,well:10,were:13,what:[10,13],when:[1,3,5,6,9,13,14],where:[0,8,10],whether:[1,4,5,6],which:[1,2,3,4,5,6,14],who:12,whole:0,whose:[1,5,6],wide:8,wildcard:5,willing:2,wire:8,within:[0,1,2,3,5,6,7,13],without:[1,2,6],won:13,word:2,work:[2,9],worker:2,workspac:10,would:[2,5,10,11,14],wrap:[1,2,6],written:[1,2,6],x:[5,9],xor:5,y:5,year:8,yield:5,you:[0,10,12,13,14],your:12,z:5,zero:[4,5],zoneid:13},titles:["Aggregation","API Reference","coherence.aggregator","coherence.event","coherence.extractor","coherence.filter","coherence.processor","The Basics","Entry Processing","Events","Coherence Python Client","Installation","Querying","Serialization","Sessions"],titleterms:{The:7,abstractcomparableaggreg:2,abstractcompositeextractor:4,abstractdoubleaggreg:2,aggreg:[0,1,2],allfilt:5,alwaysfilt:5,andfilt:5,anyfilt:5,api:1,arrayfilt:5,averageaggreg:2,basic:7,betweenfilt:5,chainedextractor:4,client:10,cluster:10,coher:[2,3,4,5,6,10],comparisonfilt:5,compositeaggreg:2,compositeprocessor:6,compositeupdat:4,conditionalprocessor:6,conditionalput:6,conditionalputal:6,conditionalremov:6,containsallfilt:5,containsanyfilt:5,containsfilt:5,contribut:10,countaggreg:2,distinctvaluesaggreg:2,document:10,entri:8,entryaggreg:2,entryprocessor:6,equalsfilt:5,event:[3,9],exampl:10,extractor:4,extractorfilt:5,extractorprocessor:6,featur:10,filter:[1,5],greaterequalsfilt:5,greaterfilt:5,groupaggreg:2,help:10,identityextractor:4,indic:10,infilt:5,instal:[10,11],isnonefilt:5,isnotnonefilt:5,lessfilt:5,licens:10,likefilt:5,mapentri:1,mapev:[1,3],mapeventfilt:5,mapeventtyp:3,maplifecycleev:3,maplisten:[1,3],maxaggreg:2,methodinvocationprocessor:6,minaggreg:2,modul:1,namedcach:1,namedmap:1,neverfilt:5,notequalsfilt:5,notfilt:5,nullprocessor:6,numberincrementor:6,numbermultipli:6,option:1,orfilt:5,predicatefilt:5,preloadrequest:6,presentfilt:5,priorityaggreg:2,process:8,processor:[1,6],propertymanipul:6,propertyprocessor:6,python:10,queri:12,queryrecord:2,reduceraggreg:2,refer:1,regexfilt:5,requir:10,schedul:2,scriptprocessor:6,secur:10,serial:13,session:[1,14],src:[],start:10,sumaggreg:2,tabl:10,timeout:2,tlsoption:1,topaggreg:2,touchprocessor:6,universalextractor:4,universalupdat:4,updaterprocessor:6,valueextractor:4,valuemanipul:4,valueupdat:4,versionedput:6,versionedputal:6,xorfilt:5}})