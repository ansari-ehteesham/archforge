# ArchForge CDK Rules (v1)

These rules apply to every CDK project the agent creates. Version 1 supports one architecture only: Lambda + API Gateway + DynamoDB.

## Scope

1. Only these services are allowed: AWS Lambda, Amazon API Gateway, Amazon DynamoDB. Any other service (VPC, ECS, RDS, SQS, S3 and so on) is out of scope. If the design needs one, stop and tell the user.
2. The region is us-east-1.
3. The CDK language is Python 3.12 with CDK v2. Import all constructs from `aws-cdk-lib`.

## Naming

1. In v1, the stack class is named `ArchForgeInfraStack`. It is deployed under the same name. Do not rename it, because the deploy permissions depend on this name.
2. Never set `role_name` on any IAM role. Let CDK generate it. The deploy permissions only allow role names that start with `ArchForgeInfraStack-`.
3. Never set `table_name` on a DynamoDB table. Let CDK generate it. A fixed name blocks the next deploy if the old table is left behind.
4. Python code style: snake_case for variables, functions, methods, files and folders. PascalCase for classes. UPPER_SNAKE_CASE for constants.

## Project Structure

1. The CDK project lives in the `archforge-infra` repository.
2. Lambda code goes in the `lambda` folder in the project root. One Python file per Lambda function.
3. Do not edit `.github/workflows/`, `cdk.json` or the bootstrap settings. Only the user changes these.

## IAM and Security

1. Never give administrative access (`AdministratorAccess` or `Action: "*"` on `Resource: "*"`) to any resource.
2. The only managed policy allowed on a Lambda role is `AWSLambdaBasicExecutionRole`.
3. Give a Lambda access to DynamoDB with the table's grant methods (for example `grant_read_data`, `grant_write_data`). Do not write custom IAM policies by hand.
4. Never put secrets, access keys or tokens in code.
5. The agent never has AWS credentials and never deploys. Deployment is done only by GitHub Actions after the user approves.

## Lambda

1. Runtime is Python 3.12. Architecture is x86_64.
2. A Lambda behind API Gateway must return a dictionary with `statusCode` (integer), `body` (string) and `headers`. A wrong structure causes a 502 error.
3. The `body` must be a JSON string created with `json.dumps`. Set the `Content-Type` header to `application/json`.
4. Pass the DynamoDB table name to the Lambda through an environment variable. Do not hard-code it.
5. Each Lambda does one job (for example one saves an item, one reads items).

## API Gateway

1. Use an API Gateway REST API.
2. Every resource name is a single lowercase plural noun (for example `items`).
3. Every method (GET, POST and so on) must be connected to a Lambda function.

## DynamoDB

1. Create one standard table only. No extra indexes, no streams, no cache, no advanced settings.
2. The partition key is required. Add a sort key only if the architecture design asks for one. Do not add any other key.
3. Use on-demand billing (pay per request).

## Process

1. Write the CDK code from the architecture design given by the user.
2. Run `cdk synth` and show the output to the user. If it fails, fix the code and run it again.
3. Wait for the user's approval of the CDK code. Do not continue without it.
4. After approval, create a new branch, add the code and raise a Pull Request.
5. Never push to the `main` branch.