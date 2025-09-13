# Implementation Plan: Provider-Based Web Scraping System


**Branch**: `001-read-spec-md` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-read-spec-md/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement a provider-based web scraping system that allows data analysts to configure and run scraping workflows through JSON definitions. The system uses pluggable providers for both scraping strategies (per website) and storage backends (CSV, PostgreSQL, MongoDB, etc.). Core workflow includes: Init → Discovery → Extraction → Pagination → Post-processing, with each step defined as composable commands in JSON format. **Updated to use Python due to its superior web scraping ecosystem and extensive library support.**

## Technical Context
**Language/Version**: Python 3.11+ (superior web scraping ecosystem with extensive libraries)
**Primary Dependencies**: Scrapy, Playwright, BeautifulSoup4, Requests, Click, Pydantic, SQLAlchemy
**Storage**: Multiple providers - CSV, PostgreSQL, SQL Server, MongoDB, JSON files
**Testing**: pytest with pytest-asyncio, Playwright Test for E2E, Docker for integration tests
**Target Platform**: Cross-platform CLI tool (Linux/macOS/Windows)
**Project Type**: single - CLI-based scraping system with Python packaging
**Performance Goals**: 10-100 concurrent scrapers, <1GB memory per workflow, 1-50 req/sec rate limiting
**Constraints**: Anti-detection strategies, exponential backoff retries, configurable timeouts
**Scale/Scope**: Single workflow execution model, streaming for large datasets, containerized testing

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (scraping system with CLI interface using Python packaging)
- Using framework directly? YES (direct use of Scrapy, Playwright, BeautifulSoup)
- Single data model? YES (unified workflow and data element models with Pydantic)
- Avoiding patterns? YES (provider pattern justified for pluggable architecture)

**Architecture**:
- EVERY feature as library? YES (scraping-core, scrapers, storage, cli as separate Python packages)
- Libraries listed: scraping-core (workflow engine), scrapers (provider implementations), storage (persistence providers), cli (Click-based command interface)
- CLI per library: YES (--help/--version/--format for each component using Click)
- Library docs: YES (llms.txt format planned with Python docstrings)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? YES (tests written before implementation using pytest)
- Git commits show tests before implementation? YES (constitutional requirement)
- Order: Contract→Integration→E2E→Unit strictly followed? YES
- Real dependencies used? YES (actual storage backends for integration tests via Docker)
- Integration tests for: YES (provider interfaces, workflow execution, storage operations)
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? YES (Python logging with structured output, scraping progress)
- Frontend logs → backend? N/A (CLI-only application)
- Error context sufficient? YES (detailed error context for debugging failed scrapes)

**Versioning**:
- Version number assigned? 0.1.0 (initial implementation)
- BUILD increments on every change? YES
- Breaking changes handled? YES (provider interface versioning with semantic versioning)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Python package (DEFAULT)
src/
├── scraper_core/
│   ├── models/
│   ├── workflow/
│   └── __init__.py
├── providers/
│   ├── scrapers/
│   ├── storage/
│   └── __init__.py
└── cli/
    ├── commands/
    └── __init__.py

tests/
├── contract/
├── integration/
├── unit/
└── fixtures/

pyproject.toml
setup.py (compatibility)
requirements.txt

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 - Single project structure suitable for Python CLI package with pip distribution

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy (Python-focused)**:
The /tasks command will create tasks.md by analyzing the Python-based design artifacts:

1. **From contracts/provider-interfaces.py**: Generate pytest contract tests for each protocol method
2. **From contracts/workflow.schema.json**: Generate Pydantic model validation tests
3. **From data-model.md entities**: Generate Python class definitions with Pydantic models
4. **From cli-api.md**: Generate Click-based CLI command implementations
5. **From quickstart.md scenarios**: Generate pytest integration tests validating user workflows

**Specific Task Categories (Python Implementation)**:
- **Contract Tests** (15-18 tasks): pytest tests for each provider protocol method, must fail initially
- **Pydantic Models** (8-10 tasks): Data model classes with validation and JSON schema generation
- **Provider Implementations** (8-10 tasks): Scrapy, BeautifulSoup, CSV, PostgreSQL providers for MVP
- **Workflow Engine** (6-8 tasks): AsyncIO-based workflow execution, error handling, retry logic
- **CLI Interface** (4-5 tasks): Click commands, Rich output formatting, configuration management
- **Integration Tests** (6-8 tasks): End-to-end workflow validation with Docker containers

**Ordering Strategy**:
1. **TDD Constitutional Order**: All pytest tests before implementation
2. **Python Dependency Flow**: Pydantic models → Provider protocols → Implementations → Engine → CLI → Integration
3. **Parallel Marking**: Independent tasks marked [P] for concurrent execution
4. **Library-First**: Each component as standalone Python package with pip installation

**Task Template Structure**:
Each task will include:
- Clear acceptance criteria based on constitutional requirements
- pytest test mandate (RED phase required before implementation)
- Python file locations and expected class interfaces
- Dependencies on other tasks (imports, inheritance)
- Definition of done including test coverage and type hints

**Estimated Output**: 41-59 numbered, ordered tasks covering full Python implementation

**Constitutional Compliance Validation**:
Tasks will enforce:
- Every feature implemented as Python library first (pip installable)
- Click CLI interface for each library component
- Real dependencies in integration tests (Docker containers with pytest)
- No implementation without failing pytest tests first
- Structured Python logging with asyncio support
- Type hints and Pydantic validation throughout

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - Python technology decisions
- [x] Phase 1: Design complete (/plan command) - Python interfaces and contracts
- [x] Phase 2: Task planning complete (/plan command - Python-focused approach described)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (Python stack decisions made)
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
