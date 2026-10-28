"""
This Python File contain different helper or common function
"""

from glom import glom
import json
import os


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

def save(file_dir, file_name, data, extension:str):
        """
        This function save the different format file
        
        file_dir: File Directory
        file_name: file name which need to saved
        data: data which we need to save in the file
        extension: file extension (Do not include '.')
        """
        
        file_path_exists = os.path.exists(path=file_dir)
        
        if not file_path_exists:
            print(f"File Directory Doesn't exists. So, creating one - {file_dir}")
            os.mkdir(path=file_dir)
        
        file_name, _ = os.path.splitext(file_name)
        
        file_path = os.path.join(file_dir, f"{file_name}.{extension}")
        
        with open(file_path, "w", encoding="utf-8") as html_file:
            html_file.write(data)
            html_file.close()
            
        return file_path