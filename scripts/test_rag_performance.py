import json
from archforge.rag.orchestrator import RAGOrchestrator

def run_evaluation():
    # Load test cases
    with open("scripts/rag_eval_cases.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    orchestrator = RAGOrchestrator()
    retrieval_hits = 0
    total_tests = len(test_cases)

    print(f"Starting RAG Retrieval Evaluation across {total_tests} test cases...\n")

    for i, test in enumerate(test_cases):
        query = test["query"]
        expected_service = test["expected_service"]
        expected_keywords = test["expected_keywords"]

        print(f"Test Case {i+1}: {query}")
        
        # Query your RAG database (returns top 5 chunks by default)
        result = orchestrator.storedb.query(query)
        
        retrieved_metadatas = result.get("metadatas", [[]])[0]
        retrieved_documents = result.get("documents", [[]])[0]

        # Check Hit Rate: Did any of the top results match the expected service?
        matched_services = [meta.get("service") == expected_service for meta in retrieved_metadatas]
        is_service_hit = any(matched_services)

        # Check Keyword Recall: Are key terms present in the retrieved text chunks?
        combined_text = " ".join(retrieved_documents)
        keyword_matches = [kw.lower() in combined_text.lower() for kw in expected_keywords]
        keyword_recall_score = sum(keyword_matches) / len(expected_keywords)

        if is_service_hit:
            retrieval_hits += 1
            print(f"  ✅ Service Match Found ({expected_service})")
        else:
            print(f"  ❌ Service Mismatch. Got: {[m.get('service') for m in retrieved_metadatas]}")

        print(f"  📊 Keyword Recall Score: {keyword_recall_score * 100:.1f}%\n" + "-"*40)

    print(f"Final Retrieval Hit Rate (Precision @ K): {retrieval_hits / total_tests * 100:.1f}%")

if __name__ == "__main__":
    run_evaluation()