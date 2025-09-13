# Scrapper Constitution

## Core Principles

### 1. Follow github development flow

Create a Branch
Start by creating a descriptive branch from the main branch to work on a new feature or fix. This isolates your changes and keeps the main branch production-ready.

Make Commits
Develop your feature or fix, committing changes with clear, concise messages. Frequent commits help in tracking progress and facilitate easier reviews.

Open a Pull Request (PR)
Once your work is ready, open a PR to propose your changes. This initiates a discussion and review process, allowing team members to provide feedback.

Review and Discuss
Collaborate with your team through comments and suggestions on the PR. Address any feedback by making additional commits to the same branch.

Merge the PR
After approvals and successful checks, merge the PR into the main branch. This step integrates your changes into the production-ready codebase.

Deploy
Deploy the updated main branch to production. With CI/CD tools, this can be automated to ensure rapid and reliable releases.

### 2. Library-First Architecture
Every feature MUST begin its existence as a standalone library. No feature shall be implemented directly within application code without first being abstracted into a reusable library component. Libraries must be self-contained, independently testable, and properly documented with clear purpose and boundaries.

### 3. CLI Interface Protocol
Every library exposes its functionality through a command-line interface following text I/O protocol:
- Input: stdin/args → Output: stdout
- Errors: stderr
- Support both JSON and human-readable output formats
- Enable composability through Unix philosophy

### 4. Test-First Development (NON-NEGOTIABLE)
Test-Driven Development is mandatory for all implementations:
- Write tests first → Get user approval → Tests must fail → Then implement
- Red-Green-Refactor cycle strictly enforced
- No implementation without failing tests
- UI components require Playwright tests for user interactions
- All tests must pass before considering work complete

### 5. GitHub Issues Integration
All work is tracked through GitHub Issues:

#### Issue Lifecycle Management
- Check for existing issues before starting work: `gh issue list --state open`
- Assign issue to self when starting: `gh issue edit [issue-number] --add-assignee @me`
- Add "in-progress" label: `gh issue edit [issue-number] --add-label "in-progress"`
- Remove other status labels when updating
- Link commits to issues using `#[issue-number]` in commit messages
- Close issues automatically via PR description: `Closes #[issue-number]`

#### Issue Comments for Communication
- Comment when starting work: `gh issue comment [issue-number] --body "Starting work on this issue"`
- Update progress in issue comments
- Document blockers or dependencies
- Notify team of completion in issue before PR

### 6. Git Workflow Protocol (Team Collaboration)
Every development task follows professional remote developer practices:

#### Branch Management
- Branch name format: `[issue-number]-[short-description]`
- Always create from latest `main`: `git checkout main && git pull origin main && git checkout -b [branch-name]`
- Never work directly on `main` branch
- Update from `main` before final push: `git fetch origin && git rebase origin/main`
- Resolve conflicts locally before pushing

#### Development Cycle
1. Find/create GitHub issue for task
2. Assign issue to self and add "in-progress" label
3. Comment on issue announcing start of work
4. Create feature branch with issue number
5. Implement following TDD principles
6. Write/update tests (unit, integration, Playwright for UI)
7. Run all tests locally: `npm test && npm run test:e2e`
8. Update from main and resolve conflicts
9. Commit with issue reference: `git commit -m "[#issue-number] Description of change"`
10. Push feature branch to remote

#### Pull Request Protocol
- Create PR using GitHub CLI: `gh pr create --title "[#issue-number] Feature name" --body-file .github/pull_request_template.md`
- PR description must include:
  - `Closes #[issue-number]` to auto-close issue
  - Summary of changes
  - Testing instructions
  - Screenshots for UI changes
- Self-review using: `gh pr diff [pr-number]`
- Request reviews: `gh pr edit [pr-number] --add-reviewer [reviewer]`
- Address review comments promptly
- Ensure all checks pass: `gh pr checks [pr-number]`
- Merge only after approval: `gh pr merge [pr-number] --squash`

#### Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- Playwright tests for UI interactions: `npx playwright test`
- Test coverage must exceed 80%
- All tests must pass in CI/CD pipeline
- Screenshot tests for UI components when applicable

