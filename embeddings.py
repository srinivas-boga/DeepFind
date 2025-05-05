from sentence_transformers import SentenceTransformer
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient, Collection

class Embeddings:
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", db_path: str = None):
        """
        Initialize the Embeddings class with a specified model name.

        Args:
            model_name (str): The name of the model to be used for embeddings.
        """
        self.db_client = self.load_db_client(db_path) if db_path else None
        self.model = self.load_model(model_name)

    def load_db_client(self, db_path: str):
        """
        Load the database client.

        Args:
            db_path (str): The path to the database.
        """

        client = MilvusClient(db_path)
        # create a collection if it doesn't exist with schema id, file_name, and embedding
        collection_name = "embeddings"
        if not client.has_collection(collection_name):
            # Define the schema for the collection


            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)  # use your model's dim
            ]

            schema = CollectionSchema(fields, description="Custom embedding collection")
            client.create_collection(collection_name, schema = schema)
            # Create an index for the embedding field

            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }

            
            index_params = client.prepare_index_params()

            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )

            client.create_index(collection_name, index_params=index_params)

            
        return client


    def load_model(self, model_name: str):
        """
        Load the specified model.

        Args:
            model_name (str): The name of the model to be loaded.

        Returns:
            object: The loaded model.
        """
        model = SentenceTransformer(model_name)
        return model
    
    def get_embeddings(self, texts: list):
        """
        Get embeddings for a list of texts.

        Args:
            texts (list): A list of texts to get embeddings for.

        Returns:
            list: A list of embeddings.
        """
        embeddings = self.model.encode(texts)
        return embeddings
    

    def save_embeddings(self, embeddings: list, file_name: str, collection_name: str = "embeddings"):
        """
        Save embeddings to the database.

        Args:
            embeddings (list): A list of embeddings to save.
            file_name (str): The name of the file associated with the embeddings.
            collection_name (str): The name of the collection to save the embeddings to.
        """
        if self.db_client:
            self.db_client.load_collection(collection_name)
            self.db_client.insert(collection_name, [{"file_name": file_name, "embedding": embedding} for embedding in embeddings])
            self.db_client.flush(collection_name)


    def search_embeddings(self, query: str, top_k: int = 4, collection_name: str = "embeddings"):
        """
        Search for similar embeddings in the database.

        Args:
            query (str): The query text to search for.
            top_k (int): The number of top results to return.
            collection_name (str): The name of the collection to search in.

        Returns:
            list: A list of top_k similar embeddings.
        """
        if self.db_client:
            
            self.db_client.load_collection(collection_name)

            query_embedding = self.get_embeddings([query])[0]
            
            results = self.db_client.search(
                collection_name,
                data=[query_embedding],
                anns_field = "embedding",
                limit=5,
                search_params={"metric_type": "L2"},
                output_fields=["file_name"],
            )

            # Extract the file names from the results
            file_names = set([result.entity.get("file_name") for result in results[0]])
            return list(file_names)
            
        return []