# Amazon API Gateway Construct Library

Amazon API Gateway is a fully managed service that makes it easy for developers to publish, maintain, monitor, and secure APIs at any scale. Create an API to access data, business logic, or functionality from your back-end services, such as applications running on Amazon Elastic Compute Cloud (Amazon EC2), code running on AWS Lambda, or any web application.

## Defining APIs

APIs are defined as a hierarchy of resources and methods. `addResource` and `addMethod` can be used to build this hierarchy. The root resource is `api.root`.

For example, the following code defines an API that includes the following HTTP endpoints: `ANY /`, `GET /books`, `POST /books`, `GET /books/{book_id}`, `DELETE /books/{book_id}`.

```
api = apigateway.RestApi(self, "books-api")

api.root.add_method("ANY")

books = api.root.add_resource("books")
books.add_method("GET")
books.add_method("POST")

book = books.add_resource("{book_id}")
book.add_method("GET")
book.add_method("DELETE")
```

To give an IAM User or Role permission to invoke a method, use `grantExecute`:

```
# api: apigateway.RestApi
# user: iam.User


method = api.root.add_resource("books").add_method("GET")
method.grant_execute(user)
```

### Breaking up Methods and Resources across Stacks

It is fairly common for REST APIs with a large number of Resources and Methods to hit the CloudFormation limit of 500 resources per stack.

To help with this, Resources and Methods for the same REST API can be re-organized across multiple stacks. A common way to do this is to have a stack per Resource or groups of Resources, but this is not the only possible way. The following example uses sets up two Resources '/pets' and '/books' in separate stacks using nested stacks:

```
from aws_cdk.aws_apigateway import IntegrationResponse, MethodResponse, IntegrationResponse, MethodResponse
from constructs import Construct
from aws_cdk import NestedStackProps
from aws_cdk import App, CfnOutput, NestedStack, Stack
from aws_cdk.aws_apigateway import Method
from aws_cdk.aws_apigateway import Deployment, MockIntegration, PassthroughBehavior, RestApi, Stage

#
# This file showcases how to split up a RestApi's Resources and Methods across nested stacks.
#
# The root stack 'RootStack' first defines a RestApi.
# Two nested stacks BooksStack and PetsStack, create corresponding Resources '/books' and '/pets'.
# They are then deployed to a 'prod' Stage via a third nested stack - DeployStack.
#
# To verify this worked, go to the APIGateway
#

class RootStack(Stack):
    def __init__(self, scope):
        super().__init__(scope, "integ-restapi-import-RootStack")

        rest_api = RestApi(self, "RestApi",
            cloud_watch_role=True,
            deploy=False
        )
        rest_api.root.add_method("ANY")

        pets_stack = PetsStack(self,
            rest_api_id=rest_api.rest_api_id,
            root_resource_id=rest_api.rest_api_root_resource_id
        )
        books_stack = BooksStack(self,
            rest_api_id=rest_api.rest_api_id,
            root_resource_id=rest_api.rest_api_root_resource_id
        )
        DeployStack(self,
            rest_api_id=rest_api.rest_api_id,
            methods=pets_stack.methods.concat(books_stack.methods)
        )

        CfnOutput(self, "PetsURL",
            value=f"https://{restApi.restApiId}.execute-api.{this.region}.amazonaws.com/prod/pets"
        )

        CfnOutput(self, "BooksURL",
            value=f"https://{restApi.restApiId}.execute-api.{this.region}.amazonaws.com/prod/books"
        )

class PetsStack(NestedStack):

    def __init__(self, scope, *, restApiId, rootResourceId, parameters=None, timeout=None, notificationArns=None, removalPolicy=None, description=None, suppressTemplateIndentation=None):
        super().__init__(scope, "integ-restapi-import-PetsStack", restApiId=restApiId, rootResourceId=rootResourceId, parameters=parameters, timeout=timeout, notificationArns=notificationArns, removalPolicy=removalPolicy, description=description, suppressTemplateIndentation=suppressTemplateIndentation)

        api = RestApi.from_rest_api_attributes(self, "RestApi",
            rest_api_id=rest_api_id,
            root_resource_id=root_resource_id
        )

        method = api.root.add_resource("pets").add_method("GET", MockIntegration(
            integration_responses=[IntegrationResponse(
                status_code="200"
            )],
            passthrough_behavior=PassthroughBehavior.NEVER,
            request_templates={
                "application/json": "{ \"statusCode\": 200 }"
            }
        ),
            method_responses=[MethodResponse(status_code="200")]
        )

        self.methods.push(method)

class BooksStack(NestedStack):

    def __init__(self, scope, *, restApiId, rootResourceId, parameters=None, timeout=None, notificationArns=None, removalPolicy=None, description=None, suppressTemplateIndentation=None):
        super().__init__(scope, "integ-restapi-import-BooksStack", restApiId=restApiId, rootResourceId=rootResourceId, parameters=parameters, timeout=timeout, notificationArns=notificationArns, removalPolicy=removalPolicy, description=description, suppressTemplateIndentation=suppressTemplateIndentation)

        api = RestApi.from_rest_api_attributes(self, "RestApi",
            rest_api_id=rest_api_id,
            root_resource_id=root_resource_id
        )

        method = api.root.add_resource("books").add_method("GET", MockIntegration(
            integration_responses=[IntegrationResponse(
                status_code="200"
            )],
            passthrough_behavior=PassthroughBehavior.NEVER,
            request_templates={
                "application/json": "{ \"statusCode\": 200 }"
            }
        ),
            method_responses=[MethodResponse(status_code="200")]
        )

        self.methods.push(method)

class DeployStack(NestedStack):
    def __init__(self, scope, *, restApiId, methods=None, parameters=None, timeout=None, notificationArns=None, removalPolicy=None, description=None, suppressTemplateIndentation=None):
        super().__init__(scope, "integ-restapi-import-DeployStack", restApiId=restApiId, methods=methods, parameters=parameters, timeout=timeout, notificationArns=notificationArns, removalPolicy=removalPolicy, description=description, suppressTemplateIndentation=suppressTemplateIndentation)

        deployment = Deployment(self, "Deployment",
            api=RestApi.from_rest_api_id(self, "RestApi", rest_api_id)
        )
        if methods:
            for method in methods:
                deployment.node.add_dependency(method)
        Stage(self, "Stage", deployment=deployment)

RootStack(App())
```
> **Warning:** In the code above, an API Gateway deployment is created during the initial CDK deployment. However, if there are changes to the resources in subsequent CDK deployments, a new API Gateway deployment is not automatically created. As a result, the latest state of the resources is not reflected. To ensure the latest state of the resources is reflected, a manual deployment of the API Gateway is required after the CDK deployment. See Controlled triggering of deployments for more info.

## AWS Lambda-backed APIs

A very common practice is to use Amazon API Gateway with AWS Lambda as the backend integration. The `LambdaRestApi` construct makes it easy:

The following code defines a REST API that routes all requests to the specified AWS Lambda function:

```
# backend: lambda.Function

apigateway.LambdaRestApi(self, "myapi",
    handler=backend
)
```

You can also supply `proxy: false`, in which case you will have to explicitly define the API model:

```
# backend: lambda.Function

api = apigateway.LambdaRestApi(self, "myapi",
    handler=backend,
    proxy=False
)

items = api.root.add_resource("items")
items.add_method("GET") # GET /items
items.add_method("POST") # POST /items

item = items.add_resource("{item}")
item.add_method("GET") # GET /items/{item}

# the default integration for methods is "handler", but one can
# customize this behavior per method or even a sub path.
item.add_method("DELETE", apigateway.HttpIntegration("http://amazon.com"))
```

Additionally, `integrationOptions` can be supplied to explicitly define options of the Lambda integration:

```
# backend: lambda.Function


api = apigateway.LambdaRestApi(self, "myapi",
    handler=backend,
    integration_options=apigateway.LambdaIntegrationOptions(
        allow_test_invoke=False,
        timeout=Duration.seconds(1)
    )
)
```

## AWS StepFunctions backed APIs

You can use Amazon API Gateway with AWS Step Functions as the backend integration, specifically Synchronous Express Workflows.

The `StepFunctionsRestApi` only supports integration with Synchronous Express state machine. The `StepFunctionsRestApi` construct makes this easy by setting up input, output and error mapping.

The construct sets up an API endpoint and maps the `ANY` HTTP method and any calls to the API endpoint starts an express workflow execution for the underlying state machine.

Invoking the endpoint with any HTTP method (`GET`, `POST`, `PUT`, `DELETE`, ...) in the example below will send the request to the state machine as a new execution. On success, an HTTP code `200` is returned with the execution output as the Response Body.

If the execution fails, an HTTP `500` response is returned with the `error` and `cause` from the execution output as the Response Body. If the request is invalid (ex. bad execution input) HTTP code `400` is returned.

To disable default response models generation use the `useDefaultMethodResponses` property:

```
# machine: stepfunctions.IStateMachine


apigateway.StepFunctionsRestApi(self, "StepFunctionsRestApi",
    state_machine=machine,
    use_default_method_responses=False
)
```

The response from the invocation contains only the `output` field from the StartSyncExecution API. In case of failures, the fields `error` and `cause` are returned as part of the response. Other metadata such as billing details, AWS account ID and resource ARNs are not returned in the API response.

By default, a `prod` stage is provisioned.

In order to reduce the payload size sent to AWS Step Functions, `headers` are not forwarded to the Step Functions execution input. It is possible to choose whether `headers`, `requestContext`, `path`, `querystring`, and `authorizer` are included or not. By default, `headers` are excluded in all requests.

More details about AWS Step Functions payload limit can be found at https://docs.aws.amazon.com/step-functions/latest/dg/limits-overview.html#service-limits-task-executions.

The following code defines a REST API that routes all requests to the specified AWS StepFunctions state machine:

```
state_machine_definition = stepfunctions.Pass(self, "PassState")

state_machine = stepfunctions.StateMachine(self, "StateMachine",
    definition=state_machine_definition,
    state_machine_type=stepfunctions.StateMachineType.EXPRESS
)

apigateway.StepFunctionsRestApi(self, "StepFunctionsRestApi",
    deploy=True,
    state_machine=state_machine
)
```

When the REST API endpoint configuration above is invoked using POST, as follows -

```
curl -X POST -d '{ "customerId": 1 }' https://example.com/
```

AWS Step Functions will receive the request body in its input as follows:

```
{
  "body": {
    "customerId": 1
  },
  "path": "/",
  "querystring": {}
}
```

When the endpoint is invoked at path '/users/5' using the HTTP GET method as below:

```
curl -X GET https://example.com/users/5?foo=bar
```

AWS Step Functions will receive the following execution input:

```
{
  "body": {},
  "path": {
     "users": "5"
  },
  "querystring": {
    "foo": "bar"
  }
}
```

Additional information around the request such as the request context, authorizer context, and headers can be included as part of the input forwarded to the state machine. The following example enables headers to be included in the input but not query string.

