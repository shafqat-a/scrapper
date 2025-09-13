# Data Model: Provider-Based Web Scraping System

## Core Entities

### Workflow
Represents a complete scraping configuration and execution plan.

**Fields**:
- `id`: string - Unique workflow identifier
- `version`: string - Workflow schema version (semver)
- `metadata`: WorkflowMetadata - Descriptive information
- `scraping`: ScrapingConfig - Provider and scraping configuration
- `storage`: StorageConfig - Data persistence configuration
- `steps`: WorkflowStep[] - Ordered execution steps
- `postProcessing`: PostProcessingStep[] - Optional data transformation steps

**Validation Rules**:
- ID must be alphanumeric with hyphens/underscores only
- Version must follow semver format (x.y.z)
- At least one step with command 'init' required
- Steps must form valid execution sequence
- Provider names must exist in available provider registry

**State Transitions**:
- Created → Validated → Executing → Completed/Failed
- Failed workflows can be retried from last successful step

### WorkflowMetadata
Descriptive information about the workflow.

**Fields**:
- `name`: string - Human-readable workflow name
- `description`: string - Purpose and scope description
- `author`: string - Creator identification
- `created`: ISO string - Creation timestamp
- `tags`: string[] - Categorization labels
- `targetSite`: string - Primary website being scraped

**Validation Rules**:
- Name required, max 100 characters
- Description required, max 500 characters
- Created must be valid ISO 8601 timestamp
- Tags must be lowercase alphanumeric

### ScrapingProvider
Pluggable component implementing website-specific scraping logic.

**Fields**:
- `name`: string - Provider identifier (e.g., 'playwright', 'cheerio')
- `version`: string - Provider version
- `config`: ProviderConfig - Provider-specific configuration
- `capabilities`: string[] - Supported features (js-rendering, cookies, etc.)

**Validation Rules**:
- Name must match registered provider
- Version must be compatible with workflow engine
- Config must validate against provider schema

### StorageProvider
Pluggable component handling data persistence.

**Fields**:
- `name`: string - Storage provider identifier (e.g., 'postgresql', 'csv')
- `version`: string - Provider version
- `config`: StorageConfig - Connection and formatting options
- `schema`: SchemaDefinition - Expected data structure

**Validation Rules**:
- Name must match registered storage provider
- Config must include required connection parameters
- Schema must define all expected data fields

### WorkflowStep
Individual executable command within a workflow.

**Fields**:
- `id`: string - Unique step identifier within workflow
- `command`: StepCommand - Action type ('init', 'discover', 'extract', 'paginate')
- `config`: StepConfig - Command-specific parameters
- `retries`: number - Maximum retry attempts (default: 3)
- `timeout`: number - Step timeout in milliseconds (default: 30000)
- `continueOnError`: boolean - Whether to proceed if step fails (default: false)

**Validation Rules**:
- ID must be unique within workflow
- Command must be one of defined enum values
- Timeout must be positive integer
- Retries must be non-negative integer

**State Transitions**:
- Pending → Running → Completed/Failed
- Failed steps can be retried up to retry limit

### DataElement
Individual piece of extracted information.

**Fields**:
- `id`: string - Unique identifier for this data piece
- `type`: DataType - Classification of data (text, link, image, structured)
- `value`: any - The extracted content
- `metadata`: ElementMetadata - Source and extraction context
- `timestamp`: ISO string - When data was extracted
- `selector`: string - CSS/XPath selector used for extraction

**Validation Rules**:
- Type must match value format
- Value cannot be null for required fields
- Timestamp must be valid ISO 8601
- Selector must be valid CSS or XPath expression

### PageContext
Current state of scraping session.

**Fields**:
- `url`: string - Current page URL
- `title`: string - Page title
- `cookies`: Cookie[] - Current session cookies
- `navigationHistory`: string[] - Previous URLs visited
- `viewport`: Viewport - Current browser viewport size
- `userAgent`: string - Current user agent string

**Validation Rules**:
- URL must be valid HTTP/HTTPS
- Viewport dimensions must be positive integers
- Navigation history limited to 100 entries

## Provider Interface Contracts

### ScrapingProviderInterface
Common interface that all scraping providers must implement.

```typescript
interface ScrapingProviderInterface {
  name: string;
  version: string;

  // Initialization
  initialize(config: ProviderConfig): Promise<void>;

  // Step execution
  executeInit(stepConfig: InitStepConfig): Promise<PageContext>;
  executeDiscover(stepConfig: DiscoverStepConfig, context: PageContext): Promise<DataElement[]>;
  executeExtract(stepConfig: ExtractStepConfig, context: PageContext): Promise<DataElement[]>;
  executePaginate(stepConfig: PaginateStepConfig, context: PageContext): Promise<PageContext | null>;

  // Cleanup
  cleanup(): Promise<void>;
}
```

### StorageProviderInterface
Common interface that all storage providers must implement.

```typescript
interface StorageProviderInterface {
  name: string;
  version: string;

  // Connection management
  connect(config: ConnectionConfig): Promise<void>;
  disconnect(): Promise<void>;

  // Data operations
  store(data: DataElement[], schema: SchemaDefinition): Promise<void>;
  query(criteria: QueryCriteria): Promise<DataElement[]>;

  // Schema management
  createSchema(definition: SchemaDefinition): Promise<void>;
  validateSchema(definition: SchemaDefinition): Promise<boolean>;
}
```

## Data Flow

### Workflow Execution Flow
1. **Workflow Validation**: Validate JSON schema and provider availability
2. **Provider Initialization**: Load and configure scraping and storage providers
3. **Step Execution**: Execute each workflow step in sequence
4. **Data Collection**: Accumulate extracted data elements
5. **Post-processing**: Apply optional data transformations
6. **Storage**: Persist final dataset using storage provider
7. **Cleanup**: Release resources and close connections

### Error Handling Flow
1. **Step Failure**: Log error details and context
2. **Retry Logic**: Attempt step retry if retries remaining
3. **Error Propagation**: Mark workflow as failed if step cannot recover
4. **Partial Success**: Save any successfully extracted data
5. **Cleanup**: Ensure all resources are properly released

### Data Transformation Pipeline
1. **Raw Extraction**: Data elements as extracted from page
2. **Type Conversion**: Convert to appropriate data types
3. **Validation**: Ensure data meets schema requirements
4. **Post-processing**: Apply custom transformations if configured
5. **Schema Mapping**: Map to storage provider schema format
6. **Persistence**: Store in configured storage backend

## Relationships

### Workflow → WorkflowStep (1:n)
- One workflow contains multiple steps
- Steps executed in defined order
- Step failure can halt workflow execution

### WorkflowStep → DataElement (1:n)
- Each step can produce multiple data elements
- Data elements linked to source step for traceability

### PageContext → DataElement (1:n)
- Data elements extracted from specific page context
- Context provides source URL and extraction environment

### Workflow → ScrapingProvider (n:1)
- Multiple workflows can use same scraping provider
- Provider handles multiple concurrent workflows

### Workflow → StorageProvider (n:1)
- Multiple workflows can use same storage provider
- Provider manages data isolation between workflows

## Schema Evolution

### Version Compatibility
- Backward compatibility maintained for minor version increments
- Breaking changes require major version increment
- Migration utilities provided for schema updates

### Provider Compatibility
- Provider interfaces versioned independently
- Workflow engine maintains compatibility matrix
- Graceful degradation for unsupported provider versions