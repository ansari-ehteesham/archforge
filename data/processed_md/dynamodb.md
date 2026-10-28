# Amazon DynamoDB Construct Library
> The DynamoDB construct library has two table constructs - `Table` and `TableV2`. `TableV2` is the preferred construct for all use cases, including creating a single table or a table with multiple `replicas`.

`Table` API documentation

Here is a minimal deployable DynamoDB table using `TableV2`:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)
```

By default, `TableV2` will create a single table in the main deployment region referred to as the primary table. The properties of the primary table are configurable via `TableV2` properties. For example, consider the following DynamoDB table created using the `TableV2` construct defined in a `Stack` being deployed to `us-west-2`:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
        enabled=True
    ),
    table_class=dynamodb.TableClass.STANDARD_INFREQUENT_ACCESS,
    point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
        point_in_time_recovery_enabled=True
    )
)
```

The above `TableV2` definition will result in the provisioning of a single table in `us-west-2` with properties that match the properties set on the `TableV2` instance.

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

## Replicas

The `TableV2` construct can be configured with replica tables. This will enable you to work with your table as a global table. To do this, the `TableV2` construct must be defined in a `Stack` with a defined region. The main deployment region must not be given as a replica because this is created by default with the `TableV2` construct. The following is a minimal example of defining `TableV2` with `replicas`. This `TableV2` definition will provision three copies of the table - one in `us-west-2` (primary deployment region), one in `us-east-1`, and one in `us-east-2`.

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)
```

Alternatively, you can add new `replicas` to an instance of the `TableV2` construct using the `addReplica` method:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1")]
)

global_table.add_replica(region="us-east-2", deletion_protection=True)
```

The following properties are configurable on a per-replica basis, but will be inherited from the `TableV2` properties if not specified:

- contributorInsightsSpecification
- deletionProtection
- pointInTimeRecoverySpecification
- tableClass
- readCapacity (only configurable if the `TableV2` billing mode is `PROVISIONED`)
- globalSecondaryIndexes (only `contributorInsightsSpecification` and `readCapacity`)

The following example shows how to define properties on a per-replica basis:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
        enabled=True
    ),
    point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
        point_in_time_recovery_enabled=True
    ),
    replicas=[dynamodb.ReplicaTableProps(
        region="us-east-1",
        table_class=dynamodb.TableClass.STANDARD_INFREQUENT_ACCESS,
        point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
            point_in_time_recovery_enabled=False
        )
    ), dynamodb.ReplicaTableProps(
        region="us-east-2",
        contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
            enabled=False
        )
    )
    ]
)
```

To obtain an `ITableV2` reference to a specific replica table, call the `replica` method on an instance of the `TableV2` construct and pass the replica region as an argument:

```
import aws_cdk as cdk

# user: iam.User


class FooStack(cdk.Stack):

    def __init__(self, scope, id, *, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        self.global_table = dynamodb.TableV2(self, "GlobalTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
            ]
        )

class BarStack(cdk.Stack):
    def __init__(self, scope, id, *, replicaTable, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, replicaTable=replicaTable, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        # user is given grantWriteData permissions to replica in us-east-1
        replica_table.grant_write_data(user)

app = cdk.App()

foo_stack = FooStack(app, "FooStack", env=cdk.Environment(region="us-west-2"))
bar_stack = BarStack(app, "BarStack",
    replica_table=foo_stack.global_table.replica("us-east-1"),
    env=cdk.Environment(region="us-east-1")
)
```

Note: You can create an instance of the `TableV2` construct with as many `replicas` as needed as long as there is only one replica per region. After table creation you can add or remove `replicas`, but you can only add or remove a single replica in each update.

### Multi-Account Global Tables

Multi-account global tables extend DynamoDB replication across AWS accounts, providing enhanced security, governance, and fault isolation. Each replica resides in a separate AWS account, enabling account-level isolation and alignment with organizational structures.

#### Creating Multi-Account Replicas

For tables defined in the same CDK application, use the `TableV2MultiAccountReplica` construct:

```
import aws_cdk as cdk


app = cdk.App()

# Source table in Account A
source_stack = cdk.Stack(app, "SourceStack",
    env=cdk.Environment(region="us-east-2", account="111111111111")
)

source_table = dynamodb.TableV2(source_stack, "SourceTable",
    table_name="MyMultiAccountTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    global_table_settings_replication_mode=dynamodb.GlobalTableSettingsReplicationMode.ALL
)

# Replica stack in Account B
replica_stack = cdk.Stack(app, "ReplicaStack",
    env=cdk.Environment(region="us-east-1", account="222222222222")
)

# Create replica - permissions are automatically configured
replica = dynamodb.TableV2MultiAccountReplica(replica_stack, "ReplicaTable",
    table_name="MyMultiAccountTable",
    replica_source_table=source_table,
    global_table_settings_replication_mode=dynamodb.GlobalTableSettingsReplicationMode.ALL
)
```

The `TableV2MultiAccountReplica` construct:

- Creates the replica table with the correct source ARN
- Copies the key schema from the source table
- Automatically adds resource policies to both source and replica tables
- Validates that the replica is in a different account and region

**Note**: Permissions are automatically configured when both tables are in the same CDK app. For imported source tables, see "Working with Imported Tables" below.

#### Adding Replicas to Existing Tables

If the source table already exists in AWS, you cannot use automatic cross-stack references. The replica will issue a warning, and you must manually configure permissions:

```
import aws_cdk as cdk


app = cdk.App()

# Source table in Account A
source_stack = cdk.Stack(app, "SourceStack",
    env=cdk.Environment(region="us-east-1", account="111111111111")
)

# Region us-west-2
source_table = dynamodb.TableV2(source_stack, "SourceTable",
    table_name="MyMultiAccountTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    global_table_settings_replication_mode=dynamodb.GlobalTableSettingsReplicationMode.ALL
)
# After replica is deployed, update source stack with the ARN
source_table.grants.multi_account_replication_to("arn:aws:dynamodb:us-east-1:222222222222:table/MyMultiAccountTable")
```

#### Working with Imported Tables

When importing a source table, the replica will issue a warning since it cannot automatically configure permissions on the imported table:

```
import aws_cdk as cdk


app = cdk.App()

replica_stack = cdk.Stack(app, "ReplicaStack",
    env=cdk.Environment(region="us-east-1", account="222222222222")
)

# Import source table
imported_source = dynamodb.TableV2.from_table_arn(replica_stack, "ImportedSource", "arn:aws:dynamodb:us-east-2:111111111111:table/MyMultiAccountTable")

# Create replica - will issue a warning about missing source permissions
replica = dynamodb.TableV2MultiAccountReplica(replica_stack, "ReplicaTable",
    table_name="MyMultiAccountTable",
    replica_source_table=imported_source,
    global_table_settings_replication_mode=dynamodb.GlobalTableSettingsReplicationMode.ALL
)
```

**Warning**: The replica will emit a warning indicating that you must manually configure permissions on the actual source table.

Then configure permissions on the actual source table using the replica ARN as shown in "Adding Replicas to Existing Tables" above.

#### Key Considerations

- Multi-account replicas can only be created using the `TableV2MultiAccountReplica` construct
- Each replica must be in a separate AWS account and region
- Only Multi-Region Eventual Consistency (MREC) is supported
- Resource-based policies must be configured on both source and replica tables before replication begins

## Multi-Region Strong Consistency (MRSC)

By default, DynamoDB global tables provide eventual consistency across regions. For applications requiring strong consistency across regions, you can configure Multi-Region Strong Consistency (MRSC) using the `multiRegionConsistency` property.

MRSC global tables can be configured in two ways:

- **Three replicas**: Deploy your table across three regions within the same region set
- **Two replicas + one witness**: Deploy your table across two regions with a witness region for consensus

### Region Sets

MRSC global tables must be deployed within the same region set. The supported region sets are:

- **US Region set**: `us-east-1`, `us-east-2`, `us-west-2`
- **EU Region set**: `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-central-1`
- **AP Region set**: `ap-northeast-1`, `ap-northeast-2`, `ap-northeast-3`

### Three Replicas Configuration

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

mrsc_table = dynamodb.TableV2(stack, "MRSCTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    multi_region_consistency=dynamodb.MultiRegionConsistency.STRONG,
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)
```

### Two Replicas + Witness Configuration

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

mrsc_table = dynamodb.TableV2(stack, "MRSCTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    multi_region_consistency=dynamodb.MultiRegionConsistency.STRONG,
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1")
    ],
    witness_region="us-east-2"
)
```

### Important Considerations

- **Witness regions** can only be used with `MultiRegionConsistency.STRONG`. Attempting to specify a witness region with eventual consistency will result in a validation error.
- **Region validation**: All regions (primary, replicas, and witness) must be within the same region set.
- **Replica count**: When using a witness region, you must have exactly 2 replicas (including the primary). Without a witness region, you must have exactly 3 replicas.
- **Performance**: MRSC provides strong consistency but may have higher latency compared to eventual consistency.

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html#V2globaltables_HowItWorks.consistency-modes-mrsc

## Billing

The `TableV2` construct can be configured with on-demand or provisioned billing:

- On-demand - The default option. This is a flexible billing option capable of serving requests without capacity planning. The billing mode will be `PAY_PER_REQUEST`.
- You can optionally specify the `maxReadRequestUnits` or `maxWriteRequestUnits` on individual tables and associated global secondary indexes (GSIs). When you configure maximum throughput for an on-demand table, throughput requests that exceed the maximum amount specified will be throttled.
- Provisioned - Specify the `readCapacity` and `writeCapacity` that you need for your application. The billing mode will be `PROVISIONED`. Capacity can be configured using one of the following modes:
  * Fixed - provisioned throughput capacity is configured with a fixed number of I/O operations per second.
  * Autoscaled - provisioned throughput capacity is dynamically adjusted on your behalf in response to actual traffic patterns.

Note: `writeCapacity` can only be configured using autoscaled capacity.

The following example shows how to configure `TableV2` with on-demand billing:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.on_demand()
)
```

