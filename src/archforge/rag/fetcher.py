"""
This File contain the code for the HTML File Fetching
"""

from archforge.utils import save
import requests


class HTMLFetcher:
    def __init__(self, save_path):
        self.html_save_path = save_path

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

    def orchestrate(self, aws_service):
        """
        This method is just an push button for the fetcher to work
        """

        print(f"URL - {aws_service.get("url")}")
        print(f"Service Name and It's File Name - {aws_service.get("file_name")}")

        html = self.fetch(url=aws_service.get("url"))
        htmlFile = save(
            file_path=f"{self.html_save_path}/{aws_service.get("file_name")}",
            data=html,
            extension="html",
        )

        print(htmlFile)
