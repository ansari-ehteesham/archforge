"""
In this file we'll use the Google Gemini Embedding Model 1 and store the embedding into the Chrom DB
"""

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json


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

    def store_data(self, data):
        """
        This function will use the embedding model and chromadb to embed the chunks and store it in the DB
        
        For now only 5 chunks will be taken from each service and store it in the chroma db
        """
    
        lambda_5_chunks = [chunk for  chunk in data if chunk.get("metadata").get("service")=="lambda"][:5]
        dynamodb_5_chunks = [chunk for  chunk in data if chunk.get("metadata").get("service")=="dynamodb"][:5]
        apigateway_5_chunks = [chunk for  chunk in data if chunk.get("metadata").get("service")=="apigateway"][:5]
        
        combined_lst = lambda_5_chunks + dynamodb_5_chunks + apigateway_5_chunks
        print(f"Length Combined List - {len(combined_lst)}")
        
        
        packeddata = [(d.get("id"), d.get("text"), d.get("metadata")) for d in combined_lst]
        ids, documents, metadata = zip(*packeddata)
        
        print(f"IDs - {len(ids)}")
        print(f"Documents - {len(documents)}")
        print(f"Metadatas - {len(metadata)}")
        
        
        self.collection.upsert(
            ids=list(ids),
            documents=list(documents),
            metadatas=list(metadata)
        )