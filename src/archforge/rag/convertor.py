"""
This file contain the process of converting the Processed HTML File in the MarkDown File
"""

from html_to_markdown import convert, ConversionOptions
from archforge.utils import save

class Convertor:
    def __init__(self, md_file_path):
        self.saved_file_path = md_file_path
        
    def add_metadata(self):
        pass
    
    def orchestrator(self, processed_html, service, service_url, datetime):
        """
        This function will convert the HTML to Markdown and save it
        
        html_file: Processed HTML File Path
        """
        if isinstance(processed_html, str):
            OPTIONS = ConversionOptions(
                compact_tables=True,
                code_language="python"
            )
            result = convert(html=processed_html, options=OPTIONS)
            
            metadata = (
            "---\n"
            f"source: {service_url}\n"
            f"service: {service}\n"
            f"fetched: {datetime}\n"
            "---\n"
            )
            
            content = "".join([metadata, result.content])
        else:
            raise TypeError(f"Processed HTML is not wrapped in String. Type = {type(processed_html)}")
        
        md_file_path = save(
            file_dir=self.saved_file_path,
            file_name=service,
            data=content,
            extension="md"
        )
        
        return md_file_path