```
apigateway.StepFunctionsRestApi(self, "StepFunctionsRestApi",
    state_machine=machine,
    headers=True,
    path=False,
    querystring=False,
    authorizer=False,
    request_context=apigateway.RequestContext(
        caller=True,
        user=True
    )
)
```

In such a case, when the endpoint is invoked as below:

```
curl -X GET https://example.com/
```

AWS Step Functions will receive the following execution input:

```
{
  "headers": {
    "Accept": "...",
    "CloudFront-Forwarded-Proto": "...",
  },
  "requestContext": {
     "accountId": "...",
     "apiKey": "...",
  },
  "body": {}
}
```

## Integration Targets

Methods are associated with backend integrations, which are invoked when this method is called. API Gateway supports the following integrations:

- `MockIntegration` - can be used to test APIs. This is the default integration if one is not specified.
- `AwsIntegration` - can be used to invoke arbitrary AWS service APIs.
- `HttpIntegration` - can be used to invoke HTTP endpoints.
- `LambdaIntegration` - can be used to invoke an AWS Lambda function.
- `SagemakerIntegration` - can be used to invoke Sagemaker Endpoints.

The following example shows how to integrate the `GET /book/{book_id}` method to an AWS Lambda function:

```
# get_book_handler: lambda.Function
# book: apigateway.Resource


get_book_integration = apigateway.LambdaIntegration(get_book_handler)
book.add_method("GET", get_book_integration)
```

Integration options can be optionally be specified:

```
# get_book_handler: lambda.Function
# get_book_integration: apigateway.LambdaIntegration


get_book_integration = apigateway.LambdaIntegration(get_book_handler,
    content_handling=apigateway.ContentHandling.CONVERT_TO_TEXT,  # convert to base64
    credentials_passthrough=True
)
```

Method options can optionally be specified when adding methods:

```
# book: apigateway.Resource
# get_book_integration: apigateway.LambdaIntegration


book.add_method("GET", get_book_integration,
    authorization_type=apigateway.AuthorizationType.IAM,
    api_key_required=True
)
```

It is possible to also integrate with AWS services in a different region. The following code integrates with Amazon SQS in the `eu-west-1` region.

```
get_message_integration = apigateway.AwsIntegration(
    service="sqs",
    path="queueName",
    region="eu-west-1"
)
```

### Response Streaming

Integrations support response streaming, which allows responses to be streamed back to clients. This is useful for large payloads or when you want to start sending data before the entire response is ready.

To enable response streaming, set `ResponseTransferMode.STREAM` to the `responseTransferMode` option:

```
# handler: lambda.Function

apigateway.LambdaIntegration(handler,
    response_transfer_mode=apigateway.ResponseTransferMode.STREAM
)
```

### Lambda Integration Permissions

By default, creating a `LambdaIntegration` will add a permission for API Gateway to invoke your AWS Lambda function, scoped to the specific method which uses the integration.

If you reuse the same AWS Lambda function for many integrations, the AWS Lambda permission policy size can be exceeded by adding a separate policy statement for each method which invokes the AWS Lambda function. To avoid this, you can opt to scope permissions to any method on the API by setting `scopePermissionToMethod` to `false`, and this will ensure only a single policy statement is added to the AWS Lambda permission policy.

```
# book: apigateway.Resource
# backend: lambda.Function


get_book_integration = apigateway.LambdaIntegration(backend,
    scope_permission_to_method=False
)
create_book_integration = apigateway.LambdaIntegration(backend,
    scope_permission_to_method=False
)

book.add_method("GET", get_book_integration)
book.add_method("POST", create_book_integration)
```

In the above example, a single permission is added, shared by both `getBookIntegration` and `createBookIntegration`.

Note that setting `scopePermissionToMethod` to `false` will always allow test invocations, no matter the value specified for `allowTestInvoke`.

## Usage Plan & API Keys

A usage plan specifies who can access one or more deployed API stages and methods, and the rate at which they can be accessed. The plan uses API keys to identify API clients and meters access to the associated API stages for each key. Usage plans also allow configuring throttling limits and quota limits that are enforced on individual client API keys.

The following example shows how to create and associate a usage plan and an API key:

```
# integration: apigateway.LambdaIntegration


api = apigateway.RestApi(self, "hello-api")

v1 = api.root.add_resource("v1")
echo = v1.add_resource("echo")
echo_method = echo.add_method("GET", integration, api_key_required=True)

plan = api.add_usage_plan("UsagePlan",
    name="Easy",
    throttle=apigateway.ThrottleSettings(
        rate_limit=10,
        burst_limit=2
    )
)

key = api.add_api_key("ApiKey")
plan.add_api_key(key)
```

To associate a plan to a given RestAPI stage:

```
# plan: apigateway.UsagePlan
# api: apigateway.RestApi
# echo_method: apigateway.Method


plan.add_api_stage(
    stage=api.deployment_stage,
    throttle=[apigateway.ThrottlingPerMethod(
        method=echo_method,
        throttle=apigateway.ThrottleSettings(
            rate_limit=10,
            burst_limit=2
        )
    )
    ]
)
```

Existing usage plans can be imported into a CDK app using its id.

```
imported_usage_plan = apigateway.UsagePlan.from_usage_plan_id(self, "imported-usage-plan", "<usage-plan-key-id>")
```

The name and value of the API Key can be specified at creation; if not provided, a name and value will be automatically generated by API Gateway.

```
# api: apigateway.RestApi

key = api.add_api_key("ApiKey",
    api_key_name="myApiKey1",
    value="MyApiKeyThatIsAtLeast20Characters"
)
```

Existing API keys can also be imported into a CDK app using its id.

```
imported_key = apigateway.ApiKey.from_api_key_id(self, "imported-key", "<api-key-id>")
```

The "grant" methods can be used to give prepackaged sets of permissions to other resources. The following code provides read permission to an API key.

```
# imported_key: apigateway.ApiKey
# lambda_fn: lambda.Function

imported_key.grant_read(lambda_fn)
```

### Adding an API Key to an imported RestApi

API Keys are added to ApiGateway Stages, not to the API itself. When you import a RestApi it does not have any information on the Stages that may be associated with it. Since adding an API Key requires a stage, you should instead add the Api Key to the imported Stage.

```
# rest_api: apigateway.IRestApi

imported_stage = apigateway.Stage.from_stage_attributes(self, "imported-stage",
    stage_name="myStageName",
    rest_api=rest_api
)

imported_stage.add_api_key("MyApiKey")
```

### â ï¸ Multiple API Keys

It is possible to specify multiple API keys for a given Usage Plan, by calling `usagePlan.addApiKey()`.

When using multiple API keys, a past bug of the CDK prevents API key associations to a Usage Plan to be deleted. If the CDK app had the feature flag - `@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId` - enabled when the API keys were created, then the app will not be affected by this bug.

If this is not the case, you will need to ensure that the CloudFormation logical ids of the API keys that are not being deleted remain unchanged. Make note of the logical ids of these API keys before removing any, and set it as part of the `addApiKey()` method:

```
# usageplan: apigateway.UsagePlan
# api_key: apigateway.ApiKey


usageplan.add_api_key(api_key,
    override_logical_id="..."
)
```

### Rate Limited API Key

In scenarios where you need to create a single api key and configure rate limiting for it, you can use `RateLimitedApiKey`. This construct lets you specify rate limiting properties which should be applied only to the api key being created. The API key created has the specified rate limits, such as quota and throttles, applied.

The following example shows how to use a rate limited api key :

```
# api: apigateway.RestApi


key = apigateway.RateLimitedApiKey(self, "rate-limited-api-key",
    customer_id="hello-customer",
    api_stages=[apigateway.UsagePlanPerApiStage(stage=api.deployment_stage)],
    quota=apigateway.QuotaSettings(
        limit=10000,
        period=apigateway.Period.MONTH
    )
)
```

## Working with models

When you work with Lambda integrations that are not Proxy integrations, you have to define your models and mappings for the request, response, and integration.

```
hello = lambda_.Function(self, "hello",
    runtime=lambda_.Runtime.NODEJS_LATEST,
    handler="hello.handler",
    code=lambda_.Code.from_asset("lambda")
)

api = apigateway.RestApi(self, "hello-api")
resource = api.root.add_resource("v1")
```

You can define more parameters on the integration to tune the behavior of API Gateway

```
# hello: lambda.Function


integration = apigateway.LambdaIntegration(hello,
    proxy=False,
    request_parameters={
        # You can define mapping parameters from your method to your integration
        # - Destination parameters (the key) are the integration parameters (used in mappings)
        # - Source parameters (the value) are the source request parameters or expressions
        # @see: https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html
        "integration.request.querystring.who": "method.request.querystring.who"
    },
    allow_test_invoke=True,
    request_templates={
        # You can define a mapping that will build a payload for your integration, based
        #  on the integration parameters that you have specified
        # Check: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
        "application/json": JSON.stringify({"action": "sayHello", "poll_id": "$util.escapeJavaScript($input.params('who'))"})
    },
    # This parameter defines the behavior of the engine is no suitable response template is found
    passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
    integration_responses=[apigateway.IntegrationResponse(
        # Successful response from the Lambda function, no filter defined
        #  - the selectionPattern filter only tests the error message
        # We will set the response status code to 200
        status_code="200",
        response_templates={
            # This template takes the "message" result from the Lambda function, and embeds it in a JSON response
            # Check https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html
            "application/json": JSON.stringify({"state": "ok", "greeting": "$util.escapeJavaScript($input.body)"})
        },
        response_parameters={
            # We can map response parameters
            # - Destination parameters (the key) are the response parameters (used in mappings)
            # - Source parameters (the value) are the integration response parameters or expressions
            "method.response.header.Content-Type": "'application/json'",
            "method.response.header.Access-Control-Allow-Origin": "'*'",
            "method.response.header.Access-Control-Allow-Credentials": "'true'"
        }
    ), apigateway.IntegrationResponse(
        # For errors, we check if the error message is not empty, get the error data
        selection_pattern="(\n|.)+",
        # We will set the response status code to 200
        status_code="400",
        response_templates={
            "application/json": JSON.stringify({"state": "error", "message": "$util.escapeJavaScript($input.path('$.errorMessage'))"})
        },
        response_parameters={
            "method.response.header.Content-Type": "'application/json'",
            "method.response.header.Access-Control-Allow-Origin": "'*'",
            "method.response.header.Access-Control-Allow-Credentials": "'true'"
        }
    )
    ]
)
```

You can define models for your responses (and requests)

```
# api: apigateway.RestApi


# We define the JSON Schema for the transformed valid response
response_model = api.add_model("ResponseModel",
    content_type="application/json",
    model_name="ResponseModel",
    schema=apigateway.JsonSchema(
        schema=apigateway.JsonSchemaVersion.DRAFT4,
        title="pollResponse",
        type=apigateway.JsonSchemaType.OBJECT,
        properties={
            "state": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING),
            "greeting": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING)
        }
    )
)

# We define the JSON Schema for the transformed error response
error_response_model = api.add_model("ErrorResponseModel",
    content_type="application/json",
    model_name="ErrorResponseModel",
    schema=apigateway.JsonSchema(
        schema=apigateway.JsonSchemaVersion.DRAFT4,
        title="errorResponse",
        type=apigateway.JsonSchemaType.OBJECT,
        properties={
            "state": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING),
            "message": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING)
        }
    )
)
```

