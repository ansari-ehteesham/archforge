"""
This File is used to run the RAG Pipeline from Collection -> Cleaning -> Converting to MD -> Storing in the RAG
"""

from archforge.rag.fetcher import HTMLFetcher
from archforge.utils import read_json


class RAGOrchestrator:
    def __init__(self):
        self.aws_services = read_json(
            file_path="src/archforge/rag/config.json",
            query="aws_cdk_api.api_references_url.*",
        )

        self.html_save_path = read_json(
            file_path="src/archforge/rag/config.json", query="upload_folder"
        ).get("raw_html")

        self.preprocess_md_save_path = read_json(
            file_path="src/archforge/rag/config.json", query="upload_folder"
        ).get("processed_md")

        self.html_fetcher = HTMLFetcher(save_path=self.html_save_path)

    def pipeline(self):
        """
        This is the main method which will invoke all the steps in the RAG Pipeline

        Step 1: Collect the AWS CDK HTML File and Save It
        """

        for i, service in enumerate(self.aws_services):
            print(f"{"="*10} Step {i+1} {"="*10}")
            step_01_result = self.html_fetcher.orchestrate(aws_service=service)
