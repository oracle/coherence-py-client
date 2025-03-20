..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Serialization
=============

The Coherence Python Client uses JSON as the serialization format.  Out of the box, it's possible
to store any Python object in Coherence, however, these objects will only be understood by other Python clients.
This is fine if you're only using Python to access the cluster, but if the cluster will be accessed by other language
clients, such as Javascript or Go, it's best to use Java classes, known to Coherence server, representing the data model. The
following describes how to achieve interoperability with Java.

To begin, let's describe a simple Java class describing a Task for a TODO list application:

.. code-block:: java

  package common.data;

  import java.io.Serializable;
  import java.time.Instant;
  import java.time.LocalDateTime;
  import java.time.ZoneId;
  import java.util.Objects;
  import java.util.UUID;

  public class Task
       implements Serializable
    {
    // ---- data members ----------------------------------------------------

    /**
     * The creation time.
     */
    private long createdAt;

    /**
     * The completion status.
     */
    private Boolean completed;

    /**
     * The task ID.
     */
    private String id;

    /**
     * The task description.
     */
    private String description;

    // ---- constructors ----------------------------------------------------

    /**
     * Deserialization constructor.
     */
    public Task()
        {
        }

    /**
     * Construct {@link Task} instance.
     *
     * @param description  task description
     */
    public Task(String description)
        {
        this.id          = UUID.randomUUID().toString().substring(0, 6);
        this.createdAt   = System.currentTimeMillis();
        this.description = description;
        this.completed   = false;
        }

    // ---- accessors -------------------------------------------------------

    /**
     * Get the creation time.
     *
     * @return the creation time
     */
    public long getCreatedAt()
        {
        return createdAt;
        }

    /**
     * Get the task ID.
     *
     * @return the task ID
     */
    public String getId()
        {
        return id;
        }

    /**
     * Get the task description.
     *
     * @return the task description
     */
    public String getDescription()
        {
        return description;
        }

    /**
     * Set the task description.
     *
     * @param description  the task description
     *
     * @return this task
     */
    public Task setDescription(String description)
        {
        this.description = description;
        return this;
        }

    /**
     * Get the completion status.
     *
     * @return true if it is completed, false otherwise.
     */
    public Boolean getCompleted()
        {
        return completed;
        }

    /**
     * Sets the completion status.
     *
     * @param completed  the completion status
     *
     * @return this task
     */
    public Task setCompleted(Boolean completed)
        {
        this.completed = completed;
        return this;
        }

    /**
     * Returns the created date as a {@link LocalDateTime}.
     *
     * @return the created date as a {@link LocalDateTime}.
     */
    public LocalDateTime getCreatedAtDate()
        {
        return LocalDateTime.ofInstant(Instant.ofEpochMilli(createdAt), ZoneId.systemDefault());
        }

    // ---- Object methods --------------------------------------------------

    @Override
    public boolean equals(Object o)
        {
        if (this == o)
            {
            return true;
            }
        if (o == null || getClass() != o.getClass())
            {
            return false;
            }
        Task task = (Task) o;
        return Objects.equals(createdAt, task.createdAt) &&
               Objects.equals(completed, task.completed) &&
               Objects.equals(id, task.id) &&
               Objects.equals(description, task.description);
        }

    @Override
    public int hashCode()
        {
        return Objects.hash(createdAt, completed, id, description);
        }

    @Override
    public String toString()
        {
        return "Task{"
               + "id=" + id
               + ", description=" + description
               + ", completed=" + completed
               + ", createdAt=" + getCreatedAtDate()
               + '}';
        }
    }

.. note::
  Even though the Task type will be serialized as JSON to the client, the Task value stored in Coherence will still use
  Java or POF serialization for the value, thus the type will need to be marked as Serializable for Java serialization
  or PortableObject for POF serialization.

In order for the Task type to be JSON serializable, it needs to have an alias in a Java properties file on the
classpath called `META-INF/type-aliases.properties`.  This file defines a mapping between an alias and it's associated
type.  If the type being JSON serialized isn't present, a `com.oracle.coherence.io.json.genson.JsonBindingException` will
be thrown by Coherence.  The format for an entry (there may be multiple entries) in this file is simple:
`<alias>=<full-qualified-classname>`.  For the Task class described above, the entry will be: `Task=common.data.Task`,

With the alias defined within the `META-INF/type-aliases.properties` and on Coherence's classpath, it will be possible
to JSON serialize the Task.  The following is an example of the serialized result:

.. code-block:: json

  {
  "@class":"Task",
  "completed":false,
  "createdAt":1669671978888,
  "description":"Milk, bread, and eggs",
  "id":"0ebd49"
  }

Notice the properties defined in the Task class were serialized using the field names.  This behavior can be
overriden by annotating the appropriate field with the `jakarta.json.bind.annotation.JsonbProperty` annotation
passing the desired name:

.. code-block:: java

  @JsonbProperty("return")  // serializes as return instead of returnValue
  private boolean returnValue;

If a particular field shouldn't be serialized, annotate it with the `jakarta.json.bind.annotation.JsonbTransient`
annotation:

.. code-block:: java

  @JsonbTransient // field won't be included in the serialized result
  private long someInternalValue;


What about the `@class` attribute?  This is metadata that is inserted by the `coherence-json` serializer and is read
by the Serializer in order to deserialize the JSON payload into a Java object (in this case, the Task type).  The value
is the alias previously defined in the `META-INF/type-aliases.properties`.


That covers the basics for the Java side of the equation - let's cover Python.
In order for the Python version of the Task to be saved by the Python client to be deserialized as a Java Task it
must be decorated with `@coherence.serialization.proxy("<type alias>")` decorator providing the type alias already defined
in the `/META-INF/type-aliases.properties` (described above).  Here's the Python equivalent of the

.. code-block:: python

  from typing import cast
  from uuid import uuid4
  from time import time

  from coherence import serialization


  @serialization.proxy('Task')
  @serialization.mappings({"created_at": "createdAt"})
  class Task:

    def __init__(self, description: str) -> None:
        super().__init__()
        self.id: str = str(uuid4())[0:6]
        self.description: str = description
        self.completed: bool = False
        self.created_at: int = int(time() * 1000)

    def __hash__(self) -> int:
        return hash((self.id, self.description, self.completed, self.created_at))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Task):
            t: Task = cast(Task, o)
            return self.id == t.id and self.description == t.description and \
                self.completed == t.completed and self.created_at == t.created_at
        return False

    def __str__(self) -> str:
        return "Task(id=\"{}\", description=\"{}\", completed={}, created_at={})".format(self.id,
                                                                                         self.description,
                                                                                         self.completed,
                                                                                         self.created_at)


Take note that the properties of this class have the same names as those used in the Java Task version.
Except, however, for `created_at`.  This attribute uses snake case (Python's standard) and Java's version, `createdAt`
uses camel case.  It is of course possible to just rename the Python version to `createdAt`, but it's also possible
to use the `@coherence.serialization.mappings` decorator to provide a mapping of the Python attribute and its serialized
form.  In this case, the attribute `created_at` will be serialized as `createdAt`.  Similarly, when deserializing,
`createdAt` will be converted to `created_at`.  This is a somewhat contrived use-case, but it fairly demonstrates the
functionality should it be needed.

Also note the `@coherence.serialization.proxy` usage - the value passed is the type alias name that was
previously defined in the `META-INF/type-aliases.properties`.
