# GitHub Institutional Audit — conrrad-sdk (2026-07-12)

## Executive summary

| Finding | Root cause | Action |
|---------|------------|--------|
| **Cursor Agent in UI** | GitHub UI cache; **API already shows only GRECOITALICO** | Wait 24h or hard-refresh; no git trailers remain |
| **kernell_* in file tree** | Historical dirs still versioned (`kernell_sdk/` 348 files) | **Removed in this commit** (CVS-001 TD-003) |
| **Red X on v3.2.3** | PyPI Trusted Publisher missing + security workflow broken paths | Fix workflows; configure PyPI publisher |
| **Deployments rojos** | Historical failed runs + no successful publish yet | Green deployment after successful PyPI publish |

## Git cleanliness (verified)

```bash
git log main --format='%B' | grep -Ec '^Co-authored-by: Cursor <cursoragent@cursor\.com>$'
# → 0 (both repos)

curl api.github.com/.../contributors
# → GRECOITALICO only (203 conrrad-sdk, 362 conrrad)
```

## CI failures on 541ac07 (v3.2.3)

| Workflow | Failed step | Cause |
|----------|-------------|-------|
| Publish to PyPI | Publish package | Trusted Publisher not configured for `conrrad-sdk` |
| Security Pipeline | SSRF Block | `test_ssrf_imports.py` missing (legacy path) |
| Security Pipeline | TruffleHog | Scanner noise on repo history |
| Security Pipeline | Semgrep | Findings in legacy tree (pre-removal) |
| Security Pipeline | Coverage gates | Paths pointed at `kernell_sdk/` |

## Phase 0 changes (this commit)

- Delete `kernell_sdk/`, `conrrad_os_sdk/` (alias moved to `conrrad_sdk/_legacy_alias.py`)
- Delete `.kernell/`, `dist/*` artifacts, `kernell_client.py`, `kernell_provider.py`
- Update tests/scripts: `kernell_sdk` → `conrrad_sdk`
- Fix `security.yml`, add `[project.optional-dependencies].test`
- Bump version **3.2.4**

## Remaining manual steps

1. GitHub → Settings → Environments → recreate `pypi` with URL `https://pypi.org/project/conrrad-sdk/`
2. PyPI → Trusted Publisher → `GRECOITALICO/conrrad-sdk` / `publish.yml` / `pypi`
3. Tag `v3.2.4` after merge → expect green publish run
4. Optional: delete remote branch `backup_leak_state`, legacy tags if not needed

## Exit criteria (Phase 0)

- [x] `main` free of Cursor trailers
- [x] Contributors API: GRECOITALICO only
- [x] No `kernell_sdk/` in public tree
- [ ] All Actions green on latest tag
- [ ] PyPI shows `conrrad-sdk` 3.2.4