And reference all on your method definition.

```
# integration: apigateway.LambdaIntegration
# resource: apigateway.Resource
# response_model: apigateway.Model
# error_response_model: apigateway.Model


resource.add_method("GET", integration,
    # We can mark the parameters as required
    request_parameters={
        "method.request.querystring.who": True
    },
    # we can set request validator options like below
    request_validator_options=apigateway.RequestValidatorOptions(
        request_validator_name="test-validator",
        validate_request_body=True,
        validate_request_parameters=False
    ),
    method_responses=[apigateway.MethodResponse(
        # Successful response from the integration
        status_code="200",
        # Define what parameters are allowed or not
        response_parameters={
            "method.response.header.Content-Type": True,
            "method.response.header.Access-Control-Allow-Origin": True,
            "method.response.header.Access-Control-Allow-Credentials": True
        },
        # Validate the schema on the response
        response_models={
            "application/json": response_model
        }
    ), apigateway.MethodResponse(
        # Same thing for the error responses
        status_code="400",
        response_parameters={
            "method.response.header.Content-Type": True,
            "method.response.header.Access-Control-Allow-Origin": True,
            "method.response.header.Access-Control-Allow-Credentials": True
        },
        response_models={
            "application/json": error_response_model
        }
    )
    ]
)
```

Specifying `requestValidatorOptions` automatically creates the RequestValidator construct with the given options. However, if you have your RequestValidator already initialized or imported, use the `requestValidator` option instead.

If you want to use `requestValidatorOptions` in multiple `addMethod()` calls then you need to set the `@aws-cdk/aws-apigateway:requestValidatorUniqueId` feature flag. When this feature flag is set, each `RequestValidator` will have a unique generated id.
> **Note** if you enable this feature flag when you have already used `addMethod()` with `requestValidatorOptions` the Logical Id of the resource will change causing the resource to be replaced.

```
# integration: apigateway.LambdaIntegration
# resource: apigateway.Resource
# response_model: apigateway.Model
# error_response_model: apigateway.Model


resource.node.set_context("@aws-cdk/aws-apigateway:requestValidatorUniqueId", True)

resource.add_method("GET", integration,
    # we can set request validator options like below
    request_validator_options=apigateway.RequestValidatorOptions(
        request_validator_name="test-validator",
        validate_request_body=True,
        validate_request_parameters=False
    )
)

resource.add_method("POST", integration,
    # we can set request validator options like below
    request_validator_options=apigateway.RequestValidatorOptions(
        request_validator_name="test-validator2",
        validate_request_body=True,
        validate_request_parameters=False
    )
)
```

## Default Integration and Method Options

The `defaultIntegration` and `defaultMethodOptions` properties can be used to configure a default integration at any resource level. These options will be used when defining method under this resource (recursively) with undefined integration or options.
> If not defined, the default integration is `MockIntegration`. See reference documentation for default method options.

The following example defines the `booksBackend` integration as a default integration. This means that all API methods that do not explicitly define an integration will be routed to this AWS Lambda function.

```
# books_backend: apigateway.LambdaIntegration

api = apigateway.RestApi(self, "books",
    default_integration=books_backend
)

books = api.root.add_resource("books")
books.add_method("GET") # integrated with `booksBackend`
books.add_method("POST") # integrated with `booksBackend`

book = books.add_resource("{book_id}")
book.add_method("GET")
```

A Method can be configured with authorization scopes. Authorization scopes are used in conjunction with an authorizer that uses Amazon Cognito user pools. Read more about authorization scopes here.

Authorization scopes for a Method can be configured using the `authorizationScopes` property as shown below -

```
# books: apigateway.Resource


books.add_method("GET", apigateway.HttpIntegration("http://amazon.com"),
    authorization_type=apigateway.AuthorizationType.COGNITO,
    authorization_scopes=["Scope1", "Scope2"]
)
```

## Proxy Routes

The `addProxy` method can be used to install a greedy `{proxy+}` resource on a path. By default, this also installs an `"ANY"` method:

```
# resource: apigateway.Resource
# handler: lambda.Function

proxy = resource.add_proxy(
    default_integration=apigateway.LambdaIntegration(handler),

    # "false" will require explicitly adding methods on the `proxy` resource
    any_method=True
)
```

## Authorizers

API Gateway supports several different authorization types that can be used for controlling access to your REST APIs.

### IAM-based authorizer

The following CDK code provides 'execute-api' permission to an IAM user, via IAM policies, for the 'GET' method on the `books` resource:

```
# books: apigateway.Resource
# iam_user: iam.User


get_books = books.add_method("GET", apigateway.HttpIntegration("http://amazon.com"),
    authorization_type=apigateway.AuthorizationType.IAM
)

iam_user.attach_inline_policy(iam.Policy(self, "AllowBooks",
    statements=[
        iam.PolicyStatement(
            actions=["execute-api:Invoke"],
            effect=iam.Effect.ALLOW,
            resources=[get_books.method_arn]
        )
    ]
))
```

### Lambda-based token authorizer

API Gateway also allows lambda functions to be used as authorizers.

This module provides support for token-based Lambda authorizers. When a client makes a request to an API's methods configured with such an authorizer, API Gateway calls the Lambda authorizer, which takes the caller's identity as input and returns an IAM policy as output. A token-based Lambda authorizer (also called a token authorizer) receives the caller's identity in a bearer token, such as a JSON Web Token (JWT) or an OAuth token.

API Gateway interacts with the authorizer Lambda function handler by passing input and expecting the output in a specific format. The event object that the handler is called with contains the `authorizationToken` and the `methodArn` from the request to the API Gateway endpoint. The handler is expected to return the `principalId` (i.e. the client identifier) and a `policyDocument` stating what the client is authorizer to perform. See here for a detailed specification on inputs and outputs of the Lambda handler.

The following code attaches a token-based Lambda authorizer to the 'GET' Method of the Book resource:

```
# auth_fn: lambda.Function
# books: apigateway.Resource


auth = apigateway.TokenAuthorizer(self, "booksAuthorizer",
    handler=auth_fn
)

books.add_method("GET", apigateway.HttpIntegration("http://amazon.com"),
    authorizer=auth
)
```

A full working example is shown below.

```
from aws_cdk.aws_apigateway import MethodOptions, CorsOptions, IntegrationResponse, MethodResponse
class MyStack(Stack):
    def __init__(self, scope, id):
        super().__init__(scope, id)

        authorizer_fn = lambda_.Function(self, "MyAuthorizerFunction",
            runtime=lambda_.Runtime.NODEJS_LATEST,
            handler="index.handler",
            code=lambda_.AssetCode.from_asset(path.join(__dirname, "integ.token-authorizer.handler"))
        )

        authorizer = TokenAuthorizer(self, "MyAuthorizer",
            handler=authorizer_fn
        )

        restapi = RestApi(self, "MyRestApi",
            cloud_watch_role=True,
            default_method_options=MethodOptions(
                authorizer=authorizer
            ),
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS
            )
        )

        restapi.root.add_method("ANY", MockIntegration(
            integration_responses=[IntegrationResponse(status_code="200")
            ],
            passthrough_behavior=PassthroughBehavior.NEVER,
            request_templates={
                "application/json": "{ \"statusCode\": 200 }"
            }
        ),
            method_responses=[MethodResponse(status_code="200")
            ]
        )
```

By default, the `TokenAuthorizer` looks for the authorization token in the request header with the key 'Authorization'. This can, however, be modified by changing the `identitySource` property.

Authorizers can also be passed via the `defaultMethodOptions` property within the `RestApi` construct or the `Method` construct. Unless explicitly overridden, the specified defaults will be applied across all `Method`s across the `RestApi` or across all `Resource`s, depending on where the defaults were specified.

### Lambda-based request authorizer

This module provides support for request-based Lambda authorizers. When a client makes a request to an API's methods configured with such an authorizer, API Gateway calls the Lambda authorizer, which takes specified parts of the request, known as identity sources, as input and returns an IAM policy as output. A request-based Lambda authorizer (also called a request authorizer) receives the identity sources in a series of values pulled from the request, from the headers, stage variables, query strings, and the context.

API Gateway interacts with the authorizer Lambda function handler by passing input and expecting the output in a specific format. The event object that the handler is called with contains the body of the request and the `methodArn` from the request to the API Gateway endpoint. The handler is expected to return the `principalId` (i.e. the client identifier) and a `policyDocument` stating what the client is authorizer to perform. See here for a detailed specification on inputs and outputs of the Lambda handler.

The following code attaches a request-based Lambda authorizer to the 'GET' Method of the Book resource:

```
# auth_fn: lambda.Function
# books: apigateway.Resource


auth = apigateway.RequestAuthorizer(self, "booksAuthorizer",
    handler=auth_fn,
    identity_sources=[apigateway.IdentitySource.header("Authorization")]
)

books.add_method("GET", apigateway.HttpIntegration("http://amazon.com"),
    authorizer=auth
)
```

A full working example is shown below.

```
from aws_cdk.aws_apigateway import IntegrationResponse, MethodResponse, IntegrationResponse, MethodResponse
import path as path
import aws_cdk.aws_lambda as lambda_
from aws_cdk import App, Stack
from aws_cdk.aws_apigateway import MockIntegration, PassthroughBehavior, RestApi, RequestAuthorizer, IdentitySource

# Against the RestApi endpoint from the stack output, run
# `curl -s -o /dev/null -w "%{http_code}" <url>` should return 401
# `curl -s -o /dev/null -w "%{http_code}" -H 'Authorization: deny' <url>?allow=yes` should return 403
# `curl -s -o /dev/null -w "%{http_code}" -H 'Authorization: allow' <url>?allow=yes` should return 200

app = App()
stack = Stack(app, "RequestAuthorizerInteg")

authorizer_fn = lambda_.Function(stack, "MyAuthorizerFunction",
    runtime=lambda_.Runtime.NODEJS_LATEST,
    handler="index.handler",
    code=lambda_.AssetCode.from_asset(path.join(__dirname, "integ.request-authorizer.handler"))
)

restapi = RestApi(stack, "MyRestApi", cloud_watch_role=True)

authorizer = RequestAuthorizer(stack, "MyAuthorizer",
    handler=authorizer_fn,
    identity_sources=[IdentitySource.header("Authorization"), IdentitySource.query_string("allow")]
)

second_authorizer = RequestAuthorizer(stack, "MySecondAuthorizer",
    handler=authorizer_fn,
    identity_sources=[IdentitySource.header("Authorization"), IdentitySource.query_string("allow")]
)

restapi.root.add_method("ANY", MockIntegration(
    integration_responses=[IntegrationResponse(status_code="200")
    ],
    passthrough_behavior=PassthroughBehavior.NEVER,
    request_templates={
        "application/json": "{ \"statusCode\": 200 }"
    }
),
    method_responses=[MethodResponse(status_code="200")
    ],
    authorizer=authorizer
)

restapi.root.resource_for_path("auth").add_method("ANY", MockIntegration(
    integration_responses=[IntegrationResponse(status_code="200")
    ],
    passthrough_behavior=PassthroughBehavior.NEVER,
    request_templates={
        "application/json": "{ \"statusCode\": 200 }"
    }
),
    method_responses=[MethodResponse(status_code="200")
    ],
    authorizer=second_authorizer
)
```