The following example shows how to configure `TableV2` with on-demand billing with optional maximum throughput configured:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.on_demand(
        max_read_request_units=100,
        max_write_request_units=115
    )
)
```

When using provisioned billing, you must also specify `readCapacity` and `writeCapacity`. You can choose to configure `readCapacity` with fixed capacity or autoscaled capacity, but `writeCapacity` can only be configured with autoscaled capacity. The following example shows how to configure `TableV2` with provisioned billing:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.provisioned(
        read_capacity=dynamodb.Capacity.fixed(10),
        write_capacity=dynamodb.Capacity.autoscaled(max_capacity=15)
    )
)
```

When using provisioned billing, you can configure the `readCapacity` on a per-replica basis:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.provisioned(
        read_capacity=dynamodb.Capacity.fixed(10),
        write_capacity=dynamodb.Capacity.autoscaled(max_capacity=15)
    ),
    replicas=[dynamodb.ReplicaTableProps(
        region="us-east-1"
    ), dynamodb.ReplicaTableProps(
        region="us-east-2",
        read_capacity=dynamodb.Capacity.autoscaled(max_capacity=20, target_utilization_percent=50)
    )
    ]
)
```

When changing the billing for a table from provisioned to on-demand or from on-demand to provisioned, `seedCapacity` must be configured for each autoscaled resource:

```
global_table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.provisioned(
        read_capacity=dynamodb.Capacity.fixed(10),
        write_capacity=dynamodb.Capacity.autoscaled(max_capacity=10, seed_capacity=20)
    )
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html

## Warm Throughput

Warm throughput refers to the number of read and write operations your DynamoDB table can instantaneously support.

This optional configuration allows you to pre-warm your table or index to handle anticipated throughput, ensuring optimal performance under expected load.

The Warm Throughput configuration settings are automatically replicated across all Global Table replicas.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    warm_throughput=dynamodb.WarmThroughput(
        read_units_per_second=15000,
        write_units_per_second=20000
    )
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html

## Encryption

All user data stored in a DynamoDB table is fully encrypted at rest. When creating an instance of the `TableV2` construct, you can select the following table encryption options:

- AWS owned keys - Default encryption type. The keys are owned by DynamoDB (no additional charge).
- AWS managed keys - The keys are stored in your account and are managed by AWS KMS (AWS KMS charges apply).
- Customer managed keys - The keys are stored in your account and are created, owned, and managed by you. You have full control over the KMS keys (AWS KMS charges apply).

The following is an example of how to configure `TableV2` with encryption using an AWS owned key:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    encryption=dynamodb.TableEncryptionV2.dynamo_owned_key()
)
```

The following is an example of how to configure `TableV2` with encryption using an AWS managed key:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    encryption=dynamodb.TableEncryptionV2.aws_managed_key()
)
```

When configuring `TableV2` with encryption using customer managed keys, you must specify the KMS key for the primary table as the `tableKey`. A map of `replicaKeyArns` must be provided containing each replica region and the associated KMS key ARN:

