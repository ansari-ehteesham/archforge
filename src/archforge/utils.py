"""
This Python File contain different helper or common function
"""

from glom import glom
import json


def read_json(file_path, query: str = "*"):
    """
    It reads the JSON file and query that JSON structure to get exact result

    file_path: Relative File Path of the JSON file
    query: used to query the JSON Structure
        - default value is "*" which means it will take whole JSON Structure and return it as it is
    """
    with open(file_path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
    result = glom(target=json_data, spec=query)
    return result

def save(file_path, data, extension:str):
        """
        This function save the different format file
        
        file_path: Relative path of the file
        data: data which we need to save in the file
        extension: file extension (Do not include '.')
        """
        
        with open(f"{file_path}.{extension}", "w", encoding="utf-8") as html_file:
            html_file.write(data)
            html_file.close()
            
        return f"File Saved Succussfully in {file_path}.{extension}"