By default, the `RequestAuthorizer` does not pass any kind of information from the request. This can, however, be modified by changing the `identitySource` property, and is required when specifying a value for caching.

Authorizers can also be passed via the `defaultMethodOptions` property within the `RestApi` construct or the `Method` construct. Unless explicitly overridden, the specified defaults will be applied across all `Method`s across the `RestApi` or across all `Resource`s, depending on where the defaults were specified.

### Cognito User Pools authorizer

API Gateway also allows Amazon Cognito user pools as authorizer

The following snippet configures a Cognito user pool as an authorizer:

```
# books: apigateway.Resource
user_pool = cognito.UserPool(self, "UserPool")

auth = apigateway.CognitoUserPoolsAuthorizer(self, "booksAuthorizer",
    cognito_user_pools=[user_pool]
)
books.add_method("GET", apigateway.HttpIntegration("http://amazon.com"),
    authorizer=auth,
    authorization_type=apigateway.AuthorizationType.COGNITO
)
```

## Mutual TLS (mTLS)

Mutual TLS can be configured to limit access to your API based by using client certificates instead of (or as an extension of) using authorization headers.

```
# acm: Any


apigateway.DomainName(self, "domain-name",
    domain_name="example.com",
    certificate=acm.Certificate.from_certificate_arn(self, "cert", "arn:aws:acm:us-east-1:1111111:certificate/11-3336f1-44483d-adc7-9cd375c5169d"),
    mtls=apigateway.MTLSConfig(
        bucket=s3.Bucket(self, "bucket"),
        key="truststore.pem",
        version="version"
    )
)
```

Instructions for configuring your trust store can be found here.

## Deployments

By default, the `RestApi` construct will automatically create an API Gateway Deployment and a "prod" Stage which represent the API configuration you defined in your CDK app. This means that when you deploy your app, your API will have open access from the internet via the stage URL.

The URL of your API can be obtained from the attribute `restApi.url`, and is also exported as an `Output` from your stack, so it's printed when you `cdk deploy` your app:

```
$ cdk deploy
...
books.booksapiEndpointE230E8D5 = https://6lyktd4lpk.execute-api.us-east-1.amazonaws.com/prod/
```

To disable this behavior, you can set `{ deploy: false }` when creating your API. This means that the API will not be deployed and a stage will not be created for it. You will need to manually define a `apigateway.Deployment` and `apigateway.Stage` resources.

Use the `deployOptions` property to customize the deployment options of your API.

The following example will configure API Gateway to emit logs and data traces to AWS CloudWatch for all API calls:
> Note: whether or not this is enabled or disabled by default is controlled by the `@aws-cdk/aws-apigateway:disableCloudWatchRole` feature flag. When this feature flag is set to `false` the default behavior will set `cloudWatchRole=true`

This is controlled via the `@aws-cdk/aws-apigateway:disableCloudWatchRole` feature flag and is disabled by default. When enabled (or `@aws-cdk/aws-apigateway:disableCloudWatchRole=false`), an IAM role will be created and associated with API Gateway to allow it to write logs and metrics to AWS CloudWatch.

```
api = apigateway.RestApi(self, "books",
    cloud_watch_role=True,
    deploy_options=apigateway.StageOptions(
        logging_level=apigateway.MethodLoggingLevel.INFO,
        data_trace_enabled=True
    )
)
```
> Note: there can only be a single apigateway.CfnAccount per AWS environment so if you create multiple `RestApi`s with `cloudWatchRole=true` each new `RestApi` will overwrite the `CfnAccount`. It is recommended to set `cloudWatchRole=false` (the default behavior if `@aws-cdk/aws-apigateway:disableCloudWatchRole` is enabled) and only create a single CloudWatch role and account per environment.

You can specify the CloudWatch Role and Account sub-resources removal policy with the `cloudWatchRoleRemovalPolicy` property, which defaults to `RemovalPolicy.RETAIN`. This option requires `cloudWatchRole` to be enabled.

```
import aws_cdk as cdk


api = apigateway.RestApi(self, "books",
    cloud_watch_role=True,
    cloud_watch_role_removal_policy=cdk.RemovalPolicy.DESTROY
)
```

### Deploying to an existing stage

#### Using RestApi

If you want to use an existing stage to deploy your `RestApi`, first set `{ deploy: false }` so the construct doesn't automatically create new `Deployment` and `Stage` resources. Then you can manually define a `apigateway.Deployment` resource and specify the stage name for your existing stage using the `stageName` property.

Note that as long as the deployment's logical ID doesn't change, it will represent the snapshot in time when the resource was created. To ensure your deployment reflects changes to the `RestApi` model, see Controlled triggering of deployments.

```
rest_api = apigateway.RestApi(self, "my-rest-api",
    deploy=False
)

# Use `stageName` to deploy to an existing stage
deployment = apigateway.Deployment(self, "my-deployment",
    api=rest_api,
    stage_name="dev",
    retain_deployments=True
)
```

#### Using SpecRestApi

If you want to use an existing stage to deploy your `SpecRestApi`, first set `{ deploy: false }` so the construct doesn't automatically create new `Deployment` and `Stage` resources. Then you can manually define a `apigateway.Deployment` resource and specify the stage name for your existing stage using the `stageName` property.

To automatically create a new deployment that reflects the latest API changes, you can use the `addToLogicalId()` method and pass in your OpenAPI definition.

```
my_api_definition = apigateway.ApiDefinition.from_asset("path-to-file.json")
spec_rest_api = apigateway.SpecRestApi(self, "my-specrest-api",
    deploy=False,
    api_definition=my_api_definition
)

# Use `stageName` to deploy to an existing stage
deployment = apigateway.Deployment(self, "my-deployment",
    api=spec_rest_api,
    stage_name="dev",
    retain_deployments=True
)

# Trigger a new deployment on OpenAPI definition updates
deployment.add_to_logical_id(my_api_definition)
```
> Note: If the `stageName` property is set but a stage with the corresponding name does not exist, a new stage resource will be created with the provided stage name.
> Note: If you update the `stageName` property, you should be triggering a new deployment (i.e. with an updated logical ID and API changes). Otherwise, an error will occur during deployment.

### Controlled triggering of deployments

By default, the `RestApi` construct deploys changes immediately. If you want to control when deployments happen, set `{ deploy: false }` and create a `Deployment` construct yourself. Add a revision counter to the construct ID, and update it in your source code whenever you want to trigger a new deployment:

```
rest_api = apigateway.RestApi(self, "my-api",
    deploy=False
)

deployment_revision = 5 # Bump this counter to trigger a new deployment
apigateway.Deployment(self, f"Deployment{deploymentRevision}",
    api=rest_api
)
```

### Deep dive: Invalidation of deployments

API Gateway deployments are an immutable snapshot of the API. This means that we want to automatically create a new deployment resource every time the API model defined in our CDK app changes.

In order to achieve that, the AWS CloudFormation logical ID of the `AWS::ApiGateway::Deployment` resource is dynamically calculated by hashing the API configuration (resources, methods). This means that when the configuration changes (i.e. a resource or method are added, configuration is changed), a new logical ID will be assigned to the deployment resource. This will cause CloudFormation to create a new deployment resource.

By default, old deployments are *deleted*. You can set `retainDeployments: true` to allow users revert the stage to an old deployment manually.

In order to also create a new deployment when changes are made to any authorizer attached to the API, the `@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId` feature flag can be enabled. This can be set in the `cdk.json` file.

```
{
  "context": {
    "@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId": true
  }
}
```

## Custom Domains

To associate an API with a custom domain, use the `domainName` configuration when you define your API:

```
# acm_certificate_for_example_com: Any


api = apigateway.RestApi(self, "MyDomain",
    domain_name=apigateway.DomainNameOptions(
        domain_name="example.com",
        certificate=acm_certificate_for_example_com
    )
)
```

This will define a `DomainName` resource for you, along with a `BasePathMapping` from the root of the domain to the deployment stage of the API. This is a common set up.

To route domain traffic to an API Gateway API, use Amazon Route 53 to create an alias record. An alias record is a Route 53 extension to DNS. It's similar to a CNAME record, but you can create an alias record both for the root domain, such as `example.com`, and for subdomains, such as `www.example.com`. (You can create CNAME records only for subdomains.)

```
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets

# api: apigateway.RestApi
# hosted_zone_for_example_com: Any


route53.ARecord(self, "CustomDomainAliasRecord",
    zone=hosted_zone_for_example_com,
    target=route53.RecordTarget.from_alias(targets.ApiGateway(api))
)
```

You can also define a `DomainName` resource directly in order to customize the default behavior:

```
# acm_certificate_for_example_com: Any


apigateway.DomainName(self, "custom-domain",
    domain_name="example.com",
    certificate=acm_certificate_for_example_com,
    endpoint_type=apigateway.EndpointType.EDGE,  # default is REGIONAL
    security_policy=apigateway.SecurityPolicy.TLS_1_2
)
```

API Gateway supports both legacy security policies (TLS 1.0, TLS 1.2) and enhanced security policies. Enhanced security policies (those starting with `SecurityPolicy_`) support TLS 1.3 and provide additional options such as post-quantum cryptography. Use enhanced security policies for regulated workloads, advanced governance, or to use post-quantum cryptography. For more details, see the AWS documentation.

When using enhanced security policies, you must specify `endpointAccessMode`. `STRICT` is recommended for production workloads, but `BASIC` may be needed during migration or for certain application architectures:

```
# acm_certificate_for_example_com: Any


# For regional or private APIs with enhanced security policy
apigateway.DomainName(self, "custom-domain-tls13",
    domain_name="example.com",
    certificate=acm_certificate_for_example_com,
    security_policy=apigateway.SecurityPolicy.TLS13_1_3_2025_09,  # TLS 1.3
    endpoint_access_mode=apigateway.EndpointAccessMode.STRICT
)

# For edge-optimized APIs with enhanced security policy
apigateway.DomainName(self, "custom-domain-edge-tls13",
    domain_name="example.com",
    certificate=acm_certificate_for_example_com,
    endpoint_type=apigateway.EndpointType.EDGE,
    security_policy=apigateway.SecurityPolicy.TLS13_2025_EDGE,  # Enhanced security policy for edge
    endpoint_access_mode=apigateway.EndpointAccessMode.STRICT
)
```
> **Note:** Mutual TLS (mTLS) cannot be enabled on a domain name that uses an enhanced security policy.

