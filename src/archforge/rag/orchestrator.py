"""
This File is used to run the RAG Pipeline from Collection -> Cleaning -> Converting to MD -> Storing in the RAG
"""

from archforge.rag.fetcher import HTMLFetcher
from archforge.rag.html_post_processing import HTMLPostProcessing
from archforge.utils import read_json
from pathlib import Path


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

        self.html_fetcher = HTMLFetcher(
            save_path=self.html_save_path, prog_lang=self.cdk_programming_language
        )

        self.html_processing = HTMLPostProcessing(
            process_html_path=self.process_html_save_path,
            prog_lang=self.cdk_programming_language,
        )

    def pipeline(self):
        """
        This is the main method which will invoke all the steps in the RAG Pipeline

        Step 1: Collect the AWS CDK HTML File and Save It
        """

        for i, service in enumerate(self.aws_services):
            print(f"{"="*10} Service {i+1} {"="*10}")

            # Fecthing adn saving the HTML File with Python as Language
            save_file_path = self.html_fetcher.orchestrate(aws_service=service)

            # Cleaning the saved HTML File
            processed_html = self.html_processing.orchestrator(save_file_path)