```
import aws_cdk as cdk
import aws_cdk.aws_kms as kms


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

table_key = kms.Key(stack, "Key")
replica_key_arns = {
    "us-east-1": "arn:aws:kms:us-east-1:123456789012:key/g24efbna-az9b-42ro-m3bp-cq249l94fca6",
    "us-east-2": "arn:aws:kms:us-east-2:123456789012:key/h90bkasj-bs1j-92wp-s2ka-bh857d60bkj8"
}

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    encryption=dynamodb.TableEncryptionV2.customer_managed_key(table_key, replica_key_arns),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)
```

Note: When encryption is configured with customer managed keys, you must have a key already created in each replica region.

Further reading: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#key-mgmt

## Secondary Indexes

Secondary indexes allow efficient access to data with attributes other than the `primaryKey`. DynamoDB supports two types of secondary indexes:

- Global secondary index - An index with partition key(s) and optional sort key(s) that can be different from those on the base table. A `globalSecondaryIndex` is considered "global" because queries on the index can span all of the data in the base table, across all partitions. A `globalSecondaryIndex` is stored in its own partition space away from the base table and scales separately from the base table.

- Local secondary index - An index that has the same `partitionKey` as the base table, but a different `sortKey`. A `localSecondaryIndex` is "local" in the sense that every partition of a `localSecondaryIndex` is scoped to a base table partition that has the same `partitionKey` value.

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SecondaryIndexes.html

### Global Secondary Indexes

`TableV2` can be configured with `globalSecondaryIndexes` by providing them as a `TableV2` property:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    global_secondary_indexes=[dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
    )
    ]
)
```

#### Multi-attribute Keys

Global secondary indexes support multi-attribute keys, allowing you to specify multiple partition keys and/or multiple sort keys. This enables more flexible query patterns for complex data models.

**Key Constraints:**

- You can specify up to **4 partition keys** per global secondary index
- You can specify up to **4 sort keys** per global secondary index
- Use **either** `partitionKey` (singular) **or** `partitionKeys` (plural), but not both
- Use **either** `sortKey` (singular) **or** `sortKeys` (plural), but not both
- At least one partition key must be specified (either `partitionKey` or `partitionKeys`)
- For multiple keys, you **must** use the plural parameters (`partitionKeys` and/or `sortKeys`)
- **Keys cannot be added or modified after index creation** - attempting to add additional keys to an existing index will result in an error

**Example with multi-attribute partition and sort keys:**

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    global_secondary_indexes=[dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="multi-attribute-gsi",
        partition_keys=[dynamodb.Attribute(name="gsi_pk1", type=dynamodb.AttributeType.STRING), dynamodb.Attribute(name="gsi_pk2", type=dynamodb.AttributeType.NUMBER)
        ],
        sort_keys=[dynamodb.Attribute(name="gsi_sk1", type=dynamodb.AttributeType.STRING), dynamodb.Attribute(name="gsi_sk2", type=dynamodb.AttributeType.BINARY)
        ]
    )
    ]
)
```

You can also add a `globalSecondaryIndex` using the `addGlobalSecondaryIndex` method:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    global_secondary_indexes=[dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi1",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
    )
    ]
)

table.add_global_secondary_index(
    index_name="gsi2",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)

# Add a GSI with multi-attribute keys
table.add_global_secondary_index(
    index_name="multi-attribute-gsi2",
    partition_keys=[dynamodb.Attribute(name="multi-attribute_pk1", type=dynamodb.AttributeType.STRING), dynamodb.Attribute(name="multi-attribute_pk2", type=dynamodb.AttributeType.NUMBER)
    ],
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING)
)
```

You can configure `readCapacity` and `writeCapacity` on a `globalSecondaryIndex` when an `TableV2` is configured with provisioned `billing`. If `TableV2` is configured with provisioned `billing` but `readCapacity` or `writeCapacity` are not configured on a `globalSecondaryIndex`, then they will be inherited from the capacity settings specified with the `billing` configuration:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    billing=dynamodb.Billing.provisioned(
        read_capacity=dynamodb.Capacity.fixed(10),
        write_capacity=dynamodb.Capacity.autoscaled(max_capacity=10)
    ),
    global_secondary_indexes=[dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi1",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        read_capacity=dynamodb.Capacity.fixed(15)
    ), dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi2",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        write_capacity=dynamodb.Capacity.autoscaled(min_capacity=5, max_capacity=20)
    )
    ]
)
```

All `globalSecondaryIndexes` for replica tables are inherited from the primary table. You can configure `contributorInsightsSpecification` and `readCapacity` for each `globalSecondaryIndex` on a per-replica basis:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
        enabled=True
    ),
    billing=dynamodb.Billing.provisioned(
        read_capacity=dynamodb.Capacity.fixed(10),
        write_capacity=dynamodb.Capacity.autoscaled(max_capacity=10)
    ),
    # each global secondary index will inherit contributor insights as true
    global_secondary_indexes=[dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi1",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        read_capacity=dynamodb.Capacity.fixed(15)
    ), dynamodb.GlobalSecondaryIndexPropsV2(
        index_name="gsi2",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        write_capacity=dynamodb.Capacity.autoscaled(min_capacity=5, max_capacity=20)
    )
    ],
    replicas=[dynamodb.ReplicaTableProps(
        region="us-east-1",
        global_secondary_index_options={
            "gsi1": dynamodb.ReplicaGlobalSecondaryIndexOptions(
                read_capacity=dynamodb.Capacity.autoscaled(min_capacity=1, max_capacity=10)
            )
        }
    ), dynamodb.ReplicaTableProps(
        region="us-east-2",
        global_secondary_index_options={
            "gsi2": dynamodb.ReplicaGlobalSecondaryIndexOptions(
                contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
                    enabled=False
                )
            )
        }
    )
    ]
)
```

### Local Secondary Indexes

`TableV2` can only be configured with `localSecondaryIndexes` when a `sortKey` is defined as a `TableV2` property.

You can provide `localSecondaryIndexes` as a `TableV2` property:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER),
    local_secondary_indexes=[dynamodb.LocalSecondaryIndexProps(
        index_name="lsi",
        sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER)
    )
    ]
)
```

Alternatively, you can add a `localSecondaryIndex` using the `addLocalSecondaryIndex` method:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER),
    local_secondary_indexes=[dynamodb.LocalSecondaryIndexProps(
        index_name="lsi1",
        sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER)
    )
    ]
)

