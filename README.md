# ArchForge

> **Status:** Just started. I have a clear goal, but the details will be decided and checked step by step as I build.

## 1. Project Goal

Build an AI agent that reads an AWS architecture design and creates the AWS infrastructure for it using code (AWS CDK in Python). The agent also tests that the infrastructure works.

This is also my self-improvement project to learn AI, RAG and MCP.

## 2. Current Version Scope (Version 1)

Keep it small:

- One simple architecture only: **Lambda + API Gateway + DynamoDB**
- The AI agent creates the CDK code and checks it
- A human approves at two places (see the workflow)
- The infrastructure is deployed to AWS
- The AI agent tests the deployed infrastructure (for example: is the Lambda giving the correct response?) and tells me if it works as expected

Not in Version 1: bigger architectures (VPC, ECS, RDS), and anything extra.

## 3. Full Workflow

1. I give the architecture design to the AI agent.
2. The agent understands it and writes the CDK code.
3. The agent checks the code for errors.
4. **Human approval 1:** I review and approve the CDK code.
5. The agent creates a new branch, adds the code, and raises a Pull Request (PR) on GitHub.
6. **Human approval 2:** I review the PR, approve it, and merge it to the `main` branch.
7. GitHub Actions starts automatically and creates the stack in AWS.
8. The AI agent gets a signal that the stack is deployed (or I tell it that the PR is merged).
9. The agent tests the architecture, for example whether the Lambda gives a proper response.
10. The agent gives me the result: working as expected or not.

**Rule:** The AI agent never gets direct AWS credentials. Only GitHub Actions deploys to AWS.

## 4. Technical Stack

- Python
- uv
- Git
- GitHub
- VS Code (IDE)

More tools (for RAG, LLM and MCP) will be added when I reach those steps.

## 5. Taking Help From

- Claude
- ChatGPT