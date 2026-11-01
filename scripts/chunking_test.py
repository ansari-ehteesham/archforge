chunk_size = 10
overlap_size = 5


def text_splitter(data):
    """
    This function help to split the data based on the chunk size and overlap size
    """

    lst_of_chunks = []
    for i in range(0, len(data), chunk_size):
        print(f"i value is = {i}")
        if i == 0:
            lst_of_chunks.append(data[i : chunk_size])
        else:
            lst_of_chunks.append(data[(i - overlap_size) : (i + chunk_size)])
            
    return lst_of_chunks

def main():
    with open("data/processed_md/rules.md", "r", encoding="utf-8") as file:
        data = file.read()
        
    chunks = text_splitter(data=data[:100])
    print(f"There are total {len(chunks)} Chunks")
    
    print(f"First Chunk - \n{chunks[0]}")
    print(f"\nSecond Chunk - \n{chunks[1]}")
    print(f"\nThird Chunk - \n{chunks[2]}")
    
    
if __name__ == "__main__":
    main()