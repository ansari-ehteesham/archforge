from archforge.rag.orchestrator import RAGOrchestrator
import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Archeforge CLI")

    # Define --pipeline as a string (defaulting to a sensible value if needed)
    parser.add_argument(
        "--pipeline",
        type=str,
        required=True,
        help="Name of the pipeline to run (e.g., RAG)",
    )

    # Handle boolean flags cleanly (True/False strings or boolean flags)
    parser.add_argument(
        "--rerun",
        type=lambda v: v.lower() == "true",
        default=False,
        help="Whether to force a rerun (True/False)",
    )

    return parser.parse_args()


def main():
    # Parse arguments coming from uv run Archeforge ...
    args = parse_args()

    # Retrieve and use the values
    print(f"Running pipeline: {args.pipeline}")
    print(f"Rerun enabled: {args.rerun} (type: {type(args.rerun).__name__})")

    if args.pipeline == "RAG" and args.rerun:
        RAGOrchestrator().pipeline()


if __name__ == "__main__":
    main()