Once you have a domain, you can map base paths of the domain to APIs. The following example will map the URL <https://example.com/go-to-api1> to the `api1` API and <https://example.com/boom> to the `api2` API.

```
# domain: apigateway.DomainName
# api1: apigateway.RestApi
# api2: apigateway.RestApi


domain.add_base_path_mapping(api1, base_path="go-to-api1")
domain.add_base_path_mapping(api2, base_path="boom")
```

By default, the base path URL will map to the `deploymentStage` of the `RestApi`. You can specify a different API `Stage` to which the base path URL will map to.

```
# domain: apigateway.DomainName
# restapi: apigateway.RestApi


beta_deploy = apigateway.Deployment(self, "beta-deployment",
    api=restapi
)
beta_stage = apigateway.Stage(self, "beta-stage",
    deployment=beta_deploy
)
domain.add_base_path_mapping(restapi, base_path="api/beta", stage=beta_stage)
```

It is possible to create a base path mapping without associating it with a stage by using the `attachToStage` property. When set to `false`, the stage must be included in the URL when invoking the API. For example, <https://example.com/myapi/prod> will invoke the stage named `prod` from the `myapi` base path mapping.

```
# domain: apigateway.DomainName
# api: apigateway.RestApi


domain.add_base_path_mapping(api, base_path="myapi", attach_to_stage=False)
```

If you don't specify `basePath`, all URLs under this domain will be mapped to the API, and you won't be able to map another API to the same domain:

```
# domain: apigateway.DomainName
# api: apigateway.RestApi

domain.add_base_path_mapping(api)
```

This can also be achieved through the `mapping` configuration when defining the domain as demonstrated above.

Base path mappings can also be created with the `BasePathMapping` resource.

```
# api: apigateway.RestApi


domain_name = apigateway.DomainName.from_domain_name_attributes(self, "DomainName",
    domain_name="domainName",
    domain_name_alias_hosted_zone_id="domainNameAliasHostedZoneId",
    domain_name_alias_target="domainNameAliasTarget"
)

apigateway.BasePathMapping(self, "BasePathMapping",
    domain_name=domain_name,
    rest_api=api
)
```

If you wish to setup this domain with an Amazon Route53 alias, use the `targets.ApiGatewayDomain`:

```
# hosted_zone_for_example_com: Any
# domain_name: apigateway.DomainName

import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets


route53.ARecord(self, "CustomDomainAliasRecord",
    zone=hosted_zone_for_example_com,
    target=route53.RecordTarget.from_alias(targets.ApiGatewayDomain(domain_name))
)
```

### Custom Domains with multi-level api mapping

Additional requirements for creating multi-level path mappings for RestApis:

(both are defaults)

- Must use `SecurityPolicy.TLS_1_2` or higher (TLS 1.0 is not supported for multi-level paths)
- DomainNames must be `EndpointType.REGIONAL`

```
# acm_certificate_for_example_com: Any
# rest_api: apigateway.RestApi


apigateway.DomainName(self, "custom-domain",
    domain_name="example.com",
    certificate=acm_certificate_for_example_com,
    mapping=rest_api,
    base_path="orders/v1/api"
)
```

To then add additional mappings to a domain you can use the `addApiMapping` method.

```
# acm_certificate_for_example_com: Any
# rest_api: apigateway.RestApi
# second_rest_api: apigateway.RestApi


domain = apigateway.DomainName(self, "custom-domain",
    domain_name="example.com",
    certificate=acm_certificate_for_example_com,
    mapping=rest_api
)

domain.add_api_mapping(second_rest_api.deployment_stage,
    base_path="orders/v2/api"
)
```

## Access Logging

Access logging creates logs every time an API method is accessed. Access logs can have information on who has accessed the API, how the caller accessed the API and what responses were generated. Access logs are configured on a Stage of the RestApi. Access logs can be expressed in a format of your choosing, and can contain any access details, with a minimum that it must include either 'requestId' or 'extendedRequestId'. The list of variables that can be expressed in the access log can be found here. Read more at Setting Up CloudWatch API Logging in API Gateway

```
# production stage
prod_log_group = logs.LogGroup(self, "PrdLogs")
api = apigateway.RestApi(self, "books",
    deploy_options=apigateway.StageOptions(
        access_log_destination=apigateway.LogGroupLogDestination(prod_log_group),
        access_log_format=apigateway.AccessLogFormat.json_with_standard_fields()
    )
)
deployment = apigateway.Deployment(self, "Deployment", api=api)

# development stage
dev_log_group = logs.LogGroup(self, "DevLogs")
apigateway.Stage(self, "dev",
    deployment=deployment,
    access_log_destination=apigateway.LogGroupLogDestination(dev_log_group),
    access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
        caller=False,
        http_method=True,
        ip=True,
        protocol=True,
        request_time=True,
        resource_path=True,
        response_length=True,
        status=True,
        user=True
    )
)
```

The following code will generate the access log in the CLF format.

```
log_group = logs.LogGroup(self, "ApiGatewayAccessLogs")
api = apigateway.RestApi(self, "books",
    deploy_options=apigateway.StageOptions(
        access_log_destination=apigateway.LogGroupLogDestination(log_group),
        access_log_format=apigateway.AccessLogFormat.clf()
    )
)
```

You can also configure your own access log format by using the `AccessLogFormat.custom()` API. `AccessLogField` provides commonly used fields. The following code configures access log to contain.

```
log_group = logs.LogGroup(self, "ApiGatewayAccessLogs")
apigateway.RestApi(self, "books",
    deploy_options=apigateway.StageOptions(
        access_log_destination=apigateway.LogGroupLogDestination(log_group),
        access_log_format=apigateway.AccessLogFormat.custom(f"""{apigateway.AccessLogField.contextRequestId()} {apigateway.AccessLogField.contextErrorMessage()} {apigateway.AccessLogField.contextErrorMessageString()}
                  {apigateway.AccessLogField.contextAuthorizerError()} {apigateway.AccessLogField.contextAuthorizerIntegrationStatus()}""")
    )
)
```

You can use the `methodOptions` property to configure default method throttling for a stage. The following snippet configures the a stage that accepts 100 requests per minute, allowing burst up to 200 requests per minute.

```
api = apigateway.RestApi(self, "books")
deployment = apigateway.Deployment(self, "my-deployment", api=api)
stage = apigateway.Stage(self, "my-stage",
    deployment=deployment,
    method_options={
        "/*/*": apigateway.MethodDeploymentOptions( # This special path applies to all resource paths and all HTTP methods
            throttling_rate_limit=100,
            throttling_burst_limit=200)
    }
)
```

Configuring `methodOptions` on the `deployOptions` of `RestApi` will set the throttling behaviors on the default stage that is automatically created.

```
api = apigateway.RestApi(self, "books",
    deploy_options=apigateway.StageOptions(
        method_options={
            "/*/*": apigateway.MethodDeploymentOptions( # This special path applies to all resource paths and all HTTP methods
                throttling_rate_limit=100,
                throttling_burst_limit=1000)
        }
    )
)
```

To write access log files to a Firehose delivery stream destination use the `FirehoseLogDestination` class:

```
destination_bucket = s3.Bucket(self, "Bucket")
delivery_stream_role = iam.Role(self, "Role",
    assumed_by=iam.ServicePrincipal("firehose.amazonaws.com")
)

stream = firehose.CfnDeliveryStream(self, "MyStream",
    delivery_stream_name="amazon-apigateway-delivery-stream",
    s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
        bucket_arn=destination_bucket.bucket_arn,
        role_arn=delivery_stream_role.role_arn
    )
)

api = apigateway.RestApi(self, "books",
    deploy_options=apigateway.StageOptions(
        access_log_destination=apigateway.FirehoseLogDestination(stream),
        access_log_format=apigateway.AccessLogFormat.json_with_standard_fields()
    )
)
```

**Note:** The delivery stream name must start with `amazon-apigateway-`.
> Visit Logging API calls to Amazon Data Firehose for more details.

## Cross Origin Resource Sharing (CORS)

Cross-Origin Resource Sharing (CORS) is a mechanism that uses additional HTTP headers to tell browsers to give a web application running at one origin, access to selected resources from a different origin. A web application executes a cross-origin HTTP request when it requests a resource that has a different origin (domain, protocol, or port) from its own.

You can add the CORS preflight OPTIONS HTTP method to any API resource via the `defaultCorsPreflightOptions` option or by calling the `addCorsPreflight` on a specific resource.

The following example will enable CORS for all methods and all origins on all resources of the API:

```
apigateway.RestApi(self, "api",
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=apigateway.Cors.ALL_ORIGINS,
        allow_methods=apigateway.Cors.ALL_METHODS
    )
)
```

The following example will add an OPTIONS method to the `myResource` API resource, which only allows GET and PUT HTTP requests from the origin <https://amazon.com.>

```
# my_resource: apigateway.Resource


my_resource.add_cors_preflight(
    allow_origins=["https://amazon.com"],
    allow_methods=["GET", "PUT"]
)
```

See the `CorsOptions` API reference for a detailed list of supported configuration options.

You can specify defaults this at the resource level, in which case they will be applied to the entire resource sub-tree:

```
# resource: apigateway.Resource


subtree = resource.add_resource("subtree",
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=["https://amazon.com"]
    )
)
```

This means that all resources under `subtree` (inclusive) will have a preflight OPTIONS added to them.

See #906 for a list of CORS features which are not yet supported.

## Endpoint Configuration

API gateway allows you to specify an API Endpoint Type. To define an endpoint type for the API gateway, use `endpointConfiguration` property:

```
api = apigateway.RestApi(self, "api",
    endpoint_configuration=apigateway.EndpointConfiguration(
        types=[apigateway.EndpointType.EDGE]
    )
)
```

You can also configure endpoint IP address type. The default value is `IpAddressType.DUAL_STACK` for private API, and `IpAddressType.IPV4` for regional and edge-optimized API.

```
api = apigateway.RestApi(self, "api",
    endpoint_configuration=apigateway.EndpointConfiguration(
        types=[apigateway.EndpointType.REGIONAL],
        ip_address_type=apigateway.IpAddressType.DUAL_STACK
    )
)
```

**Note**: If creating a private API, the `IPV4` IP address type is not supported.

You can also create an association between your Rest API and a VPC endpoint. By doing so, API Gateway will generate a new Route53 Alias DNS record which you can use to invoke your private APIs. More info can be found here.

Here is an example:

```
# some_endpoint: ec2.IVpcEndpoint


api = apigateway.RestApi(self, "api",
    endpoint_configuration=apigateway.EndpointConfiguration(
        types=[apigateway.EndpointType.PRIVATE],
        vpc_endpoints=[some_endpoint]
    )
)
```

By performing this association, we can invoke the API gateway using the following format:

