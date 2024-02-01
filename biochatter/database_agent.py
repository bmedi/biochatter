import json
from .prompts import BioCypherPromptEngine
import neo4j_utils as nu
from langchain.schema import Document


class DatabaseAgent:
    def __init__(
        self,
        model_name: str,
        connection_args: dict,
        schema_config_or_info_dict: dict,
    ) -> None:
        """
        Create a DatabaseAgent analogous to the VectorDatabaseAgentMilvus class,
        which can return results from a database using a query engine. Currently
        limited to Neo4j for development.

        Args:
            connection_args (dict): A dictionary of arguments to connect to the
                database. Contains database name, URI, user, and password.
        """
        self.prompt_engine = BioCypherPromptEngine(
            model_name=model_name,
            schema_config_or_info_dict=schema_config_or_info_dict,
        )
        self.connection_args = connection_args
        self.driver = None

    def connect(self) -> None:
        """
        Connect to the database and authenticate.
        """
        db_name = self.connection_args.get("db_name")
        uri = f"{self.connection_args.get('host')}:{self.connection_args.get('port')}"
        user = self.connection_args.get("user")
        password = self.connection_args.get("password")
        self.driver = nu.Driver(
            db_name=db_name or "neo4j",
            uri=uri,
            user=user,
            password=password,
        )
    def is_connected(self) -> bool:
        return not self.driver is None

    def get_query_results(self, query: str, k: int = 3) -> list[Document]:
        """
        Generate a query using the prompt engine and return the results.
        Replicates vector database similarity search API. Results are returned
        as a list of Document objects to align with the vector database agent.

        Args:
            query (str): A query string.

            k (int): The number of results to return.

        Returns:
            list[Document]: A list of Document objects. The page content values
                are the literal dictionaries returned by the query, the metadata
                values are the cypher query used to generate the results, for
                now.
        """
        cypher_query = self.prompt_engine.generate_query(query)
        # TODO some logic if it fails?
        results = self.driver.query(query=cypher_query)

        documents = []
        # return first k results
        # returned nodes can have any formatting, and can also be empty or fewer
        # than k
        for result in results:
            documents.append(
                Document(
                    page_content=json.dumps(result),
                    metadata={
                        "cypher_query": cypher_query,
                    },
                )
            )
            if len(documents) == k:
                break

        return documents