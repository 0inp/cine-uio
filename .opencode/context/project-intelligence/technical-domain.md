<!-- Context: project-intelligence/technical | Priority: critical | Version: 1.0 | Updated: 2026-04-02 -->

# Technical Domain

**Purpose**: Tech stack, architecture, development patterns for this project.
**Last Updated**: 2026-04-02

## Quick Reference
**Update Triggers**: Tech stack changes | New patterns | Architecture decisions
**Audience**: Developers, AI agents

## Primary Stack
| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Framework | SolidJS | Latest | Reactive UI with fine-grained updates |
| Styling | TailwindCSS | Latest | Utility-first CSS framework |
| Backend | Go | 1.26.1 | High performance, concurrent backend |
| Database | SQLite | Latest | Lightweight, file-based database |

## Backend Toolchain
| Tool | Version | Purpose |
|------|---------|---------|
| chromedp | v0.15.1 | Headless Chrome automation for web scraping |
| goquery | v1.12.0 | HTML parsing and DOM manipulation |
| GORM | v1.31.1 | ORM for database operations |
| SQLite Driver | v1.6.0 | SQLite database connectivity |

## Code Patterns

### API Endpoint
*(No specific API pattern provided - using Go standard patterns)*

### Component
*(No specific component pattern provided - using SolidJS standard patterns)*

### Web Scraping
- Use `chromedp` for headless browser automation
- Parse HTML with `goquery` for DOM manipulation
- Implement proper error handling and retries
- Use context-based cancellation for cleanup
- Handle dynamic content with appropriate waits

#### Scraping Best Practices (Updated 2026-04-12)
- **Dynamic Waiting**: Use `chromedp.WaitVisible()` instead of fixed `Sleep()` delays
- **Retry Logic**: Implement 2-3 retry attempts for transient failures
- **Content Verification**: Verify active state and content presence before parsing
- **Targeted Parsing**: Parse only relevant DOM sections, not entire page
- **Early Exit**: Detect and skip empty states (`.EmptyState`) immediately
- **Active Day Verification**: Confirm correct day loaded after navigation
- **Multi-level Validation**: Check container existence, content presence, and element availability

#### Day Navigation Pattern
```go
// 1. Click day button with retry logic
for retry := 0; retry <= maxRetries; retry++ {
    err = chromedp.Run(s.Ctx,
        chromedp.Click(fmt.Sprintf(`.slick-slide[data-index="%d"]`, dayIndex)),
        chromedp.WaitVisible(`.MovieDetail__content__session-type`),
        chromedp.WaitNotPresent(`div[class*="loading"]`),
    )

    // 2. Verify correct day is active
    var activeDayIndex int
    chromedp.Evaluate(`parseInt(document.querySelector('.slick-slide.slick-active')?.getAttribute('data-index') || '-1')`, &activeDayIndex)

    // 3. Retry if mismatch, succeed if correct
    if activeDayIndex == dayIndex {
        success = true
        break
    }
}
```

#### EmptyState Detection Pattern
```go
// Check for EmptyState before processing
var hasEmptyState bool
chromedp.Evaluate(`!!document.querySelector('.MovieDetail__content__session-type .EmptyState')`, &hasEmptyState)
if hasEmptyState {
    logger.Info("Skipping: EmptyState detected (no screenings)")
    return nil, nil // Early exit
}
```

## Naming Conventions
| Type | Convention | Example |
|------|-----------|---------|
| Files | kebab-case | user-profile.jsx |
| Components | PascalCase | UserProfile |
| Functions | camelCase | getUserProfile |
| Database | snake_case | user_profiles |
| Go packages | lowercase | userprofile |

## Code Standards
- Use TypeScript for all components
- Validate all API inputs
- Use prepared statements for SQL queries
- Follow SolidJS reactive principles
- Use TailwindCSS for styling
- Write unit tests for critical functions
- Document public functions with JSDoc
- Use semantic versioning for Go modules
- Implement proper error wrapping in Go
- Use context-based cancellation for long-running operations

## Security Requirements
- Use parameterized queries to prevent SQL injection

## 📂 Codebase References
**Implementation**: `src/` - SolidJS components and Go backend services
**Backend**: `backend/` - Go web scraping and data processing
**Config**: package.json, go.mod, tsconfig.json, mise.toml

## Related Files
- Business Domain (example: business-domain.md)
- Decisions Log (example: decisions-log.md)