```
https://{rest-api-id}-{vpce-id}.execute-api.{region}.amazonaws.com/{stage}
```

To restrict access to the API Gateway to only the VPC endpoint, you can use the `grantInvokeFromVpcEndpointsOnly` method to add resource policies to the API Gateway:

```
# api_gw_vpc_endpoint: ec2.IVpcEndpoint


api = apigateway.RestApi(self, "PrivateApi",
    endpoint_configuration=apigateway.EndpointConfiguration(
        types=[apigateway.EndpointType.PRIVATE],
        vpc_endpoints=[api_gw_vpc_endpoint]
    )
)
api.grant_invoke_from_vpc_endpoints_only([api_gw_vpc_endpoint])
```

## Private Integrations

A private integration makes it simple to expose HTTP/HTTPS resources behind an Amazon VPC for access by clients outside of the VPC. The private integration uses an API Gateway resource of `VpcLink` to encapsulate connections between API Gateway and targeted VPC resources. The `VpcLink` is then attached to the `Integration` of a specific API Gateway Method. The following code sets up a private integration with a network load balancer -

```
import aws_cdk.aws_elasticloadbalancingv2 as elbv2


vpc = ec2.Vpc(self, "VPC")
nlb = elbv2.NetworkLoadBalancer(self, "NLB",
    vpc=vpc
)
link = apigateway.VpcLink(self, "link",
    targets=[nlb]
)

integration = apigateway.Integration(
    type=apigateway.IntegrationType.HTTP_PROXY,
    integration_http_method="ANY",
    options=apigateway.IntegrationOptions(
        connection_type=apigateway.ConnectionType.VPC_LINK,
        vpc_link=link
    )
)
```

The uri for the private integration, in the case of a VpcLink, will be set to the DNS name of the VPC Link's NLB. If the VPC Link has multiple NLBs or the VPC Link is imported or the DNS name cannot be determined for any other reason, the user is expected to specify the `uri` property.

Any existing `VpcLink` resource can be imported into the CDK app via the `VpcLink.fromVpcLinkId()`.

```
awesome_link = apigateway.VpcLink.from_vpc_link_id(self, "awesome-vpc-link", "us-east-1_oiuR12Abd")
```

## Gateway response

If the Rest API fails to process an incoming request, it returns to the client an error response without forwarding the request to the integration backend. API Gateway has a set of standard response messages that are sent to the client for each type of error. These error responses can be configured on the Rest API. The list of Gateway responses that can be configured can be found here. Learn more about Gateway Responses.

The following code configures a Gateway Response when the response is 'access denied':

```
api = apigateway.RestApi(self, "books-api")
api.add_gateway_response("test-response",
    type=apigateway.ResponseType.ACCESS_DENIED,
    status_code="500",
    response_headers={
        # Note that values must be enclosed within a pair of single quotes
        "Access-Control-Allow-Origin": "'test.com'",
        "test-key": "'test-value'"
    },
    templates={
        "application/json": "{ \"message\": $context.error.messageString, \"statusCode\": \"488\", \"type\": \"$context.error.responseType\" }"
    }
)
```

## OpenAPI Definition

CDK supports creating a REST API by importing an OpenAPI definition file. It currently supports OpenAPI v2.0 and OpenAPI v3.0 definition files. Read more about Configuring a REST API using OpenAPI.

The following code creates a REST API using an external OpenAPI definition JSON file -

```
# integration: apigateway.Integration


api = apigateway.SpecRestApi(self, "books-api",
    api_definition=apigateway.ApiDefinition.from_asset("path-to-file.json")
)

books_resource = api.root.add_resource("books")
books_resource.add_method("GET", integration)
```

It is possible to use the `addResource()` API to define additional API Gateway Resources.

**Note:** Deployment will fail if a Resource of the same name is already defined in the Open API specification.

**Note:** Any default properties configured, such as `defaultIntegration`, `defaultMethodOptions`, etc. will only be applied to Resources and Methods defined in the CDK, and not the ones defined in the spec. Use the API Gateway extensions to OpenAPI to configure these.

There are a number of limitations in using OpenAPI definitions in API Gateway. Read the Amazon API Gateway important notes for REST APIs for more details.

**Note:** When starting off with an OpenAPI definition using `SpecRestApi`, it is not possible to configure some properties that can be configured directly in the OpenAPI specification file. This is to prevent people duplication of these properties and potential confusion.

However, you can control how API Gateway handles resource updates using the `mode` property. Valid values are:

- `overwrite` - The new API definition replaces the existing one. The existing API identifier remains unchanged.
- `merge` - The new API definition is merged with the existing API.

If you don't specify this property, a default value is chosen:

- For REST APIs created before March 29, 2021, the default is `overwrite`
- For REST APIs created after March 29, 2021, the new API definition takes precedence, but any container types such as endpoint configurations and binary media types are merged with the existing API.

Use the default mode to define top-level RestApi properties in addition to using OpenAPI. Generally, it's preferred to use API Gateway's OpenAPI extensions to model these properties.

```
api = apigateway.SpecRestApi(self, "books-api",
    api_definition=apigateway.ApiDefinition.from_asset("path-to-file.json"),
    mode=apigateway.RestApiMode.MERGE
)
```

`SpecRestApi` also supports binary media types, similar to `RestApi`:

```
api = apigateway.SpecRestApi(self, "books-api",
    api_definition=apigateway.ApiDefinition.from_asset("path-to-file.json"),
    binary_media_types=["image/png", "application/pdf"]
)
```

### Endpoint configuration

By default, `SpecRestApi` will create an edge optimized endpoint.

This can be modified as shown below:

```
# api_definition: apigateway.ApiDefinition


api = apigateway.SpecRestApi(self, "ExampleRestApi",
    api_definition=api_definition,
    endpoint_types=[apigateway.EndpointType.PRIVATE]
)
```

**Note:** For private endpoints you will still need to provide the `x-amazon-apigateway-policy` and `x-amazon-apigateway-endpoint-configuration` in your openApi file.

## Metrics

The API Gateway service sends metrics around the performance of Rest APIs to Amazon CloudWatch. These metrics can be referred to using the metric APIs available on the `RestApi`, `Stage` and `Method` constructs. Note that detailed metrics must be enabled for a stage to use the `Method` metrics. Read more about API Gateway metrics, including enabling detailed metrics. The APIs with the `metric` prefix can be used to get reference to specific metrics for this API. For example:

```
api = apigateway.RestApi(self, "my-api")
stage = api.deployment_stage
method = api.root.add_method("GET")

client_error_api_metric = api.metric_client_error()
server_error_stage_metric = stage.metric_server_error()
latency_method_metric = method.metric_latency(stage)
```

## APIGateway v2

APIGateway v2 APIs are now moved to its own package named `aws-apigatewayv2`. Previously, these APIs were marked deprecated but retained for backwards compatibility. The deprecated usage of APIGateway v2 APIs within this module `aws-apigateway` has now been removed from the codebase.

The reason for the removal of these deprecated Constructs is that CloudFormation team is releasing AWS resources like `AWS::APIGateway::DomainNameV2` and this would cause compatibility issue with the deprecated `CfnDomainNameV2` resource defined in `apigatewayv2.ts` file during the L1 generation.

Move to using `aws-apigatewayv2` to get the latest APIs and updates.

---

This module is part of the AWS Cloud Development Kit project.

## Types

