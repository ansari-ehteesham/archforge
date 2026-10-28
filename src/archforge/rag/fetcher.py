"""
This File contain the code for the HTML File Fetching
"""

from archforge.utils import save
import requests
from requests.exceptions import Timeout, HTTPError, ConnectionError


class HTMLFetcher:
    def __init__(self, save_path, prog_lang):
        self.html_save_path = save_path
        self.cdk_prog_lang = prog_lang

    def fetch(self, url) -> str:
        """
        This method make a GET request on the url and return the HTML File.

        url: website url
        """

        try:
            query_param = {"lang": self.cdk_prog_lang}

            response = requests.get(url=url, params=query_param, timeout=10)

            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"HTML File Retrived from {url}")
                return response.text
        except Timeout:
            raise Timeout("Error: Request Timeout. The server took long time to response")
        except ConnectionError:
            raise ConnectionError("Error: Network issue or DNS failure. Check your Internet Connection")
        except HTTPError as http_error:
            raise HTTPError(f"Error: HTTP Error Occured - {http_error}")
        except Exception as exc:
            raise Exception(f"An unexpected error occured - {exc}")

    def orchestrate(self, aws_service):
        """
        This method is just an push button for the fetcher to work
        """

        print(f"URL - {aws_service.get("url")}")
        print(f"Service Name and It's File Name - {aws_service.get("file_name")}")

        html = self.fetch(url=aws_service.get("url"))
        htmlFile = save(
            file_dir=self.html_save_path,
            file_name=aws_service.get("file_name"),
            data=html,
            extension="html",
        )

        return htmlFile
