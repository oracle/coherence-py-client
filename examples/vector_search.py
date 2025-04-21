# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import gzip
import json
from typing import Final, List

from sentence_transformers import SentenceTransformer

from coherence import NamedMap, Session
from coherence.ai import FloatVector, QueryResult, SimilaritySearch, Vectors
from coherence.extractor import Extractors, ValueExtractor
from coherence.filter import Filter, Filters

"""
This example shows how to use some of the Coherence AI features to store
vectors and perform a k-nearest neighbors (k-nn) search on those vectors to
find matches for search text.

Coherence includes an implementation of the HNSW index which can be used to
index vectors to improve search times.

Coherence is only a vector store so in order to actually create vectors from
text snippets this example uses the `sentence-transformers` package to
integrate with a model and produce vector embeddings from text.

This example has shows how easy it is to add vector search capabilities to
cache data in Coherence and how to easily add HNSW indexes to those searches.
It has not been optimised at all for speed of loading vector data or searches.

Coherence Vectors
=================

Coherence Python client can handle few different types of vector,
this example will use the FloatVector type

Just like any other data type in Coherence, vectors are stored in normal
Coherence caches. The vector may be stored as the actual cache value,
or it may be in a field of another type that is the cache value. Vector data
is then loaded into Coherence the same way that any other data is loaded
using the NamedMap API.

Movie Database
==============

This example is going to build a small database of movies. The database is
small because the data used is stored in the source repository along with the
code. The same techniques could be used to load any of the freely available
much larger JSON datasets with the required field names.

The Data Model
==============

This example is not going to use an specialized classes to store the data in
the cache. The dataset is a json file and the example will use Coherence json
support to read and store the data.

The schema of the JSON movie data looks like this

+--------------------+-------------------------------------------------------+
| Field Name	     |    Description                                        |
+====================+=======================================================+
| title              + The title of the movie                                |
+--------------------+-------------------------------------------------------+
| plot               | A short summary of the plot of the movie              |
+--------------------+-------------------------------------------------------+
| fullplot           | A longer summary of the plot of the movie             |
+--------------------+-------------------------------------------------------+
| cast               + A list of the names of the actors in the movie        |
+--------------------+-------------------------------------------------------+
| genres             | A list of string values representing the different    |
|                    | genres the movie belongs to                           |
+--------------------+-------------------------------------------------------+
| runtime            | How long the move runs for in minutes                 |
+--------------------+-------------------------------------------------------+
| poster             | A link to the poster for the movie                    |
+--------------------+-------------------------------------------------------+
| languages          | A list of string values representing the different    |
|                    | languages for the movie                               |
+--------------------+-------------------------------------------------------+
| directors          | A list of the names of the directors of the movie     |
+--------------------+-------------------------------------------------------+
| writers            | A list of the names of the writers of the movie       |
+--------------------+-------------------------------------------------------+

This example uses the fullplot to create the vector embeddings for each
movie. Other fields can be used by normal Coherence filters to further narrow
down vector searches.

Searching Vectors
=================

A common way to search data in Coherence caches is to use Coherence
aggregators. The aggregator feature has been used to implement k-nearest
neighbour (k-nn) vector searching using a new built-in aggregator named
SimilaritySearch. When invoking a SimilaritySearch aggregator on a cache
the results are returned as a list of QueryResult instances.

The SimilaritySearch aggregator is used to perform a Knn vector search on a
cache in the same way that normal Coherence aggregators are used.

"""


