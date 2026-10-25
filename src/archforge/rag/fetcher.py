"""
This File contain the code for the HTML File Fetching
"""

from archforge.utils import read_json, save
import requests


class HTMLFetcher:
    def __init__(self):
        self.aws_services = read_json(
            file_path="src/archforge/rag/config.json",
            query="aws_cdk_api.api_references_url.*",
        )
        
        self.html_save_path = read_json(
            file_path="src/archforge/rag/config.json",
            query="upload_folder"
        ).get("raw_html")

    def fetch(self, url) -> str:
        """
        This method make a GET request on the url and return the HTML File.

        url: website url
        """

        try:
            response = requests.get(url=url)

            if response.status_code == 200:
                print(f"HTML File Retrived from {url}")
                return response.text
            else:
                print(
                    f"Unable to retrive the HTML File\nStatus Code - {response.status_code}"
                )
        except Exception as exc:
            raise str(exc)

    def orchestrate(self):
        """
        This method is just an push button for the fetcher to work
        """
        
        for i, service in enumerate(self.aws_services, start=0):
            print(f"URL - {service.get("url")}")
            print(f"Service Name and It's File Name - {service.get("file_name")}")
            
            html = self.fetch(url=service.get("url"))
            htmlFile = save(file_path=f"{self.html_save_path}/{service.get("file_name")}", data=html, extension="html")
            
            print(htmlFile)
            
        print(f"Completed all {i} services")
        return True
