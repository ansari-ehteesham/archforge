"""
This file is used to create multiple chunks of the data.
"""

import frontmatter
import re
import json


class Chunker:
    def __init__(self, chunk_size, overlap_size):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

        if self.chunk_size <= self.overlap_size:
            raise ValueError(
                f"Overlap Size (which is {self.overlap_size}) is greater than Chunk Size (which is {self.chunk_size})"
            )

    def code_identifier(self, line: str):
        """
        This function help to identify the code block and store it with proper metadata.
        """

        result = line.strip("\n").startswith("```")
        return result

    def text_splitter(self, data: str):
        """
        This function help to split the data based on the chunk size and overlap size
        """

        lst_of_chunks = []
        i = 0
        while i < len(data):

            if len(data[i : (i + self.chunk_size)]) == self.chunk_size:
                lst_of_chunks.append(data[i : (i + self.chunk_size)])
                if i + self.chunk_size >= len(data):
                    break
                i += self.chunk_size - self.overlap_size
            else:
                lst_of_chunks.append(data[i:])
                i += len(data[i:])

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
        section, content, code_block = {}, "", ""
        lst_of_content = []
        in_code_block = False
        header_regex = re.compile(r"^(#{1,6})\s+(.+)")

        for line in data.splitlines():
            if self.code_identifier(line=line):
                in_code_block = not in_code_block
                code_block += line + "\n"
                continue

            if in_code_block:
                code_block += line + "\n"
                continue

            if not in_code_block and code_block:
                lst_of_content.append(content)
                content = ""
                lst_of_content.append(code_block)
                code_block = ""

            # Header matches
            match = header_regex.match(line)

            # Add content to the section content
            if section and not match:
                content += line + "\n"

            if match:
                if section:
                    lst_of_content.append(content)
                    section.update(
                        {"content": [item for item in lst_of_content if item.strip()]}
                    )
                    headers.append(section)
                    section, content, code_block = {}, "", ""
                    lst_of_content = []
                section["header"] = match.group(2)

        lst_of_content.append(content)
        lst_of_content.append(code_block)
        section.update({"content": [item for item in lst_of_content if item.strip()]})
        headers.append(section)

        return headers

    def packing(self, data):
        # print(json.dumps(data, indent=4))
        temp = ""
        content = []
        for i, block in enumerate(data.get("content")):
            if i == 0 and block:
                block = data.get("header") + block
            if block:
                if len(temp + block) <= self.chunk_size:
                    temp += block
                else:
                    if temp:
                        content.append(temp)
                    temp = block
                    if len(block) > self.chunk_size and not self.code_identifier(block):
                        split_text = self.text_splitter(data=block)
                        content.extend(split_text)
                        temp = ""
            else:
                continue
        if temp:
            content.append(temp)
        return content

    def start_chunking(self, md_file_path):
        self.chunk_json = {}

        with open(md_file_path, "r", encoding="utf-8") as file:
            data = file.read()

        extract_file_metadata = self.extract_metadata(data_type="document", data=data)

        if extract_file_metadata:
            self.chunk_json["source"] = extract_file_metadata.get("source")
            self.chunk_json["service"] = extract_file_metadata.get("service")
            self.chunk_json["fetched"] = extract_file_metadata.get("fetched")

        lst_header_section = self.extract_text(data=data)

        if lst_header_section:
            self.chunk_json["data"] = lst_header_section

        # print(json.dumps(self.chunk_json["data"][0], indent=4))

        # Now, let's get the finalised data
        for i, data in enumerate(self.chunk_json.get("data")):
            self.chunk_json.get("data")[i]["content"] = self.packing(data=data)
            self.chunk_json.get("data")[i]["metadata"] = data.get("header")
            print(f"Data - {json.dumps(data, indent=4)}")

        return self.chunk_json
