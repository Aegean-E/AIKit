# Project Repository Backlog

Projects left out of the 2026-10-26 normalization pass: capitalized GitHub names, curated topics,
descriptions within GitHub's 350-character limit, and new versions under the Aegean 1.1
licenses. A project qualified only with a clean working tree and no open ledger task. Each one
below gets the same pass once its in-flight work is committed or reset.

| Project | Why it was skipped | Pass still needed |
|---|---|---|
| `MemoryReconstruction` | 163 uncommitted files; open task `living-sanctuary` | topics, description, license |
| `voidfarer` | 4 uncommitted files; open task `postpush-polish-verify` | rename, topics, description, license |
| `fluid-universe` | open task `z3-koide-core` | rename, topics, description, license |
| `ui-sandbox` | open task `ui-sandbox-polish` | rename, topics, description, license |
| `AegeanWorks` | uncommitted `docs/styles.css` | topics, description |

## Follow-ups found during the pass

- `licenses/CATALOG.md` links to `aegean-licensing/blob/main/...`, but that repository's
  default branch is `master`, so those links return 404. Either rewrite them to `blob/master`
  (GitHub redirects that path if the branch is renamed later) or rename the branch to `main`.
- `python aikit.py license --help` still describes `--set` as AL-1.0, AGL-1.0 and ASL-1.0;
  `apply_license_kind` writes the 1.1 texts.