table.add_local_secondary_index(
    index_name="lsi2",
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER)
)
```

## Streams

Each DynamoDB table produces an independent stream based on all its writes, regardless of the origination point for those writes. DynamoDB supports two stream types:

- DynamoDB streams - Capture item-level changes in your table, and push the changes to a DynamoDB stream. You then can access the change information through the DynamoDB Streams API.
- Kinesis streams - Amazon Kinesis Data Streams for DynamoDB captures item-level changes in your table, and replicates the changes to a Kinesis data stream. You then can consume and manage the change information from Kinesis.

### DynamoDB Streams

A `dynamoStream` can be configured as a `TableV2` property. If the `TableV2` instance has replica tables, then all replica tables will inherit the `dynamoStream` setting from the primary table. If replicas are configured, but `dynamoStream` is not configured, then the primary table and all replicas will be automatically configured with the `NEW_AND_OLD_IMAGES` stream view type.

```
import aws_cdk as cdk
import aws_cdk.aws_kinesis as kinesis


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(self, "GlobalTable",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    dynamo_stream=dynamodb.StreamViewType.OLD_IMAGE,
    # tables in us-west-2, us-east-1, and us-east-2 all have dynamo stream type of OLD_IMAGES
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html

### Kinesis Streams

A `kinesisStream` can be configured as a `TableV2` property. Replica tables will not inherit the `kinesisStream` configured for the primary table and should added on a per-replica basis.

```
import aws_cdk as cdk
import aws_cdk.aws_kinesis as kinesis


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

stream1 = kinesis.Stream(stack, "Stream1")
stream2 = kinesis.Stream.from_stream_arn(stack, "Stream2", "arn:aws:kinesis:us-east-2:123456789012:stream/my-stream")

global_table = dynamodb.TableV2(self, "GlobalTable",
    partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
    kinesis_stream=stream1,  # for table in us-west-2
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(
        region="us-east-2",
        kinesis_stream=stream2
    )
    ]
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds.html

## Keys

When an instance of the `TableV2` construct is defined, you must define its schema using the `partitionKey` (required) and `sortKey` (optional) properties.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.NUMBER)
)
```

## Contributor Insights

Enabling `contributorInsightSpecification` for `TableV2` will provide information about the most accessed and throttled or throttled only items in a table or `globalSecondaryIndex`. DynamoDB delivers this information to you via CloudWatch Contributor Insights rules, reports, and graphs of report data.

By default, Contributor Insights for DynamoDB monitors all requests, including both the most accessed and most throttled items. To limit the scope to only the most accessed or only the most throttled items, use the optional `mode` parameter.

- To monitor all traffic on a table or index, set `mode` to `ContributorInsightsMode.ACCESSED_AND_THROTTLED_KEYS`.
- To monitor only throttled traffic on a table or index, set `mode` to `ContributorInsightsMode.THROTTLED_KEYS`.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification(
        enabled=True,
        mode=dynamodb.ContributorInsightsMode.ACCESSED_AND_THROTTLED_KEYS
    )
)
```

When you use `Table`, you can enable contributor insights for a table or specific global secondary index by setting `contributorInsightsSpecification` parameter `enabled` to `true`.

```
table = dynamodb.Table(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification( # for a table
        enabled=True,
        mode=dynamodb.ContributorInsightsMode.THROTTLED_KEYS)
)

table.add_global_secondary_index(
    contributor_insights_specification=dynamodb.ContributorInsightsSpecification( # for a specific global secondary index
        enabled=True),
    index_name="gsi",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_HowItWorks.html

## Deletion Protection

`deletionProtection` determines if your DynamoDB table is protected from deletion and is configurable as a `TableV2` property. When enabled, the table cannot be deleted by any user or process.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    deletion_protection=True
)
```

You can also specify the `removalPolicy` as a property of the `TableV2` construct. This property allows you to control what happens to tables provisioned using `TableV2` during `stack` deletion. By default, the `removalPolicy` is `RETAIN` which will cause all tables provisioned using `TableV2` to be retained in the account, but orphaned from the `stack` they were created in. You can also set the `removalPolicy` to `DESTROY` which will delete all tables created using `TableV2` during `stack` deletion:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    # applies to all replicas, i.e., us-west-2, us-east-1, us-east-2
    removal_policy=cdk.RemovalPolicy.DESTROY,
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)
```

`deletionProtection` is configurable on a per-replica basis. If the `removalPolicy` is set to `DESTROY`, but some `replicas` have `deletionProtection` enabled, then only the `replicas` without `deletionProtection` will be deleted during `stack` deletion:

```
import aws_cdk as cdk


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    removal_policy=cdk.RemovalPolicy.DESTROY,
    deletion_protection=True,
    # only the replica in us-east-1 will be deleted during stack deletion
    replicas=[dynamodb.ReplicaTableProps(
        region="us-east-1",
        deletion_protection=False
    ), dynamodb.ReplicaTableProps(
        region="us-east-2",
        deletion_protection=True
    )
    ]
)
```

## Point-in-Time Recovery

`pointInTimeRecoverySpecifcation` provides automatic backups of your DynamoDB table data which helps protect your tables from accidental write or delete operations.

You can also choose to set `recoveryPeriodInDays` to a value between `1` and `35` which dictates how many days of recoverable data is stored. If no value is provided, the recovery period defaults to `35` days.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
        point_in_time_recovery_enabled=True,
        recovery_period_in_days=4
    )
)
```

## Table Class

You can configure a `TableV2` instance with table classes:

- STANDARD - the default mode, and is recommended for the vast majority of workloads.
- STANDARD_INFREQUENT_ACCESS - optimized for tables where storage is the dominant cost.

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    table_class=dynamodb.TableClass.STANDARD_INFREQUENT_ACCESS
)
```

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.TableClasses.html

## Tags

You can add tags to a `TableV2` in several ways. By adding the tags to the construct itself it will apply the tags to the primary table.

```
from aws_cdk import CfnTag
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    tags=[CfnTag(key="primaryTableTagKey", value="primaryTableTagValue")]
)
```

You can also add tags to replica tables by specifying them within the replica table properties.

```
from aws_cdk import CfnTag
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    replicas=[dynamodb.ReplicaTableProps(
        region="us-west-1",
        tags=[CfnTag(key="replicaTableTagKey", value="replicaTableTagValue")]
    )
    ]
)
```

## Referencing Existing Global Tables

To reference an existing DynamoDB table in your CDK application, use the `TableV2.fromTableName`, `TableV2.fromTableArn`, or `TableV2.fromTableAttributes` factory methods:

```
# user: iam.User


table = dynamodb.TableV2.from_table_arn(self, "ImportedTable", "arn:aws:dynamodb:us-east-1:123456789012:table/my-table")
# now you can call methods on the referenced table
table.grant_read_write_data(user)
```

If you intend to use the `tableStreamArn` (including indirectly, for example by creating an `aws-cdk-lib/aws-lambda-event-sources.DynamoEventSource` on the referenced table), you *must* use the `TableV2.fromTableAttributes` method and the `tableStreamArn` property *must* be populated.

