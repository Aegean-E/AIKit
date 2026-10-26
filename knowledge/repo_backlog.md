# Project Repository Backlog

Projects left out of the 2026-10-26 normalization pass: capitalized GitHub names, curated topics,
descriptions within GitHub's 350-character limit, and new versions under the Aegean 1.1
licenses. A project qualified only with a clean working tree and no open ledger task. Each one
below gets the same pass once its in-flight work is committed or reset. AegeanWorks makes no
release under AGPL-3.0, so the first three still carry an AGPL LICENSE that the pass replaces.

| Project | Why it was skipped | Pass still needed |
|---|---|---|
| `MemoryReconstruction` | 163 uncommitted files; open task `living-sanctuary` | topics (drop `agpl`), description, license |
| `voidfarer` | 8 uncommitted files; open task `postpush-polish-verify` | rename, topics (drop `agpl`), description, license |
| `fluid-universe` | 56 uncommitted files, 1 unpushed commit; open task `z3-koide-core` | rename, topics, description, license |
| `AegeanWorks` | uncommitted `docs/styles.css` | none beyond committing that change |

`ui-sandbox` (now `UI-Sandbox`) finished its task and completed the pass. `idea-catcher` is a
new restricted project with no GitHub repository and is out of scope.

## Follow-ups found during the pass

- `licenses/CATALOG.md` links to `aegean-licensing/blob/main/...`, but that repository's
  default branch is `master`, so those links return 404. Either rewrite them to `blob/master`
  (GitHub redirects that path if the branch is renamed later) or rename the branch to `main`.
- `python aikit.py license --help` still describes `--set` as AL-1.0, AGL-1.0 and ASL-1.0;
  `apply_license_kind` writes the 1.1 texts.
- `_licensed_readme` in `scripts/project_license.py` rewrites a commented `LICENSE` tree line with
  the template's trailing newline, leaving a blank line inside the README tree (after `ASSETS.md`
  for games and science). The pass removed those lines by hand in every project it touched.
- `apply_license_kind` adds a `## 📜 License` section beside an existing differently named
  License heading instead of replacing it; seven READMEs had two License sections.
- `extract_readme_description` in `scripts/project_publish.py` does not strip a UTF-8 byte-order
  mark, so a README that starts with one never finds its title and `publish` sends a later block
  (a table, for `obezite-mekanizma-projesi`) as the description. That README's mark was removed.
- `publish` takes the README's first paragraph and cuts it at 350 characters with "..."; aldervale,
  cyberpulse, NeuroOptic and NobetWizard had a first paragraph that was too long, empty or a URL,
  and were rewritten so the paragraph is one complete description.
- The Aegean-Licensing policy drafts still tell a maintainer to create a `vX.Y.Z-agpl` tag
  (`policies/PORTFOLIO-MIGRATION-PLAN.md`, step 2); the license texts keep their non-retroactivity
  and AGPL-incompatibility clauses, which protect the licensor and stay until counsel review.