class MovieRepository:
    """This class represents the repository of movies. It contains all the
    code to load and search movie data."""

    MODEL_NAME: Final[str] = "all-MiniLM-L6-v2"
    """
    This is a sentence-transformers model used for generating text embeddings.
    See https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
    """

    EMBEDDING_DIMENSIONS: Final[int] = 384
    """Embedding dimension for all-MiniLM-L6-v2"""

    VECTOR_FIELD: Final[str] = "embeddings"
    """The name of the field in the json containing the embeddings."""

    VALUE_EXTRACTOR: Final[ValueExtractor] = Extractors.extract(VECTOR_FIELD)
    """The ValueExtractor to extract the embeddings vector from the json."""

    def __init__(self, movies: NamedMap) -> None:
        """
        Creates an instance of the MovieRepository

        :param movies: The Coherence NamedMap is the cache used to store the
        movie data.

        """
        self.movies = movies
        # embedding model to generate embeddings
        self.model = SentenceTransformer(self.MODEL_NAME)

    async def load(self, filename: str) -> None:
        """
        Loads the movie data into the NamedMao using the specified zip file

        :param filename: Name of the movies json zip file
        :return: None
        """
        try:
            with gzip.open(filename, "rt", encoding="utf-8") as f:
                # the JSON data should be a JSON list of movie objects (dictionary)
                # in the format described above.
                data = json.load(f)
        except FileNotFoundError:
            print("Error: The file was not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            try:
                f.close()
            except NameError:
                pass  # File was never opened, so nothing to close
            except Exception as e:
                print(f"An error occurred while closing the file: {e}")

        # iterate over list of movie objects (dictionary) to load them into
        # Coherence cache
        for movie in data:
            # get the title of the movie
            title: str = movie.get("title")
            # get the full plot of the movie
            full_plot: str = movie.get("fullplot")
            key: str = title
            # text of the full_plot converted to a vector
            vector: FloatVector = self.vectorize(full_plot)
            # vector is added to the movie object
            movie[self.VECTOR_FIELD] = vector
            # The movie object is added to the cache using the "title" field as the cache key
            await self.movies.put(key, movie)

    def vectorize(self, input_string: str) -> FloatVector:
        """vectorize method takes a String value and returns a FloatVector"""

        # model used to creat embeddings for the input_string
        # in this example model used is onnx-models/all-MiniLM-L6-v2-onnx
        embeddings: List[float] = self.model.encode(input_string).tolist()

        # The vector returned is normalized, which makes future operations on
        # the vector more efficient
        return FloatVector(Vectors.normalize(embeddings))

    async def search(self, search_text: str, count: int, filter: Filter = Filters.always()) -> List[QueryResult]:
        """
        Searches the movies cache by converting the search_text into a vector
        and then using SimilaritySearch for nearest matches to the embeddings
        vector in the cached object. The count parameter is a count of the
        number of nearest neighbours to search for. An optional filter
        parameter can be The filter is used to reduce the cache entries used
        to perform the k-nn search.

        :param search_text:  the text to nearest match on the movie full plot
        :param count: the count of the nearest matches to return :param
        filter: an optional  Filter to use to further reduce the movies to be
        queried
        :return: a List of QueryResult objects
        """

        # create a FloatVector of the search_text
        vector: FloatVector = self.vectorize(search_text)
        # create the SimilaritySearch aggregator using the above vector and count
        search: SimilaritySearch = SimilaritySearch(self.VALUE_EXTRACTOR, vector, count)
        # perform the k-nn search using the above aggregator and optional filter and
        # returns a list of QueryResults
        return await self.movies.aggregate(search, filter=filter)


# Name of the compressed gzip json file that has data for the movies
MOVIE_JSON_FILENAME: Final[str] = "movies.json.gzip"


async def do_run() -> None:

    # Create a new session to the Coherence server using the default host and
    # port i.e. localhost:1408
    session: Session = await Session.create()
    # Create a NamedMao called movies with key of str and value of dict
    movie_db: NamedMap[str, dict] = await session.get_map("movies")
    try:
        # an instance of class MovieRepository is create passing the above
        # NamedMap as a parameter
        movies_repo = MovieRepository(movie_db)

        # All of the movies data from filename  MOVIE_JSON_FILENAME is
        # processed and loaded into the movies_repo
        await movies_repo.load(MOVIE_JSON_FILENAME)

        # Search method is called on the movies_repo instance of class
        # MovieRepository that takes a search_text parameter which is the
        # text to use to convert to a vector and search the movie plot for
        # the nearest matches. The second parameter is a count of the number
        # of nearest neighbours to search for.
        #
        # Below a search for five movies roughly based on "star travel and space ships"
        # is being done
        results = await movies_repo.search("star travel and space ships", 5)
        print("Search results:")
        print("================")
        for e in results:
            print(f"key = {e.key}, distance = {e.distance}, plot = {e.value.get('plot')}")

        # Search method on the movies_repo instance can also include a filter
        # to reduce the cache entries used to perform the nearest neighbours
        # (k-nn) search.
        #
        # Below any movie with a plot similar to "star travel and space
        # ships" was searched for. In addition a Filter is used to narrow down
        # the search i.e. movies that starred "Harrison Ford". The filter
        # will be applied to the cast field of the JsonObject.
        cast_extractor = Extractors.extract("cast")
        filter = Filters.contains(cast_extractor, "Harrison Ford")
        results = await movies_repo.search("star travel and space ships", 2, filter)
        print("\nResults with a filter of movies with cast as Harrison Ford")
        print("===========================================================")
        for e in results:
            print(f"key = {e.key}, distance = {e.distance}, plot = {e.value.get('plot')}")

    finally:
        await session.close()


asyncio.run(do_run())
