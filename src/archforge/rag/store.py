"""
In this file we'll use the Google Gemini Embedding Model 1 and store the embedding into the Chrom DB
"""

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from archforge.utils import countdown_time

class EmptyCollectionError(ValueError):
    """Raised when trying to query a Chroma DB collection with no documents."""
    pass

class StoreDB:
    def __init__(self, embedding_model_config, store_path, chromadb_config):
        self.embedding_model = embedding_functions.GoogleGeminiEmbeddingFunction(
            model_name=embedding_model_config.get("model_name"),
            task_type=embedding_model_config.get("model_task"),
            dimension=embedding_model_config.get("output_dimension"),
        )

        self.client = chromadb.PersistentClient(
            path=f"{store_path}/{chromadb_config.get("folder_name")}"
        )

        # create a single collection known as cdk-docs
        self.collection = self.client.get_or_create_collection(
            name=chromadb_config.get("collection_name"),
            embedding_function=self.embedding_model,
            metadata={
                "hnsw:space": "cosine"
            }
        )
        print(f"Created the DB Collection - {chromadb_config.get("collection_name")}")
        print(f"Embedding Model - {self.embedding_model.model_name}")

        # flatten list
        self.preapred_data = []

    def db_heartbeat(self):
        return self.client.heartbeat()

    def flatten_data(self, data):
        """
        This function convert the data structure into the list form

        Output Structuer need to look like this
        [
            {
                "id": "lambda-12-0",
                "text": "Execution Role\\n\\nLambda functions assume an IAM role ...",
                "metadata": {
                "service": "lambda",
                "source": "https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html?lang=python",
                "fetched": "Mon, 02 Nov 2026 22:23:36 GMT",
                "header": "Execution Role",
                "section_index": 12,
                "chunk_index": 0
                }
            },
            { "id": "lambda-12-1", "text": "...", "metadata": { "...": "..." } }
        ]

        id = service + section number + chunk number
        """
        # total_no_section = len(data.get("data"))
        service = data.get("service")
        source = data.get("source")
        fetched = data.get("fetched")

        for i, section in enumerate(data.get("data")):
            section_json = {}
            header = section.get("header")
            section_index = i
            chunk_size = len(section.get("content"))

            print(
                f"Total {chunk_size} Chunks in the section number {i} with header {header} in service - {service}"
            )

            # looping the inner chunks of the content
            for j, chunk in enumerate(section.get("content")):
                text = chunk
                chunk_index = j
                id = f"{service}-{section_index}-{chunk_index}"

                # now appending each prepared in the list
                section_json = {
                    "id": id,
                    "text": text,
                    "metadata": {
                        "service": service,
                        "source": source,
                        "section_index": section_index,
                        "header": header,
                        "fetched": fetched,
                        "chunk_index": chunk_index,
                    },
                }

                self.preapred_data.append(section_json)
        return self.preapred_data
    
    def query(self, query):
        """
        This method take the collection and embedding model and do the similarity search
        Config:
        Number of result in Return = 5
        Including Information - Metadata, Documents, Distances
        
        query: str - user query
        """
        
        # check if the data is there or not
        if self.collection.count() == 0:
            raise EmptyCollectionError(f"Cannot query '{self.collection.name}'. The collection is completely empty.")
        
        result = self.collection.query(
            query_texts=[query],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        
        return result
        

    def store_data(self, data, batch_size=20, wait_time = 20, retries = 3):
        """
        This function will use the embedding model and chromadb to embed the chunks and store it in the DB
        
        Batch Processing Need to be done in this function
        
        batch_size : default = 20 chunks
        waiting time : default = 20 seconds
        retries : default = 3 retires
        """
        
        try:
            db_heartbeat = self.db_heartbeat()
            print(f"Connection is Successfully Established with Database \n{db_heartbeat}")
        except Exception as e:
            raise Exception(f"There is some connection Error with the ChromaDB Database - {e}")
        
        total_lenght_data = len(data)
        
        for i in range(0, total_lenght_data, batch_size):
            batch_data = data[i : (i+batch_size)]
            
            packeddata = [(d.get("id"), d.get("text"), d.get("metadata")) for d in batch_data]
            ids, documents, metadatas = zip(*packeddata)
            
            print(f"Batch Number - {i}")
            print(f"Total IDs - {len(ids)}")
            print(f"Total Documents - {len(documents)}")
            print(f"Total Metadatas - {len(metadatas)}")
            
            for attempt in range(retries):
                try:
                    print(f"Attempt Number - {attempt}")
                    self.collection.upsert(
                        ids=list(ids),
                        documents=list(documents),
                        metadatas=list(metadatas)
                    )
                    
                    break
                except Exception as e:
                    print(f"Attempt {attempt} is failed due to - {e}")
                    if attempt == retries - 1:
                        print(f"All Attempt has been finished for the batch - {i}")
                        raise
                    countdown_time(60)
                    
            print(f"Batch Number - {i} is Completed within {attempt} Attempt")
            countdown_time(wait_time)
            
        if self.collection.count() == total_lenght_data:
            return True
        else:
            return False