To grant permissions to indexes for a referenced table you can either set `grantIndexPermissions` to `true`, or you can provide the indexes via the `globalIndexes` or `localIndexes` properties. This will enable `grant*` methods to also grant permissions to *all* table indexes.

## Resource Policy

Using `resourcePolicy` you can add a resource policy to a table in the form of a `PolicyDocument`:

```
    // resource policy document
    const policy = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          actions: ['dynamodb:GetItem'],
          principals: [new iam.AccountRootPrincipal()],
          resources: ['*'],
        }),
      ],
    });

    // table with resource policy
    new dynamodb.TableV2(this, 'TableTestV2-1', {
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      removalPolicy: RemovalPolicy.DESTROY,
      resourcePolicy: policy,
    });
```

### Adding Resource Policy Statements Dynamically

You can also add resource policy statements to a table after it's created using the `addToResourcePolicy` method. Following the same pattern as KMS, resource policies use wildcard resources to avoid circular dependencies:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)

# Standard resource policy (recommended approach)
table.add_to_resource_policy(iam.PolicyStatement(
    actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
    principals=[iam.AccountRootPrincipal()],
    resources=["*"]
))

# Allow specific service access
table.add_to_resource_policy(iam.PolicyStatement(
    actions=["dynamodb:Query"],
    principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
    resources=["*"]
))
```

#### Scoped Resource Policies (Advanced)

For scoped resource policies that reference specific table ARNs, you must specify an explicit table name:

```
from aws_cdk import Fn


# Table with explicit name enables scoped resource policies
table = dynamodb.TableV2(self, "Table",
    table_name="my-explicit-table-name",  # Required for scoped resources
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)

# Now you can use scoped resources
table.add_to_resource_policy(iam.PolicyStatement(
    actions=["dynamodb:GetItem"],
    principals=[iam.AccountRootPrincipal()],
    resources=[
        Fn.sub("arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/my-explicit-table-name"),
        Fn.sub("arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/my-explicit-table-name/index/*")
    ]
))
```

**Important Limitations:**

- **Auto-generated table names**: Must use `resources: ['*']` to avoid circular dependencies
- **Explicit table names**: Enable scoped resources but lose CDK's automatic naming benefits
- **CloudFormation constraint**: Resource policies cannot reference the resource they're attached to during creation

TableV2 doesnât support creating a replica and adding a resource-based policy to that replica in the same stack update in Regions other than the Region where you deploy the stack update. To incorporate a resource-based policy into a replica, you'll need to initially deploy the replica without the policy, followed by a subsequent update to include the desired policy.

### Grant Methods and Resource Policies

Grant methods like `grantReadData()`, `grantWriteData()`, and `grantReadWriteData()` automatically add permissions to resource policies when used with same-account principals (like `AccountRootPrincipal`). This happens transparently:

```
# Adds to IAM user's policy (not resource policy)
# user: iam.User
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
)

# Automatically adds to table's resource policy (same account)
table.grant_read_data(iam.AccountRootPrincipal())
table.grant_read_data(user)
```

**How it works:**

- **Same-account principals** (AccountRootPrincipal, AccountPrincipal): Grant adds statement to table's resource policy
- **IAM identities** (User, Role, Group): Grant adds statement to the identity's IAM policy
- **Resource policy statements**: Automatically use wildcard resources (`*`) to avoid circular dependencies

This behavior follows the same pattern as other AWS services like KMS and S3, where grants intelligently choose between resource policies and identity policies based on the principal type.

**To avoid wildcards in resource policies:** If you need scoped resource ARNs instead of wildcards, use `addToResourcePolicy()` directly with an explicit table name instead of grant methods. See the "Scoped Resource Policies (Advanced)" section above for details.

### Stream Resource Policy

You can attach a resource policy to a DynamoDB stream using `streamResourcePolicy`. This applies per-replica, so you can set different policies for the primary table and each replica:

```
stream_policy = iam.PolicyDocument(
    statements=[
        iam.PolicyStatement(
            actions=["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"],
            principals=[iam.AccountRootPrincipal()],
            resources=["*"]
        )
    ]
)

dynamodb.TableV2(self, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    stream_resource_policy=stream_policy,
    replicas=[dynamodb.ReplicaTableProps(
        region="us-west-2",
        stream_resource_policy=stream_policy
    )
    ]
)
```

You can also add stream resource policy statements dynamically using `addToStreamResourcePolicy`:

```
table = dynamodb.TableV2(self, "Table",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
)

table.add_to_stream_resource_policy(iam.PolicyStatement(
    actions=["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"],
    principals=[iam.AccountRootPrincipal()],
    resources=["*"]
))
```

Note: `addToStreamResourcePolicy` applies to the primary table's stream only. To set a stream resource policy on a replica, pass `streamResourcePolicy` in the replica props.

## Grants

Using any of the `grant*` methods on an instance of the `TableV2` construct will only apply to the primary table, its indexes, and any associated `encryptionKey`. As an example, `grantReadData` used below will only apply the table in `us-west-2`:

```
import aws_cdk as cdk
import aws_cdk.aws_kms as kms

# user: iam.User


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

table_key = kms.Key(stack, "Key")
replica_key_arns = {
    "us-east-1": "arn:aws:kms:us-east-1:123456789012:key/g24efbna-az9b-42ro-m3bp-cq249l94fca6",
    "us-east-2": "arn:aws:kms:us-east-2:123456789012:key/g24efbna-az9b-42ro-m3bp-cq249l94fca6"
}

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    encryption=dynamodb.TableEncryptionV2.customer_managed_key(table_key, replica_key_arns),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)

# grantReadData only applies to the table in us-west-2 and the tableKey
global_table.grant_read_data(user)
```

The `replica` method can be used to grant to a specific replica table:

```
import aws_cdk as cdk
import aws_cdk.aws_kms as kms

# user: iam.User


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

table_key = kms.Key(stack, "Key")
replica_key_arns = {
    "us-east-1": "arn:aws:kms:us-east-1:123456789012:key/g24efbna-az9b-42ro-m3bp-cq249l94fca6",
    "us-east-2": "arn:aws:kms:us-east-2:123456789012:key/g24efbna-az9b-42ro-m3bp-cq249l94fca6"
}

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    encryption=dynamodb.TableEncryptionV2.customer_managed_key(table_key, replica_key_arns),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)

# grantReadData applies to the table in us-east-2 and the key arn for the key in us-east-2
global_table.replica("us-east-2").grant_read_data(user)
```

## Metrics

You can use `metric*` methods to generate metrics for a table that can be used when configuring an `Alarm` or `Graphs`. The `metric*` methods only apply to the primary table provisioned using the `TableV2` construct. As an example, `metricConsumedReadCapacityUnits` used below is only for the table in `us-west-2`:

```
import aws_cdk as cdk
import aws_cdk.aws_cloudwatch as cloudwatch


