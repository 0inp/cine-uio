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
| Backend | Go | Latest | High performance, concurrent backend |
| Database | SQLite | Latest | Lightweight, file-based database |

## Code Patterns
### API Endpoint
*(No specific API pattern provided - using Go standard patterns)*

### Component
*(No specific component pattern provided - using SolidJS standard patterns)*

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

## Security Requirements
- Use parameterized queries to prevent SQL injection

## 📂 Codebase References
**Implementation**: `src/` - SolidJS components and Go backend services
**Config**: package.json, go.mod, tsconfig.json

## Related Files
- Business Domain (example: business-domain.md)
- Decisions Log (example: decisions-log.md)