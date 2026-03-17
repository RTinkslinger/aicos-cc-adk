# Stack Discoveries Log

## Discovery 001: Cowork Connector Landscape (March 1, 2026)

**Source:** Web research during planning session

### Findings

**Available and relevant to Aakash's stack:**
- Notion MCP connector — works now, DeVC CRM accessible
- Granola MCP connector — works now, meeting notes accessible (Mac only)
- Gmail / GCal / GDrive — works now, for personal-pro stack (hi@aacash.me)
- Microsoft 365 — shipped Feb 2026, covers Outlook/Teams/OneDrive/SharePoint
- FactSet — available for enterprise plans

**Not available / gaps:**
- Attio — no native MCP. API exists. Custom MCP server needed.
- WhatsApp — no integration path. Biggest gap given usage intensity.

**New since Jan 2026:**
- Cowork plugins: bundles of skills + connectors + slash commands
- Pre-built plugin templates for: financial analysis, investment banking, equity research, PE, wealth management
- Plugin marketplace for enterprise (private GitHub repos as sources)
- Cross-app workflows: Excel ↔ PowerPoint context passing
- Windows support shipped

### Implications for AI CoS
1. Start with Notion + Granola + Gmail connectors immediately (Phase A Sprint 1)
2. Test M365 connector reliability early — fund email is critical path
3. Attio MCP is a Claude Code build target (Phase A Sprint 4 or Phase B)
4. WhatsApp requires creative bridging (manual export → Claude processing?)
5. Evaluate Anthropic's pre-built PE/VC plugin templates before building from scratch

### Action Items
- [ ] Connect Notion MCP in Cowork and test DeVC data access
- [ ] Connect Granola MCP and test meeting notes retrieval
- [ ] Connect M365 and test with aakash@z47.com
- [ ] Evaluate `anthropics/knowledge-work-plugins` GitHub repo for relevant templates
- [ ] Research Attio API documentation for custom MCP feasibility