app = cdk.App()
stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

global_table = dynamodb.TableV2(stack, "GlobalTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
    ]
)

# metric is only for the table in us-west-2
metric = global_table.metric_consumed_read_capacity_units()

cloudwatch.Alarm(self, "Alarm",
    metric=metric,
    evaluation_periods=1,
    threshold=1
)
```

The `replica` method can be used to generate a metric for a specific replica table:

```
import aws_cdk as cdk
import aws_cdk.aws_cloudwatch as cloudwatch


class FooStack(cdk.Stack):

    def __init__(self, scope, id, *, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        self.global_table = dynamodb.TableV2(self, "GlobalTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
            ]
        )

class BarStack(cdk.Stack):
    def __init__(self, scope, id, *, replicaTable, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, replicaTable=replicaTable, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        # metric is only for the table in us-east-1
        metric = replica_table.metric_consumed_read_capacity_units()

        cloudwatch.Alarm(self, "Alarm",
            metric=metric,
            evaluation_periods=1,
            threshold=1
        )

app = cdk.App()
foo_stack = FooStack(app, "FooStack", env=cdk.Environment(region="us-west-2"))
bar_stack = BarStack(app, "BarStack",
    replica_table=foo_stack.global_table.replica("us-east-1"),
    env=cdk.Environment(region="us-east-1")
)
```

## import from S3 Bucket

You can import data in S3 when creating a Table using the `Table` construct. To import data into DynamoDB, it is required that your data is in a CSV, DynamoDB JSON, or Amazon Ion format within an Amazon S3 bucket. The data may be compressed using ZSTD or GZIP formats, or you may choose to import it without compression. The data source can be a single S3 object or multiple S3 objects sharing a common prefix.

Further reading: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataImport.HowItWorks.html

### use CSV format

The `InputFormat.csv` method accepts `delimiter` and `headerList` options as arguments. If `delimiter` is not specified, `,` is used by default. And if `headerList` is specified, the first line of CSV is treated as data instead of header.

```
import aws_cdk as cdk
import aws_cdk.aws_s3 as s3

# bucket: s3.IBucket


app = cdk.App()
stack = cdk.Stack(app, "Stack")

dynamodb.Table(stack, "Table",
    partition_key=dynamodb.Attribute(
        name="id",
        type=dynamodb.AttributeType.STRING
    ),
    import_source=dynamodb.ImportSourceSpecification(
        compression_type=dynamodb.InputCompressionType.GZIP,
        input_format=dynamodb.InputFormat.csv(
            delimiter=",",
            header_list=["id", "name"]
        ),
        bucket=bucket,
        key_prefix="prefix"
    )
)
```

### use DynamoDB JSON format

Use the `InputFormat.dynamoDBJson()` method to specify the `inputFormat` property. There are currently no options available.

```
import aws_cdk as cdk
import aws_cdk.aws_s3 as s3

# bucket: s3.IBucket


app = cdk.App()
stack = cdk.Stack(app, "Stack")

dynamodb.Table(stack, "Table",
    partition_key=dynamodb.Attribute(
        name="id",
        type=dynamodb.AttributeType.STRING
    ),
    import_source=dynamodb.ImportSourceSpecification(
        compression_type=dynamodb.InputCompressionType.GZIP,
        input_format=dynamodb.InputFormat.dynamo_db_json(),
        bucket=bucket,
        key_prefix="prefix"
    )
)
```

### use Amazon Ion format

Use the `InputFormat.ion()` method to specify the `inputFormat` property. There are currently no options available.

```
import aws_cdk as cdk
import aws_cdk.aws_s3 as s3

# bucket: s3.IBucket


app = cdk.App()
stack = cdk.Stack(app, "Stack")

dynamodb.Table(stack, "Table",
    partition_key=dynamodb.Attribute(
        name="id",
        type=dynamodb.AttributeType.STRING
    ),
    import_source=dynamodb.ImportSourceSpecification(
        compression_type=dynamodb.InputCompressionType.GZIP,
        input_format=dynamodb.InputFormat.ion(),
        bucket=bucket,
        key_prefix="prefix"
    )
)
```

## Types

| Name                                                              | Kind           | Summary                                                                                                                                                                                                  |
| ----------------------------------------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Table`                                                           | Construct (L2) | Provides a DynamoDB table.                                                                                                                                                                               |
| `TableBase`                                                       | Construct (L2) |                                                                                                                                                                                                          |
| `TableBaseV2`                                                     | Construct (L2) | Base class for a DynamoDB table.                                                                                                                                                                         |
| `TableV2`                                                         | Construct (L2) | A DynamoDB Table.                                                                                                                                                                                        |
| `TableV2MultiAccountReplica`                                      | Construct (L2) | A multi-account replica of a DynamoDB table.                                                                                                                                                             |
| `CfnGlobalTable`                                                  | Construct (L1) | The `AWS::DynamoDB::GlobalTable` resource enables you to create and manage a Version 2019.11.21 global table. This resource cannot be used to create or manage a Version 2017.11.29 global table. For more information, see Global tables . |
| `CfnTable`                                                        | Construct (L1) | The `AWS::DynamoDB::Table` resource creates a DynamoDB table. For more information, see CreateTable in the *Amazon DynamoDB API Reference* .                                                             |
| `ApproximateCreationDateTimePrecision`                            | Enum           | The precision associated with the DynamoDB write timestamps that will be replicated to Kinesis.                                                                                                          |
| `Attribute`                                                       | Struct         | Represents an attribute for describing the key schema for the table and indexes.                                                                                                                         |
| `AttributeType`                                                   | Enum           | Data types for attributes within a table.                                                                                                                                                                |
| `AutoscaledCapacityOptions`                                       | Struct         | Options used to configure autoscaled capacity.                                                                                                                                                           |
| `Billing`                                                         | Class          | Represents how capacity is managed and how you are charged for read and write throughput for a DynamoDB table.                                                                                           |
| `BillingMode`                                                     | Enum           | DynamoDB's Read/Write capacity modes.                                                                                                                                                                    |
| `Capacity`                                                        | Class          | Represents the amount of read and write operations supported by a DynamoDB table.                                                                                                                        |
| `CapacityMode`                                                    | Enum           | Capacity modes.                                                                                                                                                                                          |
| `CfnGlobalTable.AttributeDefinitionProperty`                      | Struct         | Represents an attribute for describing the schema for the table and indexes.                                                                                                                             |
| `CfnGlobalTable.CapacityAutoScalingSettingsProperty`              | Struct         | Configures a scalable target and an autoscaling policy for a table or global secondary index's read or write capacity.                                                                                   |
| `CfnGlobalTable.ContributorInsightsSpecificationProperty`         | Struct         | Configures contributor insights settings for a replica or one of its indexes.                                                                                                                            |
| `CfnGlobalTable.GlobalReadProvisionedThroughputSettingsProperty`  | Struct         |                                                                                                                                                                                                          |
| `CfnGlobalTable.GlobalSecondaryIndexProperty`                     | Struct         | Allows you to specify a global secondary index for the global table.                                                                                                                                     |
| `CfnGlobalTable.GlobalTableWitnessProperty`                       | Struct         | The witness Region for the MRSC global table.                                                                                                                                                            |
| `CfnGlobalTable.KeySchemaProperty`                                | Struct         | Represents *a single element* of a key schema.                                                                                                                                                           |
| `CfnGlobalTable.KinesisStreamSpecificationProperty`               | Struct         | The Kinesis Data Streams configuration for the specified global table replica.                                                                                                                           |
| `CfnGlobalTable.LocalSecondaryIndexProperty`                      | Struct         | Represents the properties of a local secondary index.                                                                                                                                                    |
| `CfnGlobalTable.PointInTimeRecoverySpecificationProperty`         | Struct         | Represents the settings used to enable point in time recovery.                                                                                                                                           |
| `CfnGlobalTable.ProjectionProperty`                               | Struct         | Represents attributes that are copied (projected) from the table into an index.                                                                                                                          |
| `CfnGlobalTable.ReadOnDemandThroughputSettingsProperty`           | Struct         | Sets the read request settings for a replica table or a replica global secondary index.                                                                                                                  |
| `CfnGlobalTable.ReadProvisionedThroughputSettingsProperty`        | Struct         | Allows you to specify the read capacity settings for a replica table or a replica global secondary index when the `BillingMode` is set to `PROVISIONED` .                                                |
| `CfnGlobalTable.ReplicaGlobalSecondaryIndexSpecificationProperty` | Struct         | Represents the properties of a global secondary index that can be set on a per-replica basis.                                                                                                            |
| `CfnGlobalTable.ReplicaSpecificationProperty`                     | Struct         | Defines settings specific to a single replica of a global table.                                                                                                                                         |
| `CfnGlobalTable.ReplicaSSESpecificationProperty`                  | Struct         | Allows you to specify a KMS key identifier to be used for server-side encryption.                                                                                                                        |
| `CfnGlobalTable.ReplicaStreamSpecificationProperty`               | Struct         | Represents the DynamoDB Streams configuration for a global table replica.                                                                                                                                |
| `CfnGlobalTable.ResourcePolicyProperty`                           | Struct         | Creates or updates a resource-based policy document that contains the permissions for DynamoDB resources, such as a table, its indexes, and stream.                                                      |
| `CfnGlobalTable.SearchSchemaElementProperty`                      | Struct         |                                                                                                                                                                                                          |
| `CfnGlobalTable.SSESpecificationProperty`                         | Struct         | Represents the settings used to enable server-side encryption.                                                                                                                                           |
| `CfnGlobalTable.StreamSpecificationProperty`                      | Struct         | Represents the DynamoDB Streams configuration for a table in DynamoDB .                                                                                                                                  |
| `CfnGlobalTable.TargetTrackingScalingPolicyConfigurationProperty` | Struct         | Defines a target tracking scaling policy.                                                                                                                                                                |
| `CfnGlobalTable.TimeToLiveSpecificationProperty`                  | Struct         | Represents the settings used to enable or disable Time to Live (TTL) for the specified table.                                                                                                            |
| `CfnGlobalTable.VectorAttributeProperty`                          | Struct         |                                                                                                                                                                                                          |
| `CfnGlobalTable.VectorIndexProperty`                              | Struct         |                                                                                                                                                                                                          |
| `CfnGlobalTable.WarmThroughputProperty`                           | Struct         | Provides visibility into the number of read and write operations your table or secondary index can instantaneously support.                                                                              |
| `CfnGlobalTable.WriteOnDemandThroughputSettingsProperty`          | Struct         | Sets the write request settings for a global table or a global secondary index.                                                                                                                          |
| `CfnGlobalTable.WriteProvisionedThroughputSettingsProperty`       | Struct         | Specifies an auto scaling policy for write capacity.                                                                                                                                                     |
| `CfnGlobalTableProps`                                             | Struct         | Properties for defining a `CfnGlobalTable`.                                                                                                                                                              |
| `CfnTable.AttributeDefinitionProperty`                            | Struct         | Represents an attribute for describing the schema for the table and indexes.                                                                                                                             |
| `CfnTable.ContributorInsightsSpecificationProperty`               | Struct         | Configures contributor insights settings for a table or one of its indexes.                                                                                                                              |
| `CfnTable.CsvProperty`                                            | Struct         | The options for imported source files in CSV format.                                                                                                                                                     |
| `CfnTable.GlobalSecondaryIndexProperty`                           | Struct         | Represents the properties of a global secondary index.                                                                                                                                                   |
| `CfnTable.ImportSourceSpecificationProperty`                      | Struct         | Specifies the properties of data being imported from the S3 bucket source to the table.                                                                                                                  |
| `CfnTable.InputFormatOptionsProperty`                             | Struct         | The format options for the data that was imported into the target table.                                                                                                                                 |
| `CfnTable.KeySchemaProperty`                                      | Struct         | Represents *a single element* of a key schema.                                                                                                                                                           |
| `CfnTable.KinesisStreamSpecificationProperty`                     | Struct         | The Kinesis Data Streams configuration for the specified table.                                                                                                                                          |
| `CfnTable.LocalSecondaryIndexProperty`                            | Struct         | Represents the properties of a local secondary index.                                                                                                                                                    |
| `CfnTable.OnDemandThroughputProperty`                             | Struct         | Sets the maximum number of read and write units for the specified on-demand table.                                                                                                                       |
| `CfnTable.PointInTimeRecoverySpecificationProperty`               | Struct         | The settings used to enable point in time recovery.                                                                                                                                                      |
| `CfnTable.ProjectionProperty`                                     | Struct         | Represents attributes that are copied (projected) from the table into an index.                                                                                                                          |
| `CfnTable.ProvisionedThroughputProperty`                          | Struct         | Throughput for the specified table, which consists of values for `ReadCapacityUnits` and `WriteCapacityUnits` .                                                                                          |
| `CfnTable.ResourcePolicyProperty`                                 | Struct         | Creates or updates a resource-based policy document that contains the permissions for DynamoDB resources, such as a table, its indexes, and stream.                                                      |
| `CfnTable.S3BucketSourceProperty`                                 | Struct         | The S3 bucket that is being imported from.                                                                                                                                                               |
| `CfnTable.SearchSchemaElementProperty`                            | Struct         |                                                                                                                                                                                                          |
| `CfnTable.SSESpecificationProperty`                               | Struct         | Represents the settings used to enable server-side encryption.                                                                                                                                           |
| `CfnTable.StreamSpecificationProperty`                            | Struct         | Represents the DynamoDB Streams configuration for a table in DynamoDB.                                                                                                                                   |
| `CfnTable.TimeToLiveSpecificationProperty`                        | Struct         | Represents the settings used to enable or disable Time to Live (TTL) for the specified table.                                                                                                            |
| `CfnTable.VectorAttributeProperty`                                | Struct         |                                                                                                                                                                                                          |
| `CfnTable.VectorIndexProperty`                                    | Struct         |                                                                                                                                                                                                          |
| `CfnTable.WarmThroughputProperty`                                 | Struct         | Provides visibility into the number of read and write operations your table or secondary index can instantaneously support.                                                                              |
| `CfnTableProps`                                                   | Struct         | Properties for defining a `CfnTable`.                                                                                                                                                                    |
| `ContributorInsightsMode`                                         | Enum           | DynamoDB's Contributor Insights Mode.                                                                                                                                                                    |
| `ContributorInsightsSpecification`                                | Struct         | Reference to ContributorInsightsSpecification.                                                                                                                                                           |
| `CsvOptions`                                                      | Struct         | The options for imported source files in CSV format.                                                                                                                                                     |
| `EnableScalingProps`                                              | Struct         | Properties for enabling DynamoDB capacity scaling.                                                                                                                                                       |
| `GlobalSecondaryIndexProps`                                       | Struct         | Properties for a global secondary index.                                                                                                                                                                 |
| `GlobalSecondaryIndexPropsV2`                                     | Struct         | Properties used to configure a global secondary index.                                                                                                                                                   |
| `GlobalTableSettingsReplicationMode`                              | Enum           | The replication mode for global table settings across multiple accounts.                                                                                                                                 |
| `ImportSourceSpecification`                                       | Struct         | Properties for importing data from the S3.                                                                                                                                                               |
| `InputCompressionType`                                            | Enum           | Type of compression to use for imported data.                                                                                                                                                            |
| `InputFormat`                                                     | Class          | The format of the source data.                                                                                                                                                                           |
| `IScalableTableAttribute`                                         | Interface      | Interface for scalable attributes.                                                                                                                                                                       |
| `ITable`                                                          | Interface      | An interface that represents a DynamoDB Table - either created with the CDK, or an existing one.                                                                                                         |
| `ITableV2`                                                        | Interface      | Represents an instance of a DynamoDB table.                                                                                                                                                              |
| `KeySchema`                                                       | Struct         | A description of a key schema of an LSI, GSI or Table.                                                                                                                                                   |
| `LocalSecondaryIndexProps`                                        | Struct         | Properties for a local secondary index.                                                                                                                                                                  |
| `MaxThroughputProps`                                              | Struct         | Properties used to configure maximum throughput for an on-demand table.                                                                                                                                  |
| `MultiRegionConsistency`                                          | Enum           | Global table multi-region consistency mode.                                                                                                                                                              |
| `Operation`                                                       | Enum           | Supported DynamoDB table operations.                                                                                                                                                                     |
| `OperationsMetricOptions`                                         | Struct         | Options for configuring metrics that considers multiple operations.                                                                                                                                      |
| `PointInTimeRecoverySpecification`                                | Struct         | Reference to PointInTimeRecovey Specification for continuous backups.                                                                                                                                    |
| `ProjectionType`                                                  | Enum           | The set of attributes that are projected into the index.                                                                                                                                                 |
| `ReplicaGlobalSecondaryIndexOptions`                              | Struct         | Options used to configure global secondary indexes on a replica table.                                                                                                                                   |
| `ReplicaTableProps`                                               | Struct         | Properties used to configure a replica table.                                                                                                                                                            |
| `SchemaOptions`                                                   | Struct         | Represents the table schema attributes.                                                                                                                                                                  |
| `SecondaryIndexProps`                                             | Struct         | Properties for a secondary index.                                                                                                                                                                        |
| `StreamGrants`                                                    | Class          | A set of permissions to grant on a Table Stream.                                                                                                                                                         |
| `StreamGrantsProps`                                               | Struct         | Construction properties for StreamGrants.                                                                                                                                                                |
| `StreamViewType`                                                  | Enum           | When an item in the table is modified, StreamViewType determines what information is written to the stream for this table.                                                                               |
| `SystemErrorsForOperationsMetricOptions`                          | Struct         | Options for configuring a system errors metric that considers multiple operations.                                                                                                                       |
| `TableAttributes`                                                 | Struct         | Reference to a dynamodb table.                                                                                                                                                                           |
| `TableAttributesV2`                                               | Struct         | Attributes of a DynamoDB table.                                                                                                                                                                          |
| `TableClass`                                                      | Enum           | DynamoDB's table class.                                                                                                                                                                                  |
| `TableEncryption`                                                 | Enum           | What kind of server-side encryption to apply to this table.                                                                                                                                              |
| `TableEncryptionV2`                                               | Class          | Represents server-side encryption for a DynamoDB table.                                                                                                                                                  |
| `TableGrants`                                                     | Facade         | A set of permissions to grant on a Table.                                                                                                                                                                |
| `TableGrantsProps`                                                | Struct         | Construction properties for TableGrants.                                                                                                                                                                 |
| `TableOptions`                                                    | Struct         | Properties of a DynamoDB Table.                                                                                                                                                                          |
| `TableOptionsV2`                                                  | Struct         | Options used to configure a DynamoDB table.                                                                                                                                                              |
| `TableProps`                                                      | Struct         | Properties for a DynamoDB Table.                                                                                                                                                                         |
| `TablePropsV2`                                                    | Struct         | Properties used to configure a DynamoDB table.                                                                                                                                                           |
| `TableV2MultiAccountReplicaProps`                                 | Struct         | Properties for creating a multi-account replica table.                                                                                                                                                   |
| `ThroughputProps`                                                 | Struct         | Properties used to configure provisioned throughput for a DynamoDB table.                                                                                                                                |
| `UtilizationScalingProps`                                         | Struct         | Properties for enabling DynamoDB utilization tracking.                                                                                                                                                   |
| `WarmThroughput`                                                  | Struct         | Reference to WarmThroughput for a DynamoDB table.                                                                                                                                                        |
