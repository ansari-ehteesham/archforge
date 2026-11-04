from archforge.rag.orchestrator import RAGOrchestrator
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Archeforge CLI")

    # Define --pipeline as a string (defaulting to a sensible value if needed)
    parser.add_argument(
        "--pipeline",
        type=str,
        required=True,
        choices=["RAG"],
        help="Name of the pipeline to run (e.g., RAG)",
    )

    # Handle boolean flags cleanly (True/False strings or boolean flags)
    parser.add_argument(
        "--rerun",
        type=lambda v: v.lower() == "true",
        default=False,
        help="Whether to force a rerun (True/False)",
    )
    
    # Handling the Query argument
    parser.add_argument(
        "--query",
        type=str,
        required=False,
        help="Enter the Query to search in RAG DB"
    )

    return parser.parse_args()


def main():
    # Parse arguments coming from uv run Archeforge ...
    args = parse_args()

    # Retrieve and use the values
    print(f"Running pipeline: {args.pipeline}")
    print(f"Rerun enabled: {args.rerun} (type: {type(args.rerun).__name__})")

    if args.pipeline == "RAG":
        if args.rerun:
            print(f"Running the whole RAG Pipeline")
            RAGOrchestrator().pipeline()
        elif args.query:
            print(f"User Query - {args.query}")
            RAGOrchestrator().query(args.query)
        else:
            print('Nothing to do. Use --rerun true to build the DB, or --query "..." to search.')


if __name__ == "__main__":
    main()
