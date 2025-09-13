/**
 * Provider Interface Contracts
 * These TypeScript interfaces define the contracts that all providers must implement.
 */

// Common Types
export interface ProviderMetadata {
  name: string;
  version: string;
  type: 'scraping' | 'storage';
  capabilities: string[];
}

export interface ConnectionConfig {
  [key: string]: any;
}

export interface PageContext {
  url: string;
  title: string;
  cookies: Cookie[];
  navigationHistory: string[];
  viewport: {
    width: number;
    height: number;
  };
  userAgent: string;
}

export interface Cookie {
  name: string;
  value: string;
  domain: string;
  path: string;
  expires?: number;
  httpOnly: boolean;
  secure: boolean;
}

export interface DataElement {
  id: string;
  type: 'text' | 'link' | 'image' | 'structured';
  value: any;
  metadata: {
    selector: string;
    sourceUrl: string;
    timestamp: string;
    xpath?: string;
  };
}

// Step Configuration Types
export interface InitStepConfig {
  url: string;
  waitFor?: string | number;
  cookies?: Cookie[];
  headers?: Record<string, string>;
}

export interface DiscoverStepConfig {
  selectors: {
    [elementType: string]: string;
  };
  pagination?: {
    nextPageSelector: string;
    maxPages?: number;
  };
}

export interface ExtractStepConfig {
  elements: {
    [fieldName: string]: {
      selector: string;
      type: 'text' | 'attribute' | 'html';
      attribute?: string;
      transform?: string;
    };
  };
}

export interface PaginateStepConfig {
  nextPageSelector: string;
  maxPages?: number;
  waitAfterClick?: number;
  stopCondition?: {
    selector: string;
    condition: 'exists' | 'not-exists';
  };
}

// Scraping Provider Interface
export interface ScrapingProviderInterface {
  readonly metadata: ProviderMetadata;

  /**
   * Initialize the provider with configuration
   */
  initialize(config: ConnectionConfig): Promise<void>;

  /**
   * Navigate to initial URL and setup page context
   */
  executeInit(stepConfig: InitStepConfig): Promise<PageContext>;

  /**
   * Discover available data elements on the page
   */
  executeDiscover(
    stepConfig: DiscoverStepConfig,
    context: PageContext
  ): Promise<DataElement[]>;

  /**
   * Extract specific data elements from the page
   */
  executeExtract(
    stepConfig: ExtractStepConfig,
    context: PageContext
  ): Promise<DataElement[]>;

  /**
   * Navigate to next page if available
   * Returns new context or null if no more pages
   */
  executePaginate(
    stepConfig: PaginateStepConfig,
    context: PageContext
  ): Promise<PageContext | null>;

  /**
   * Clean up resources (close browser, etc.)
   */
  cleanup(): Promise<void>;

  /**
   * Health check for provider availability
   */
  healthCheck(): Promise<boolean>;
}

// Storage Provider Interface
export interface SchemaDefinition {
  name: string;
  fields: {
    [fieldName: string]: {
      type: 'string' | 'number' | 'boolean' | 'date' | 'json';
      required: boolean;
      maxLength?: number;
      index?: boolean;
    };
  };
  primaryKey?: string[];
  indexes?: {
    name: string;
    fields: string[];
    unique: boolean;
  }[];
}

export interface QueryCriteria {
  where?: Record<string, any>;
  orderBy?: {
    field: string;
    direction: 'ASC' | 'DESC';
  }[];
  limit?: number;
  offset?: number;
}

export interface StorageProviderInterface {
  readonly metadata: ProviderMetadata;

  /**
   * Establish connection to storage backend
   */
  connect(config: ConnectionConfig): Promise<void>;

  /**
   * Disconnect from storage backend
   */
  disconnect(): Promise<void>;

  /**
   * Store data elements according to schema
   */
  store(data: DataElement[], schema: SchemaDefinition): Promise<void>;

  /**
   * Query stored data
   */
  query(criteria: QueryCriteria, schema: SchemaDefinition): Promise<DataElement[]>;

  /**
   * Create schema/table structure
   */
  createSchema(definition: SchemaDefinition): Promise<void>;

  /**
   * Validate schema definition
   */
  validateSchema(definition: SchemaDefinition): Promise<boolean>;

  /**
   * Check if schema exists
   */
  schemaExists(schemaName: string): Promise<boolean>;

  /**
   * Get schema information
   */
  getSchema(schemaName: string): Promise<SchemaDefinition>;

  /**
   * Health check for storage connectivity
   */
  healthCheck(): Promise<boolean>;

  /**
   * Get storage statistics
   */
  getStats(): Promise<{
    totalRecords: number;
    lastUpdated: string;
    storageSize?: number;
  }>;
}

// Workflow Engine Interface
export interface WorkflowStep {
  id: string;
  command: 'init' | 'discover' | 'extract' | 'paginate';
  config: InitStepConfig | DiscoverStepConfig | ExtractStepConfig | PaginateStepConfig;
  retries: number;
  timeout: number;
  continueOnError: boolean;
}

export interface Workflow {
  version: string;
  metadata: {
    name: string;
    description: string;
    author: string;
    created: string;
    tags: string[];
    targetSite: string;
  };
  scraping: {
    provider: string;
    config: ConnectionConfig;
  };
  storage: {
    provider: string;
    config: ConnectionConfig;
    schema?: SchemaDefinition;
  };
  steps: WorkflowStep[];
  postProcessing?: {
    type: 'filter' | 'transform' | 'validate' | 'deduplicate';
    config: any;
  }[];
}

// Execution Result Types
export interface StepResult {
  stepId: string;
  status: 'completed' | 'failed' | 'skipped';
  startTime: string;
  endTime: string;
  duration: number;
  data?: DataElement[];
  error?: {
    code: string;
    message: string;
    stack?: string;
  };
  retryCount: number;
}

export interface WorkflowResult {
  workflowId: string;
  status: 'completed' | 'failed' | 'partial';
  startTime: string;
  endTime: string;
  duration: number;
  steps: StepResult[];
  totalRecords: number;
  storage: {
    provider: string;
    location: string;
  };
  errors: Array<{
    step: string;
    message: string;
    recoverable: boolean;
  }>;
}

// Provider Factory Interface
export interface ProviderFactory {
  /**
   * Create scraping provider instance
   */
  createScrapingProvider(name: string): Promise<ScrapingProviderInterface>;

  /**
   * Create storage provider instance
   */
  createStorageProvider(name: string): Promise<StorageProviderInterface>;

  /**
   * List available providers
   */
  listProviders(type?: 'scraping' | 'storage'): Promise<ProviderMetadata[]>;

  /**
   * Register new provider
   */
  registerProvider(provider: ScrapingProviderInterface | StorageProviderInterface): void;

  /**
   * Test provider connectivity
   */
  testProvider(name: string, config: ConnectionConfig): Promise<boolean>;
}

// Workflow Engine Interface
export interface WorkflowEngine {
  /**
   * Execute workflow from definition
   */
  execute(workflow: Workflow): Promise<WorkflowResult>;

  /**
   * Validate workflow definition
   */
  validate(workflow: Workflow): Promise<{
    valid: boolean;
    errors: Array<{
      field: string;
      message: string;
    }>;
  }>;

  /**
   * Get execution status
   */
  getStatus(workflowId: string): Promise<WorkflowResult>;

  /**
   * Cancel running workflow
   */
  cancel(workflowId: string): Promise<void>;
}
