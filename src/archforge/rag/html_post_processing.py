"""
This file contain the whole pipeline of cleaning or post-processing the HTML file
"""

import os
from bs4 import BeautifulSoup, SoupStrainer
from archforge.utils import save


class HTMLPostProcessing:
    def __init__(self, process_html_path, prog_lang):
        self.prog_lang = prog_lang
        self.processed_html_file = process_html_path

    def select_lang(self, soup):
        """
        This Function remove the other code snippet except Python
        """
        lang_variants = soup.find_all("div", class_="lang-variant")
        for div in lang_variants:
            if div.get("data-lang") != self.prog_lang:
                div.decompose()
                
        # remove the python heading also
        for span in soup.find_all("span", class_="lang"):
            span.decompose()

        return soup

    def remove_anchor(self, soup):
        """
        This function remove the link.
        """
        heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
        for heading in soup.find_all(heading_tags):
            # Target by class name used in static site generators (VitePress/Docusaurus)
            for anchor in heading.find_all("a", class_="header-anchor"):
                anchor.decompose()  # Deletes <a class="header-anchor">...</a> entirely

            # Fallback: remove any remaining <a> tags inside headings if they lack the class
            for remaining_a in heading.find_all("a"):
                remaining_a.decompose()

        for a in soup.find_all("a"):
            a.unwrap()

        return soup
    
    def remove_last_table(self, soup):
        """
        This function remove the current and next adjacent element from the HTML
        """
        
        current_element = soup.find(id="module-types")
        
        if current_element:
            next_sibling = current_element.find_next_sibling("table")
        if next_sibling:
            next_sibling.decompose()
            
        current_element.decompose()
        
        return str(soup)
        

    def orchestrator(self, html_file_path):
        if not os.path.exists(path=html_file_path):
            raise FileNotFoundError(f"File Not Found - {html_file_path}")

        # load the file
        only_main = SoupStrainer(name="main")
        with open(file=html_file_path, mode="r", encoding="utf-8") as html_file:
            soup = BeautifulSoup(html_file.read(), "html.parser", parse_only=only_main)
            html_file.close()

        # Select only the Choosen Programming Language
        step_01_result = self.select_lang(soup=soup)

        # Remove the Anchor Tag / link
        step_02_result = self.remove_anchor(soup=step_01_result)
        
        # Remove the last tables - "Types"
        step_03_result = self.remove_last_table(soup=step_02_result)

        # Save the processed html file
        save(
            file_dir=self.processed_html_file,
            file_name=os.path.basename(html_file_path),
            data=step_03_result,
            extension="html",
        )

        return step_03_result
