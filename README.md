# ArchForge

ArchForge is an AI agent that converts AWS architecture design documents into AWS CDK infrastructure code in Python.

The project is also being developed as an AI engineering learning project, with a focus on agentic systems, RAG, MCP, AWS infrastructure automation, validation, evaluation, and safe deployment workflows.

## Description

The goal of ArchForge is to take a high-level architecture design, understand the required AWS resources and relationships, generate AWS CDK code, validate the generated infrastructure, and prepare it for deployment through a controlled GitHub-based workflow.

The agent must not have direct production AWS credentials.

The intended deployment workflow is:

Architecture Document
        ↓
AI Agent
        ↓
AWS CDK Code
        ↓
Validation
        ↓
GitHub Pull Request
        ↓
Human Review / Approval
        ↓
GitHub Actions
        ↓
AWS

The initial proof of concept will focus on:

- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB

The project will start narrow and expand gradually.

## Project Documentation

The `docs/` directory contains the project's research and daily learning history.

```text
docs/
└── daily/
    ├── YYYY-MM-DD.md
    ├── YYYY-MM-DD.md
    └── ...