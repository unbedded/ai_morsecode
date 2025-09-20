# Design Documentation

This directory contains architectural design documents for the Morse Code Decoder project.

## Design Documents

### 📋 [Project Plan](./project-plan.md)
**Status**: ✅ Current and maintained
**Summary**: Comprehensive project roadmap with phase tracking, architecture overview, and development milestones.

**Key Content**:
- Complete development phases (1-7.5 all completed)
- Architecture components and status
- Testing strategy and current metrics
- Configuration system documentation
- Ready for merge assessment

### 🎨 [Graphics TODO Roadmap](./graphics_todo_roadmap.md)
**Status**: 📝 Planning document
**Summary**: Development roadmap for ASCII graphics visualization components with Rich library integration.

**Key Features**:
- Real-time signal visualization
- Terminal-based waveform displays
- Event-driven graphics updates
- Performance monitoring displays

### 🤖 [Claude Commands Improvement Plan](./CLAUDE_COMMANDS_IMPROVEMENT_PLAN.md)
**Status**: 📝 Enhancement proposal
**Summary**: Proposed improvements for Claude Code integration and command workflows.

**Key Improvements**:
- Enhanced command patterns
- Workflow optimization
- Integration enhancements
- User experience improvements

### 🏗️ [ConfigurableBase Design Record](../src/util/docs/configurable-base-design-record.md)
**Status**: ✅ Implemented and deployed
**Summary**: **MOVED TO UTIL PACKAGE** - Design decision record for ConfigurableBase inheritance pattern with runtime reconfiguration and C++ compatibility.

**Key Achievements**:
- Abstract base class successfully eliminates 90% of boilerplate
- Runtime reconfiguration without component recreation - proven in production
- Override dictionary pattern enables trivial testing
- C++-compatible interface design for future performance ports
- All components migrated successfully (181 tests passing)

---

## Document Standards

### Document Template
```markdown
# [Title]

**Document**: Brief description
**Version**: X.Y
**Date**: YYYY-MM-DD
**Status**: [Draft|Review|Implemented|Deprecated]

## Problem Statement
Brief description of what we're solving

## Proposed Solution
Architecture and design approach

## Implementation Status
What's been completed and what's pending

## Benefits
Why this approach is better
```

### Status Indicators
- 📝 **Draft** - Initial design, under development
- 👁️ **Review** - Ready for review
- ✅ **Implemented** - Complete and in production
- 🔄 **Current** - Living document, actively maintained
- ⚠️ **Deprecated** - No longer applicable

### Document Categories
- **Planning Documents**: Roadmaps, project plans, and strategic planning
- **Design Records**: Architecture decisions and implementation rationale
- **Enhancement Proposals**: Future improvements and feature planning
- **Reference Documentation**: Moved to appropriate package locations

---

*For questions about design documents, see [CLAUDE.md](../../CLAUDE.md) for development standards.*

*For UTIL package documentation, see [src/util/docs/](../src/util/docs/) for reusable configuration and logging patterns.*