| Name                                             | Kind           | Summary                                                                                                                                                                                                  |
| ------------------------------------------------ | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ApiKey`                                         | Construct (L2) | An API Gateway ApiKey.                                                                                                                                                                                   |
| `Authorizer`                                     | Construct (L2) | Base class for all custom authorizers.                                                                                                                                                                   |
| `BasePathMapping`                                | Construct (L2) | This resource creates a base path that clients who call your API must use in the invocation URL.                                                                                                         |
| `CognitoUserPoolsAuthorizer`                     | Construct (L2) | Cognito user pools based custom authorizer.                                                                                                                                                              |
| `Deployment`                                     | Construct (L2) | A Deployment of a REST API.                                                                                                                                                                              |
| `DomainName`                                     | Construct (L2) |                                                                                                                                                                                                          |
| `GatewayResponse`                                | Construct (L2) | Configure the response received by clients, produced from the API Gateway backend.                                                                                                                       |
| `LambdaRestApi`                                  | Construct (L2) | Defines an API Gateway REST API with AWS Lambda proxy integration.                                                                                                                                       |
| `Method`                                         | Construct (L2) |                                                                                                                                                                                                          |
| `Model`                                          | Construct (L2) |                                                                                                                                                                                                          |
| `ProxyResource`                                  | Construct (L2) | Defines a {proxy+} greedy resource and an ANY method on a route.                                                                                                                                         |
| `RateLimitedApiKey`                              | Construct (L2) | An API Gateway ApiKey, for which a rate limiting configuration can be specified.                                                                                                                         |
| `RequestAuthorizer`                              | Construct (L2) | Request-based lambda authorizer that recognizes the caller's identity via request parameters, such as headers, paths, query strings, stage variables, or context variables.                              |
| `RequestValidator`                               | Construct (L2) |                                                                                                                                                                                                          |
| `Resource`                                       | Construct (L2) |                                                                                                                                                                                                          |
| `ResourceBase`                                   | Construct (L2) |                                                                                                                                                                                                          |
| `RestApi`                                        | Construct (L2) | Represents a REST API in Amazon API Gateway.                                                                                                                                                             |
| `RestApiBase`                                    | Construct (L2) | Base implementation that are common to various implementations of IRestApi.                                                                                                                              |
| `SpecRestApi`                                    | Construct (L2) | Represents a REST API in Amazon API Gateway, created with an OpenAPI specification.                                                                                                                      |
| `Stage`                                          | Construct (L2) |                                                                                                                                                                                                          |
| `StageBase`                                      | Construct (L2) | Base class for an ApiGateway Stage.                                                                                                                                                                      |
| `StepFunctionsRestApi`                           | Construct (L2) | Defines an API Gateway REST API with a Synchrounous Express State Machine as a proxy integration.                                                                                                        |
| `TokenAuthorizer`                                | Construct (L2) | Token based lambda authorizer that recognizes the caller's identity as a bearer token, such as a JSON Web Token (JWT) or an OAuth token.                                                                 |
| `UsagePlan`                                      | Construct (L2) |                                                                                                                                                                                                          |
| `VpcLink`                                        | Construct (L2) | Define a new VPC Link Specifies an API Gateway VPC link for a RestApi to access resources in an Amazon Virtual Private Cloud (VPC).                                                                      |
| `CfnAccount`                                     | Construct (L1) | The `AWS::ApiGateway::Account` resource specifies the IAM role that Amazon API Gateway uses to write API logs to Amazon CloudWatch Logs.                                                                 |
| `CfnApiKey`                                      | Construct (L1) | The `AWS::ApiGateway::ApiKey` resource creates a unique key that you can distribute to clients who are executing API Gateway `Method` resources that require an API key.                                 |
| `CfnAuthorizer`                                  | Construct (L1) | The `AWS::ApiGateway::Authorizer` resource creates an authorization layer that API Gateway activates for methods that have authorization enabled.                                                        |
| `CfnBasePathMapping`                             | Construct (L1) | The `AWS::ApiGateway::BasePathMapping` resource creates a base path that clients who call your API must use in the invocation URL.                                                                       |
| `CfnBasePathMappingV2`                           | Construct (L1) | The `AWS::ApiGateway::BasePathMappingV2` resource creates a base path that clients who call your API must use in the invocation URL.                                                                     |
| `CfnClientCertificate`                           | Construct (L1) | The `AWS::ApiGateway::ClientCertificate` resource creates a client certificate that API Gateway uses to configure client-side SSL authentication for sending requests to the integration endpoint.       |
| `CfnDeployment`                                  | Construct (L1) | The `AWS::ApiGateway::Deployment` resource deploys an API Gateway `RestApi` resource to a stage so that clients can call the API over the internet.                                                      |
| `CfnDocumentationPart`                           | Construct (L1) | The `AWS::ApiGateway::DocumentationPart` resource creates a documentation part for an API.                                                                                                               |
| `CfnDocumentationVersion`                        | Construct (L1) | The `AWS::ApiGateway::DocumentationVersion` resource creates a snapshot of the documentation for an API.                                                                                                 |
| `CfnDomainName`                                  | Construct (L1) | The `AWS::ApiGateway::DomainName` resource specifies a public custom domain name for your API in API Gateway.                                                                                            |
| `CfnDomainNameAccessAssociation`                 | Construct (L1) | The `AWS::ApiGateway::DomainNameAccessAssociation` resource creates a domain name access association between an access association source and a private custom domain name.                              |
| `CfnDomainNameV2`                                | Construct (L1) | The `AWS::ApiGateway::DomainNameV2` resource specifies a custom domain name for your private APIs in API Gateway.                                                                                        |
| `CfnGatewayResponse`                             | Construct (L1) | The `AWS::ApiGateway::GatewayResponse` resource creates a gateway response for your API.                                                                                                                 |
| `CfnMethod`                                      | Construct (L1) | The `AWS::ApiGateway::Method` resource creates API Gateway methods that define the parameters and body that clients must send in their requests.                                                         |
| `CfnModel`                                       | Construct (L1) | The `AWS::ApiGateway::Model` resource defines the structure of a request or response payload for an API method.                                                                                          |
| `CfnRequestValidator`                            | Construct (L1) | The `AWS::ApiGateway::RequestValidator` resource sets up basic validation rules for incoming requests to your API.                                                                                       |
| `CfnResource`                                    | Construct (L1) | The `AWS::ApiGateway::Resource` resource creates a resource in an API.                                                                                                                                   |
| `CfnRestApi`                                     | Construct (L1) | The `AWS::ApiGateway::RestApi` resource creates a REST API.                                                                                                                                              |
| `CfnStage`                                       | Construct (L1) | The `AWS::ApiGateway::Stage` resource creates a stage for a deployment.                                                                                                                                  |
| `CfnUsagePlan`                                   | Construct (L1) | The `AWS::ApiGateway::UsagePlan` resource creates a usage plan for deployed APIs.                                                                                                                        |
| `CfnUsagePlanKey`                                | Construct (L1) | The `AWS::ApiGateway::UsagePlanKey` resource associates an API key with a usage plan.                                                                                                                    |
| `CfnVpcLink`                                     | Construct (L1) | The `AWS::ApiGateway::VpcLink` resource creates an API Gateway VPC link for a REST API to access resources in an Amazon Virtual Private Cloud (VPC).                                                     |
| `AccessLogDestinationConfig`                     | Struct         | Options when binding a log destination to a RestApi Stage.                                                                                                                                               |
| `AccessLogField`                                 | Class          | $context variables that can be used to customize access log pattern.                                                                                                                                     |
| `AccessLogFormat`                                | Class          | factory methods for access log format.                                                                                                                                                                   |
| `AddApiKeyOptions`                               | Struct         | Options to the UsagePlan.addApiKey() method.                                                                                                                                                             |
| `ApiDefinition`                                  | Class          | Represents an OpenAPI definition asset.                                                                                                                                                                  |
| `ApiDefinitionConfig`                            | Struct         | Post-Binding Configuration for a CDK construct.                                                                                                                                                          |
| `ApiDefinitionS3Location`                        | Struct         | S3 location of the API definition file.                                                                                                                                                                  |
| `ApiKeyGrants`                                   | Facade         | Collection of grant methods for a IApiKeyRef.                                                                                                                                                            |
| `ApiKeyOptions`                                  | Struct         | The options for creating an API Key.                                                                                                                                                                     |
| `ApiKeyProps`                                    | Struct         | ApiKey Properties.                                                                                                                                                                                       |
| `ApiKeySourceType`                               | Enum           |                                                                                                                                                                                                          |
| `ApiMappingOptions`                              | Struct         | Options for creating an api mapping.                                                                                                                                                                     |
| `AssetApiDefinition`                             | Class          | OpenAPI specification from a local file.                                                                                                                                                                 |
| `AuthorizationType`                              | Enum           |                                                                                                                                                                                                          |
| `AwsIntegration`                                 | Class          | This type of integration lets an API expose AWS service actions.                                                                                                                                         |
| `AwsIntegrationProps`                            | Struct         |                                                                                                                                                                                                          |
| `BasePathMappingOptions`                         | Struct         |                                                                                                                                                                                                          |
| `BasePathMappingProps`                           | Struct         |                                                                                                                                                                                                          |
| `CfnAccountProps`                                | Struct         | Properties for defining a `CfnAccount`.                                                                                                                                                                  |
| `CfnApiKey.StageKeyProperty`                     | Struct         | `StageKey` is a property of the AWS::ApiGateway::ApiKey resource that specifies the stage to associate with the API key. This association allows only clients with the key to make requests to methods in that stage. |
| `CfnApiKeyProps`                                 | Struct         | Properties for defining a `CfnApiKey`.                                                                                                                                                                   |
| `CfnAuthorizerProps`                             | Struct         | Properties for defining a `CfnAuthorizer`.                                                                                                                                                               |
| `CfnBasePathMappingProps`                        | Struct         | Properties for defining a `CfnBasePathMapping`.                                                                                                                                                          |
| `CfnBasePathMappingV2Props`                      | Struct         | Properties for defining a `CfnBasePathMappingV2`.                                                                                                                                                        |
| `CfnClientCertificateProps`                      | Struct         | Properties for defining a `CfnClientCertificate`.                                                                                                                                                        |
| `CfnDeployment.AccessLogSettingProperty`         | Struct         | The `AccessLogSetting` property type specifies settings for logging access in this stage.                                                                                                                |
| `CfnDeployment.CanarySettingProperty`            | Struct         | The `CanarySetting` property type specifies settings for the canary deployment in this stage.                                                                                                            |
| `CfnDeployment.DeploymentCanarySettingsProperty` | Struct         | The `DeploymentCanarySettings` property type specifies settings for the canary deployment.                                                                                                               |
| `CfnDeployment.MethodSettingProperty`            | Struct         | The `MethodSetting` property type configures settings for all methods in a stage.                                                                                                                        |
| `CfnDeployment.StageDescriptionProperty`         | Struct         | `StageDescription` is a property of the AWS::ApiGateway::Deployment resource that configures a deployment stage.                                                                                         |
| `CfnDeploymentProps`                             | Struct         | Properties for defining a `CfnDeployment`.                                                                                                                                                               |
| `CfnDocumentationPart.LocationProperty`          | Struct         | The `Location` property specifies the location of the Amazon API Gateway API entity that the documentation applies to.                                                                                   |
| `CfnDocumentationPartProps`                      | Struct         | Properties for defining a `CfnDocumentationPart`.                                                                                                                                                        |
| `CfnDocumentationVersionProps`                   | Struct         | Properties for defining a `CfnDocumentationVersion`.                                                                                                                                                     |
| `CfnDomainName.EndpointConfigurationProperty`    | Struct         | The `EndpointConfiguration` property type specifies the endpoint types and IP address types of an Amazon API Gateway domain name.                                                                        |
| `CfnDomainName.MutualTlsAuthenticationProperty`  | Struct         | The mutual TLS authentication configuration for a custom domain name.                                                                                                                                    |
| `CfnDomainNameAccessAssociationProps`            | Struct         | Properties for defining a `CfnDomainNameAccessAssociation`.                                                                                                                                              |
| `CfnDomainNameProps`                             | Struct         | Properties for defining a `CfnDomainName`.                                                                                                                                                               |
| `CfnDomainNameV2.EndpointConfigurationProperty`  | Struct         | The endpoint configuration to indicate the types of endpoints an API (RestApi) or its custom domain name (DomainName) has and the IP address types that can invoke it.                                   |
| `CfnDomainNameV2Props`                           | Struct         | Properties for defining a `CfnDomainNameV2`.                                                                                                                                                             |
| `CfnGatewayResponseProps`                        | Struct         | Properties for defining a `CfnGatewayResponse`.                                                                                                                                                          |
| `CfnMethod.IntegrationProperty`                  | Struct         | `Integration` is a property of the AWS::ApiGateway::Method resource that specifies information about the target backend that a method calls.                                                             |
| `CfnMethod.IntegrationResponseProperty`          | Struct         | `IntegrationResponse` is a property of the Amazon API Gateway Method Integration property type that specifies the response that API Gateway sends after a method's backend finishes processing a request. |
| `CfnMethod.MethodResponseProperty`               | Struct         | Represents a method response of a given HTTP status code returned to the client.                                                                                                                         |
| `CfnMethodProps`                                 | Struct         | Properties for defining a `CfnMethod`.                                                                                                                                                                   |
| `CfnModelProps`                                  | Struct         | Properties for defining a `CfnModel`.                                                                                                                                                                    |
| `CfnRequestValidatorProps`                       | Struct         | Properties for defining a `CfnRequestValidator`.                                                                                                                                                         |
| `CfnResourceProps`                               | Struct         | Properties for defining a `CfnResource`.                                                                                                                                                                 |
| `CfnRestApi.EndpointConfigurationProperty`       | Struct         | The `EndpointConfiguration` property type specifies the endpoint types and IP address types of a REST API.                                                                                               |
| `CfnRestApi.S3LocationProperty`                  | Struct         | `S3Location` is a property of the AWS::ApiGateway::RestApi resource that specifies the Amazon S3 location of a OpenAPI (formerly Swagger) file that defines a set of RESTful APIs in JSON or YAML.       |
| `CfnRestApiProps`                                | Struct         | Properties for defining a `CfnRestApi`.                                                                                                                                                                  |
| `CfnStage.AccessLogSettingProperty`              | Struct         | The `AccessLogSetting` property type specifies settings for logging access in this stage.                                                                                                                |
| `CfnStage.CanarySettingProperty`                 | Struct         | Configuration settings of a canary deployment.                                                                                                                                                           |
| `CfnStage.MethodSettingProperty`                 | Struct         | The `MethodSetting` property type configures settings for all methods in a stage.                                                                                                                        |
| `CfnStageProps`                                  | Struct         | Properties for defining a `CfnStage`.                                                                                                                                                                    |
| `CfnUsagePlan.ApiStageProperty`                  | Struct         | API stage name of the associated API stage in a usage plan.                                                                                                                                              |
| `CfnUsagePlan.QuotaSettingsProperty`             | Struct         | `QuotaSettings` is a property of the AWS::ApiGateway::UsagePlan resource that specifies a target for the maximum number of requests users can make to your REST APIs.                                    |
| `CfnUsagePlan.ThrottleSettingsProperty`          | Struct         | `ThrottleSettings` is a property of the AWS::ApiGateway::UsagePlan resource that specifies the overall request rate (average requests per second) and burst capacity when users call your REST APIs.     |
| `CfnUsagePlanKeyProps`                           | Struct         | Properties for defining a `CfnUsagePlanKey`.                                                                                                                                                             |
| `CfnUsagePlanProps`                              | Struct         | Properties for defining a `CfnUsagePlan`.                                                                                                                                                                |
| `CfnVpcLinkProps`                                | Struct         | Properties for defining a `CfnVpcLink`.                                                                                                                                                                  |
| `CognitoUserPoolsAuthorizerProps`                | Struct         | Properties for CognitoUserPoolsAuthorizer.                                                                                                                                                               |
| `ConnectionType`                                 | Enum           |                                                                                                                                                                                                          |
| `ContentHandling`                                | Enum           |                                                                                                                                                                                                          |
| `Cors`                                           | Class          |                                                                                                                                                                                                          |
| `CorsOptions`                                    | Struct         |                                                                                                                                                                                                          |
| `DeploymentProps`                                | Struct         |                                                                                                                                                                                                          |
| `DomainNameAttributes`                           | Struct         |                                                                                                                                                                                                          |
| `DomainNameOptions`                              | Struct         |                                                                                                                                                                                                          |
| `DomainNameProps`                                | Struct         |                                                                                                                                                                                                          |
| `EndpointAccessMode`                             | Enum           | The endpoint access mode for the domain name.                                                                                                                                                            |
| `EndpointConfiguration`                          | Struct         | The endpoint configuration of a REST API, including VPCs and endpoint types.                                                                                                                             |
| `EndpointType`                                   | Enum           |                                                                                                                                                                                                          |
| `FirehoseLogDestination`                         | Class          | Use a Firehose delivery stream as a custom access log destination for API Gateway.                                                                                                                       |
| `GatewayResponseOptions`                         | Struct         | Options to add gateway response.                                                                                                                                                                         |
| `GatewayResponseProps`                           | Struct         | Properties for a new gateway response.                                                                                                                                                                   |
| `HttpIntegration`                                | Class          | You can integrate an API method with an HTTP endpoint using the HTTP proxy integration or the HTTP custom integration,.                                                                                  |
| `HttpIntegrationProps`                           | Struct         |                                                                                                                                                                                                          |
| `IAccessLogDestination`                          | Interface      | Access log destination for a RestApi Stage.                                                                                                                                                              |
| `IApiKey`                                        | Interface      | API keys are alphanumeric string values that you distribute to app developer customers to grant access to your API.                                                                                      |
| `IAuthorizer`                                    | Interface      | Represents an API Gateway authorizer.                                                                                                                                                                    |
| `IdentitySource`                                 | Class          | Represents an identity source.                                                                                                                                                                           |
| `IDomainName`                                    | Interface      |                                                                                                                                                                                                          |
| `IGatewayResponse`                               | Interface      | Represents gateway response resource.                                                                                                                                                                    |
| `IModel`                                         | Interface      |                                                                                                                                                                                                          |
| `InlineApiDefinition`                            | Class          | OpenAPI specification from an inline JSON object.                                                                                                                                                        |
| `Integration`                                    | Class          | Base class for backend integrations for an API Gateway method.                                                                                                                                           |
| `IntegrationConfig`                              | Struct         | Result of binding an Integration to a Method.                                                                                                                                                            |
| `IntegrationOptions`                             | Struct         |                                                                                                                                                                                                          |
| `IntegrationProps`                               | Struct         |                                                                                                                                                                                                          |
| `IntegrationResponse`                            | Struct         |                                                                                                                                                                                                          |
| `IntegrationType`                                | Enum           |                                                                                                                                                                                                          |
| `IpAddressType`                                  | Enum           | Supported IP Address Types.                                                                                                                                                                              |
| `IRequestValidator`                              | Interface      |                                                                                                                                                                                                          |
| `IResource`                                      | Interface      |                                                                                                                                                                                                          |
| `IRestApi`                                       | Interface      |                                                                                                                                                                                                          |
| `IStage`                                         | Interface      | Represents an APIGateway Stage.                                                                                                                                                                          |
| `IUsagePlan`                                     | Interface      | A UsagePlan, either managed by this CDK app, or imported.                                                                                                                                                |
| `IVpcLink`                                       | Interface      | Represents an API Gateway VpcLink.                                                                                                                                                                       |
| `JsonSchema`                                     | Struct         | Represents a JSON schema definition of the structure of a REST API model.                                                                                                                                |
| `JsonSchemaType`                                 | Enum           |                                                                                                                                                                                                          |
| `JsonSchemaVersion`                              | Enum           |                                                                                                                                                                                                          |
| `JsonWithStandardFieldProps`                     | Struct         | Properties for controlling items output in JSON standard format.                                                                                                                                         |
| `LambdaAuthorizerProps`                          | Struct         | Base properties for all lambda authorizers.                                                                                                                                                              |
| `LambdaIntegration`                              | Class          | Integrates an AWS Lambda function to an API Gateway method.                                                                                                                                              |
| `LambdaIntegrationOptions`                       | Struct         |                                                                                                                                                                                                          |
| `LambdaRestApiProps`                             | Struct         |                                                                                                                                                                                                          |
| `LogGroupLogDestination`                         | Class          | Use CloudWatch Logs as a custom access log destination for API Gateway.                                                                                                                                  |
| `MethodDeploymentOptions`                        | Struct         |                                                                                                                                                                                                          |
| `MethodLoggingLevel`                             | Enum           |                                                                                                                                                                                                          |
| `MethodOptions`                                  | Struct         |                                                                                                                                                                                                          |
| `MethodProps`                                    | Struct         |                                                                                                                                                                                                          |
| `MethodResponse`                                 | Struct         |                                                                                                                                                                                                          |
| `MockIntegration`                                | Class          | This type of integration lets API Gateway return a response without sending the request further to the backend.                                                                                          |
| `ModelOptions`                                   | Struct         |                                                                                                                                                                                                          |
| `ModelProps`                                     | Struct         |                                                                                                                                                                                                          |
| `MTLSConfig`                                     | Struct         | The mTLS authentication configuration for a custom domain name.                                                                                                                                          |
| `PassthroughBehavior`                            | Enum           |                                                                                                                                                                                                          |
| `Period`                                         | Enum           | Time period for which quota settings apply.                                                                                                                                                              |
| `ProxyResourceOptions`                           | Struct         |                                                                                                                                                                                                          |
| `ProxyResourceProps`                             | Struct         |                                                                                                                                                                                                          |
| `QuotaSettings`                                  | Struct         | Specifies the maximum number of requests that clients can make to API Gateway APIs.                                                                                                                      |
| `RateLimitedApiKeyProps`                         | Struct         | RateLimitedApiKey properties.                                                                                                                                                                            |
| `RequestAuthorizerProps`                         | Struct         | Properties for RequestAuthorizer.                                                                                                                                                                        |
| `RequestContext`                                 | Struct         | Configure what must be included in the `requestContext`.                                                                                                                                                 |
| `RequestValidatorOptions`                        | Struct         |                                                                                                                                                                                                          |
| `RequestValidatorProps`                          | Struct         |                                                                                                                                                                                                          |
| `ResourceAttributes`                             | Struct         | Attributes that can be specified when importing a Resource.                                                                                                                                              |
| `ResourceOptions`                                | Struct         |                                                                                                                                                                                                          |
| `ResourceProps`                                  | Struct         |                                                                                                                                                                                                          |
| `ResponseTransferMode`                           | Enum           | The response transfer mode of the integration.                                                                                                                                                           |
| `ResponseType`                                   | Class          | Supported types of gateway responses.                                                                                                                                                                    |
| `RestApiAttributes`                              | Struct         | Attributes that can be specified when importing a RestApi.                                                                                                                                               |
| `RestApiBaseProps`                               | Struct         | Represents the props that all Rest APIs share.                                                                                                                                                           |
| `RestApiMode`                                    | Enum           | The Mode that determines how API Gateway handles resource updates when importing an OpenAPI definition.                                                                                                  |
| `RestApiProps`                                   | Struct         | Props to create a new instance of RestApi.                                                                                                                                                               |
| `S3ApiDefinition`                                | Class          | OpenAPI specification from an S3 archive.                                                                                                                                                                |
| `SagemakerIntegration`                           | Class          | Integrates an AWS Sagemaker Endpoint to an API Gateway method.                                                                                                                                           |
| `SagemakerIntegrationOptions`                    | Struct         | Options for SageMakerIntegration.                                                                                                                                                                        |
| `SecurityPolicy`                                 | Enum           | The minimum version of the SSL protocol that you want API Gateway to use for HTTPS connections.                                                                                                          |
| `SpecRestApiProps`                               | Struct         | Props to instantiate a new SpecRestApi.                                                                                                                                                                  |
| `StageAttributes`                                | Struct         | The attributes of an imported Stage.                                                                                                                                                                     |
| `StageOptions`                                   | Struct         |                                                                                                                                                                                                          |
| `StageProps`                                     | Struct         |                                                                                                                                                                                                          |
| `StepFunctionsExecutionIntegrationOptions`       | Struct         | Options when configuring Step Functions synchronous integration with Rest API.                                                                                                                           |
| `StepFunctionsIntegration`                       | Class          | Options to integrate with various StepFunction API.                                                                                                                                                      |
| `StepFunctionsRestApiProps`                      | Struct         | Properties for StepFunctionsRestApi.                                                                                                                                                                     |
| `ThrottleSettings`                               | Struct         | Container for defining throttling parameters to API stages or methods.                                                                                                                                   |
| `ThrottlingPerMethod`                            | Struct         | Represents per-method throttling for a resource.                                                                                                                                                         |
| `TokenAuthorizerProps`                           | Struct         | Properties for TokenAuthorizer.                                                                                                                                                                          |
| `UsagePlanPerApiStage`                           | Struct         | Represents the API stages that a usage plan applies to.                                                                                                                                                  |
| `UsagePlanProps`                                 | Struct         |                                                                                                                                                                                                          |
| `VpcLinkProps`                                   | Struct         | Properties for a VpcLink.                                                                                                                                                                                |
