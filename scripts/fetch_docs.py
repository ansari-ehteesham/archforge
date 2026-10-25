"""
This script will extract the HTML file of the AWS CDK Docs for specific resources and convert it into the Markdown structure
and save it as a .md file
"""

import requests
from bs4 import BeautifulSoup
from html_to_markdown import convert

URL = "https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb-readme.html?lang=python"


def extract_html():
    # 1. Fetch the website content
    response = requests.get(URL)

    # 2. Check if the request was successful
    if response.status_code == 200:
        # 3. Save the HTML content into a local file
        with open("aws_dynamodb_cdk.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("HTML file saved successfully!")
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        
def convertor(html_file):
    """
    This function convert the HTML File to a Markdown File
    """
    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "html.parser")
        
    # Clean the HTML File
    html_content = remove_lang(soup=soup)
    html_content = remove_link_heading(html_content)
        
    result = convert(html=html_content)
    
    with open("aws_dynamodb_cdk.md", "w", encoding="utf-8") as file:
        file.write(result.content)
        file.close()
    
    print("MarkDown File has been saved")
    
    
def remove_lang(soup):
    """
    This Function remove the other code snippet except Python
    """
    lang_variants = soup.find_all("div", class_="lang-variant")
    for div in lang_variants:
        if div.get("data-lang") != "python":
            div.decompose()
            
    return soup


def remove_link_heading(soup):
    """
    This function remove the link from the h1 to h6 tags.
    """
    
    heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
    for heading in soup.find_all(heading_tags):
        # Target by class name used in static site generators (VitePress/Docusaurus)
        for anchor in heading.find_all("a", class_="header-anchor"):
            anchor.decompose()  # Deletes <a class="header-anchor">...</a> entirely
        
        # Fallback: remove any remaining <a> tags inside headings if they lack the class
        for remaining_a in heading.find_all("a"):
            remaining_a.decompose()
            
    return str(soup)
    
        
        
if __name__ == "__main__":
    extract_html()
    convertor(html_file="aws_dynamodb_cdk.html")
