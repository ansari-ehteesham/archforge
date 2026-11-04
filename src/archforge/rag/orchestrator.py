"""
This File is used to run the RAG Pipeline from Collection -> Cleaning -> Converting to MD -> Storing in the RAG
"""

from archforge.rag.fetcher import HTMLFetcher
from archforge.rag.html_post_processing import HTMLPostProcessing
from archforge.rag.convertor import Convertor
from archforge.rag.chunker import Chunker
from archforge.rag.store import StoreDB
from archforge.utils import read_json
from pathlib import Path
import json

class RAGOrchestrator:

    ROOT_DIR = Path(__file__).resolve().parent
    CONFIG_FILE = ROOT_DIR / "config.json"

    def __init__(self):
        self.aws_services = read_json(
            file_path=self.CONFIG_FILE,
            query="aws_cdk_api.api_references_url.*",
        )

        self.html_save_path = read_json(
            file_path=self.CONFIG_FILE, query="upload_folder"
        ).get("raw_html")

        self.process_html_save_path = read_json(
            file_path=self.CONFIG_FILE, query="upload_folder"
        ).get("process_html")

        self.preprocess_md_save_path = read_json(
            file_path=self.CONFIG_FILE, query="upload_folder"
        ).get("processed_md")

        self.cdk_programming_language = read_json(
            file_path=self.CONFIG_FILE,
            query="aws_cdk_api.programming_language",
        )

        self.chunk_detail = read_json(
            file_path=self.CONFIG_FILE,
            query="docs_chunk",
        )

        self.embedding_model = read_json(
            file_path=self.CONFIG_FILE,
            query="embedding_model",
        )

        self.chromadb_config = read_json(
            file_path=self.CONFIG_FILE,
            query="chromadb",
        )

        self.html_fetcher = HTMLFetcher(
            save_path=self.html_save_path, prog_lang=self.cdk_programming_language
        )

        self.html_processing = HTMLPostProcessing(
            process_html_path=self.process_html_save_path,
            prog_lang=self.cdk_programming_language,
        )

        self.html_to_md_convertor = Convertor(md_file_path=self.preprocess_md_save_path)

        self.chunker = Chunker(
            chunk_size=self.chunk_detail.get("size"),
            overlap_size=self.chunk_detail.get("overlap"),
        )

        self.storedb = StoreDB(
            embedding_model_config=self.embedding_model,
            store_path=self.ROOT_DIR,
            chromadb_config=self.chromadb_config,
        )

    def pipeline(self):
        """
        This is the main method which will invoke all the steps in the RAG Pipeline

        Step 1: Collect the AWS CDK HTML File and Save It
        """

        for i, service in enumerate(self.aws_services):
            print(f"{"="*10} Service {i+1} {"="*10}")

            # Fecthing adn saving the HTML File with Python as Language
            save_file_path, url, datetime = self.html_fetcher.orchestrate(
                aws_service=service
            )

            # Cleaning the saved HTML File
            processed_html = self.html_processing.orchestrator(save_file_path)

            # Converting the Processed HTML File into Markdown File and Saving it
            md_convert_file = self.html_to_md_convertor.orchestrator(
                processed_html, service.get("file_name"), url, datetime
            )

            # Chunking the MD file data
            chunk_json = self.chunker.start_chunking(md_file_path=md_convert_file)

            # Flattening the Data into a proper list.
            flatten_data = self.storedb.flatten_data(data=chunk_json)
            print(
                f"There are {len(flatten_data)} number of chunks"
            )

        # Now, we have one flatten_data which include all the services chunks
        collection_data = self.storedb.store_data(data=flatten_data)
        
        if not collection_data:
            raise RuntimeError("Stored count does not match the number of chunks")
        
    def query(self, query):
        """
        This method is used for querying the RAG Database
        
        query: str - User Query will come
        """
        
        result = self.storedb.query(query)
        print(f"This is the result of the Query -\n{json.dumps(result, indent=4)}")