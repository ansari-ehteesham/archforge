"""
This file is used to create multiple chunks of the data.
"""

import frontmatter
import re


class Chunker:
    def __init__(self, chunk_size, overlap_size):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    def code_identifier(self, line):
        """
        This function help to identify the code block and store it with proper metadata.
        """

        result = line.startswith("```")
        return result

    def text_splitter(self, data):
        """
        This function help to split the data based on the chunk size and overlap size
        """

        lst_of_chunks = []
        for i in range(0, len(data), self.chunk_size):
            if i == 0:
                lst_of_chunks.append(data[i : self.chunk_size])
            else:
                lst_of_chunks.append(
                    data[(i - self.overlap_size) : (i + self.chunk_size)]
                )

        print(f"There are total {len(lst_of_chunks)} chunks")
        return lst_of_chunks

    def extract_metadata(self, data_type, data):
        """
        This function will extract the metadata of the document or the chunk
        """

        if data_type == "document":
            """
            Need to extract the source, service and fetched date
            """
            metadata, _ = frontmatter.parse(text=data)
            return metadata
        else:
            pass

    def extract_text(self, data: str):

        headers = []
        section, content = {}, ""
        in_code_block = False
        header_regex = re.compile(r"^(#{1,6})\s+(.+)")

        for i, line in enumerate(data.splitlines()):
            if self.code_identifier(line=line):
                in_code_block = not in_code_block
                content += line + "\n"
                continue

            if in_code_block:
                content += line + "\n"
                continue

            # Header matches
            match = header_regex.match(line)

            # Add content to the section content
            if section and not match:
                content += line + "\n"

            if match:
                if section:
                    section.update({"content": content})
                    headers.append(section)
                    section, content = {}, ""
                section["header"] = match.group(2)

        section.update({"content": content})
        headers.append(section)

        return headers

    def start_chunking(self, md_file_path):
        self.chunk_json = {}

        with open(md_file_path, "r", encoding="utf-8") as file:
            data = file.read()
            file.close()

        extract_file_metadata = self.extract_metadata(data_type="document", data=data)

        if extract_file_metadata:
            self.chunk_json["source"] = extract_file_metadata.get("source")
            self.chunk_json["service"] = extract_file_metadata.get("service")
            self.chunk_json["fetched"] = extract_file_metadata.get("fetched")

        lst_header_section = self.extract_text(data=data)

        if lst_header_section:
            self.chunk_json["data"] = lst_header_section
            
        print(self.chunk_json)
