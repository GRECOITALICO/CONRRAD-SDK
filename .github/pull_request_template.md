## Asset Change Declaration

Every PR must declare institutional impact.

### Asset(s) changed
- [ ] Asset ID: `SDK._____._____`
- [ ] Domain MANIFEST updated: `conrrad_sdk/___/MANIFEST.yaml`
- [ ] Registry updated: `assets/registry/domains/___.yaml`

### Five questions
| Question | Answer |
|----------|--------|
| Who am I? (asset_id) | |
| Why do I exist? (purpose) | |
| Who governs me? | |
| Who consumes me? | |
| What replaces me if retired? | |

### ADR / contracts
- [ ] ADR reference: ADR-___
- [ ] Public API index updated (if exported symbol changed)
- [ ] Tests added/updated

### Gate checklist
- [ ] `python scripts/institutional/run_institutional_gates.py --root .`
- [ ] Institutional Score ≥ 95 (`run_institutional_score.py`)

### Semantic note
Forbidden in active paths: `kernell`, `kap`, `legacy`, `prototype`, `draft`, `temp`, `backup`.
