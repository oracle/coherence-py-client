# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import gzip
import json
from typing import Final, List

from light_embed import TextEmbedding

from coherence import NamedMap, Session
from coherence.ai import FloatVector, QueryResult, SimilaritySearch, Vectors
from coherence.extractor import Extractors, ValueExtractor
from coherence.filter import Filter, Filters

"""This example shows how to use some of the Coherence AI features to store
vectors and perform a k-nearest neighbors (k-nn) search on those vectors to
find matches for search text.

Coherence includes an implementation of the HNSW index which can be used to
index vectors to improve search times.

Coherence is only a vector store so in order to actually create vectors from
text snippets this example uses the `light-embed` package to integrate with a
model and produce vector embeddings from text.

This example shows just some basic usages of vectors in Coherence including
using Coherence HNSW indexes. It has not been optimised at all for speed of
loading vector data or searches.

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

"""


class MovieRepository:
    """This class represents the repository of movies. It contains all the
    code to load and search movie data."""

    MODEL_NAME: Final[str] = "onnx-models/all-MiniLM-L6-v2-onnx"
    """
    The ONNX-ported version of the sentence-transformers/all-MiniLM-L6-v2
    for generating text embeddings.
    See https://huggingface.co/onnx-models/all-MiniLM-L6-v2-onnx
    """

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
        self.model = TextEmbedding(self.MODEL_NAME)  # embedding model to generate embeddings

    async def load(self, filename: str) -> None:
        """
        Loads the movie data into the NamedMao using the specified zip file

        :param filename: Name of the movies json zip file
        :return: None
        """
        try:
            with gzip.open(filename, "rt", encoding="utf-8") as f:
                # the JSON data should be a JSON list of movie objects in the
                # format described above.
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

        for movie in data:
            title: str = movie.get("title")
            plot: str = movie.get("fullplot")
            key: str = title
            vector: FloatVector = self.vectorize(plot)
            movie[self.VECTOR_FIELD] = vector
            await self.movies.put(key, movie)

    def vectorize(self, input_string: str) -> FloatVector:
        embeddings: List[float] = self.model.encode(input_string).tolist()
        return FloatVector(Vectors.normalize(embeddings))

    async def search(self, search_text: str, count: int, filter: Filter = Filters.always()) -> List[QueryResult]:
        vector: FloatVector = self.vectorize(search_text)
        search: SimilaritySearch = SimilaritySearch(self.VALUE_EXTRACTOR, vector, count)
        return await self.movies.aggregate(search, filter=filter)


MOVIE_JSON_FILENAME: Final[str] = "movies.json.gzip"


async def do_run() -> None:

    session: Session = await Session.create()
    movie_db: NamedMap[str, dict] = await session.get_map("movies")
    try:
        movies_repo = MovieRepository(movie_db)

        await movies_repo.load(MOVIE_JSON_FILENAME)
        results = await movies_repo.search("star travel and space ships", 5)
        for e in results:
            print(f"key = {e.key}, distance = {e.distance}, plot = {e.value.get('plot')}")

        cast_extractor = Extractors.extract("cast")
        filter = Filters.contains(cast_extractor, "Harrison Ford")
        results = await movies_repo.search("star travel and space ships", 5, filter)
        for e in results:
            print(f"key = {e.key}, distance = {e.distance}, plot = {e.value.get('plot')}")

    finally:
        await movie_db.truncate()
        await session.close()


asyncio.run(do_run())
