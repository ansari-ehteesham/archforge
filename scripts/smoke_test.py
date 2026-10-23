"""
This file is for testing the API Gateway Endpoint -> Lambda -> Dynamo DB by sending the request and receving the data which should match.
In this file the workflow which are going to test is the workflow is manually deployed workflow thorugh the GitHub Action. Check Github 
repo - ArchForgeInfra
branch - feature/initial-cdk-stack
"""

import os
import requests
import random
from typing import Dict

# Fetch the API URL
API_URL = os.environ["MANUAL_API_URL"]

def create_item():
    """
    Requesst Body Structure
    body: {"item": "...", "type": "..."}
    """
    data = {
        "item": random.choice(["Artificial Intelligence", "AWS", "Python", "Machine Learning", "Deep Learning"]),
        "type": random.choice(["Cloud", "Technology", "Programming Language", "Algorithm"])
    }
    
    header = {
        "Content-Type": "application/json"
    }
    response = requests.post(
        url=f"{API_URL}/items",
        headers=header,
        json=data
    )
    
    print(f"API Response - {response.json()}")
    
    return response.json()
    

def read_item() -> Dict:
    """
    Read all the data present in the DB
    """
    response = requests.get(url=f"{API_URL}/items")
    
    print(f"Full DB Read \n{response.json()}")
    
    return response.json()

def test_workflow():
    post_res = create_item()
    get_res = read_item() # Expected list of dicts from DynamoDB
    
    # Target values we actually inserted
    target_item = post_res.get("item")
    target_type = post_res.get("type")
    
    # Check if any record in the DB matches our inserted item & type
    match_found = any(
        record.get("item") == target_item and record.get("type") == target_type
        for record in get_res
    )
    
    if match_found:
        print(f"Workflow Work Successful - Found item '{target_item}' in DB")
        return True
    else:
        print(f"Workflow failed - Could not find ({target_item}, {target_type}) in:\n{get_res}")
        return False

        
        
if __name__ == "__main__":
    result = test_workflow()
    print(result)