### 6. Multi-Developer Awareness
Operate with awareness of concurrent team development:
- Check issue assignments before starting: `gh issue list --assignee "@me"`
- Review other open PRs for conflicts: `gh pr list --state open`
- Communicate via issue comments, not external channels
- Keep commits atomic and focused
- Write clear commit messages linking to issues
- Update shared documentation

### 7. Continuous Integration Compliance
All code must pass through GitHub Actions CI/CD:
- Automated test execution on every push
- Required checks must pass before merge:
  - Unit tests
  - Integration tests
  - Playwright E2E tests
  - Code coverage threshold
  - Linting and formatting
  - Security scanning
- Monitor workflow status: `gh run list --workflow=ci.yml`
- Fix failing workflows immediately

### 8. Code Review Discipline
Practice thorough code review using GitHub:
- Self-review before requesting others: `gh pr diff`
- Use GitHub review features:
  - Comment on specific lines
  - Suggest changes
  - Approve or request changes
- Check for:
  - Correctness and test coverage
  - Constitutional compliance
  - Performance implications
  - Security considerations
- Respond to all review comments
- Re-request review after changes: `gh pr review [pr-number] --request`

### 9. Documentation as Code
Documentation is part of the implementation:
- Update README with setup/usage changes
- Document API changes in contracts
- Update quickstart.md for new features
- Include JSDoc/docstrings for public APIs
- Maintain CHANGELOG.md entries
- Update GitHub wiki for architectural decisions

### 10. Incremental Delivery
Deliver value incrementally:
- Break large features into smaller issues
- Each PR should close one issue
- Maintain backward compatibility
- Use feature flags for gradual rollout
- No PRs larger than 500 lines (excluding tests)
- Tag releases: `git tag -a v[version] -m "Release notes"`

## GitHub Issues Workflow Commands

### Required GitHub CLI Commands

```bash
# Before starting work - Check available issues
gh issue list --state open --label "ready-for-dev"
gh issue list --assignee @me

# Claim an issue
gh issue edit [issue-number] --add-assignee @me
gh issue edit [issue-number] --add-label "in-progress"
gh issue edit [issue-number] --remove-label "ready-for-dev"
gh issue comment [issue-number] --body "Starting work on this issue. ETA: [estimate]"

# During development - Update status
gh issue comment [issue-number] --body "Progress update: [what's completed]"
gh issue comment [issue-number] --body "Blocker: [describe blocker] cc @[team-member]"

# Create PR
gh pr create \
  --title "[#issue-number] Feature description" \
  --body "Closes #[issue-number]\n\n## Summary\n[changes]\n\n## Testing\n[how to test]" \
  --draft  # Remove --draft when ready for review

# Review process
gh pr ready [pr-number]  # Mark ready for review
gh pr review [pr-number] --approve
gh pr review [pr-number] --request-changes --body "Issues found..."
gh pr checks [pr-number]  # Check CI status

# Completion
gh pr merge [pr-number] --squash --delete-branch
# Issue auto-closes if "Closes #X" is in PR description
```

## Implementation Checklist

Before marking any task complete, verify:

- [ ] GitHub issue assigned to self
- [ ] Issue labeled as "in-progress"
- [ ] Feature branch created with issue number in name
- [ ] All tests written and passing locally
- [ ] Code follows project standards and constitution
- [ ] Branch rebased on latest main
- [ ] Commits reference issue number (#X)
- [ ] PR created with "Closes #X" in description
- [ ] Self-review completed using gh pr diff
- [ ] CI/CD checks passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] PR squash-merged and branch deleted
- [ ] Issue automatically closed by PR

## Enforcement

These principles are immutable during feature development. Any deviation requires:
1. Create a GitHub issue labeled "constitution-exception"
2. Document the deviation and justification
3. Get team approval via issue comments
4. Link exception issue to implementation issue
5. Plan to address technical debt in follow-up issue

The constitution ensures that AI-generated code maintains professional development standards while fully integrating with GitHub's collaboration features.
