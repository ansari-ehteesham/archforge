"""
This file contain the process of converting the Processed HTML File in the MarkDown File
"""

from html_to_markdown import convert
from archforge.utils import save

class Convertor:
    def __init__(self, md_file_path):
        self.saved_file_path = md_file_path
    
    def orchestrator(self, processed_html, service):
        """
        This function will convert the HTML to Markdown and save it
        
        html_file: Processed HTML File Path
        """
        if isinstance(processed_html, str):
            result = convert(html=processed_html)
        else:
            raise TypeError(f"Processed HTML is not wrapped in String. Type = {type(processed_html)}")
        
        md_file_path = save(
            file_dir=self.saved_file_path,
            file_name=service,
            data=result.content,
            extension="md"
        )
        
        return md_file_path