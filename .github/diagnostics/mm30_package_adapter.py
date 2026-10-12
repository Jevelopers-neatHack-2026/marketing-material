#!/usr/bin/env python3
"""Adapt a pinned public r09 recipe to merged PR27/28/30 source in isolation.

No network, credentials, push, capture, rendering, or approval actions here.
The separate workflow owns the conditional fast-forward push. Author inspection
is not an independent review. All inherited check failures remain failures.
"""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import re
import subprocess

PIN = '3cb20950ddb13412e3e642e6dac50e5fa930321e'
PATH = '.github/diagnostics/mm_submission_refresh.py'
BLOB = '0efebcabfa55871fa4e5fb4fa93b772061ae6bb4'
ROOT = Path.cwd().resolve()
combined = os.environ['MM_COMBINED_SOURCE']
assert re.fullmatch(r'[0-9a-f]{40}', combined)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == combined
raw = subprocess.check_output(['git', 'show', PIN + ':' + PATH])
assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == BLOB
recipe = raw.decode('utf-8')

def replace_once(text: str, before: str, after: str) -> str:
    assert text.count(before) == 1, ('Recipe context changed', before[:100])
    return text.replace(before, after, 1)

recipe = replace_once(recipe, "BASE = '80ed73f3b86c32b1cc0139174cad6f390afd39c4'", "BASE = os.environ['MM_COMBINED_SOURCE']")
recipe = replace_once(recipe, "    SPEC,\n}", "    SPEC, 'tests/test_recording_handoff_review.py',\n}")
# A recorded null is an existing exclusion, not permission to erase a digest.
# Non-null inventory values follow the existing exact-digest path below.
recipe = replace_once(recipe,
    "    if path in {INV, PROV, 'messaging/claims.json'}:\n        assert row['sha256'] is None\n        continue\n",
    "    if path in {INV, PROV, 'messaging/claims.json'}:\n        print('RECORDED_CHECKSUM_POLICY', path, row.get('sha256'), flush=True)\n        if row.get('sha256') is None:\n            continue\n")
recipe = replace_once(recipe,
    "new_record('tests/test_announcement_submission.py', 'tests/test_narrative_handoff.py', 'Register offline announcement and consumer regression tests')",
    "new_record('tests/test_announcement_submission.py', 'tests/test_narrative_handoff.py', 'Register inherited PR28 announcement regression tests')\nnew_record('tests/test_recording_handoff_review.py', 'tests/test_narrative_handoff.py', 'Register PR30 companion and exact frozen-input regression tests')")
recipe = recipe.replace("'pullRequest': f'https://github.com/{REPO}/pull/28'", "'pullRequest': f'https://github.com/{REPO}/pull/30'")
# Keep inherited identity/history while accurately naming this combined operation.
recipe = recipe.replace('Current r09 submission-source/integration correction by GPT-6 Astra Pro;', 'Current combined PR27/28/30 r09 integration by GPT-6 Astra Pro;')
recipe = recipe.replace('Current correction: GPT-6 Astra Pro, source-only;', 'Current combined PR27/28/30 integration: GPT-6 Astra Pro, source-only;')

# These additions are operational text, never new narration or an approval.
source_updates = r'''
# The existing PR30 guides already reconcile current instructions and the producer
# fallback. Do not replace them with the older recipe's title-card/new-build mix.
assert digest('demo/narration.md') == '818dcf3f2796bd2a29a2f3597d2a0fcc36b36fd7e87e50454af94616058e5cf6'
replace('demo/recording-checklist.md', 'rights,finance, and destination authority.', 'rights, finance, and destination authority.')
replace('demo/recording-checklist.md',
    'Still unknown: submitter name, demo URL, official post URL, Discord cutoff and posted-entry URL.',
    'The organizer submission page supplies ' + POST + '; its X target returned HTTP 403 in the recorded observation, so human target and attachment verification remain pending. Still unknown: human submitter and form leader, final demo URL, Discord cutoff, posted-entry URL and final form acknowledgement.')
notice = ('\n## Canonical evidence acceptance versus marketing clearance\n\n'
    'The [integration-evals master checklist at `89141b4e9237d7cc1548254b99dbd0f01589eaa4`](https://github.com/Jevelopers-neatHack-2026/integration-evals/blob/89141b4e9237d7cc1548254b99dbd0f01589eaa4/planning/acceptance-checklist.md), read on 2026-10-12, records SPN-01, SPN-02 and SPN-03 as verified and owner-accepted within their stated evidence limits. The local `PENDING` labels and historical rehearsal observations in this guide describe marketing claim/destination/media review, not a reversal of that canonical acceptance. Evidence acceptance is not publication permission or proof that the final video and submission are complete. Preserve exact source scopes, the hypothetical CFO forecast labels, the guarded reviewer workbook and the unresolved generic-export limitation `CFO-R2-001`; no Finance waiver is supplied here.\n\n')
for path, heading in [
    ('demo/human-recording-runbook.md', '## 3. Known versus must-confirm before the take'),
    ('demo/recording-checklist.md', '## Final recording blockers'),
    ('docs/collateral-handoff.md', '## Current disposition'),
]:
    replace(path, heading, notice + heading)
replace('demo/human-recording-runbook.md',
    '## 5. Recovery moment',
    'The [producer clarification on checkout #112](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6128880860) explicitly says that checkout change is outside the video script and does not block the take. Do not add it as a recording prerequisite. The selected producer pack and actual behavior still govern the take.\n\n## 5. Recovery moment')
# The observed locator and the authentic human completion receipts stay distinct.
replace('docs/collateral-handoff.md',
    '## Format and external-use boundary\n',
    '## Format and external-use boundary\n\nThe organizer-supplied launch-post locator is ' + POST + '. The recorded X read returned HTTP 403, not verification of its contents or accessibility; the authorized human must verify the target and actual video attachment. This locator is not the final posted-entry URL.\n')
module = ROOT / 'tests/test_recording_handoff_review.py'
content = module.read_text(encoding='utf-8')
anchor = "\n\nif __name__ == '__main__':\n"
assert content.count(anchor) == 1
extra = "\n\nclass CanonicalAcceptanceBoundaryChecks(unittest.TestCase):\n    def test_local_pending_does_not_reverse_canonical_owner_acceptance(self):\n        for name in DOCUMENT_SECTIONS:\n            with self.subTest(document=name):\n                body = section((ROOT / name).read_text(encoding='utf-8'), 'Canonical evidence acceptance versus marketing clearance')\n                for value in ('89141b4e9237d7cc1548254b99dbd0f01589eaa4', 'SPN-01', 'SPN-02', 'SPN-03', 'owner-accepted', 'not publication permission', 'CFO-R2-001'):\n                    self.assertIn(value, body)\n"
module.write_text(content.replace(anchor, extra + anchor), encoding='utf-8')
'''
module = ast.parse(recipe, filename=PIN + ':' + PATH)
new_body = []
kept = []
skipped = []
inserted = 0
for node in module.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'extra_tests' for t in node.targets):
        # PR30's existing tests cover the newer producer fallback; do not add
        # old tests requiring an obsolete fixed opening to every possible take.
        continue
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if isinstance(call.func, ast.Name) and call.func.id == 'replace':
            path = call.args[0].value if isinstance(call.args[0], ast.Constant) else None
            before = call.args[1].value if isinstance(call.args[1], ast.Constant) else ''
            keep = path in ('README.md', 'launch/announcement-copy.md', 'launch/deliverable-briefs.md')
            keep |= path == 'docs/collateral-handoff.md' and ('r08-repository-' in before or before.startswith('Existing r01 package-copy'))
            keep |= path == 'demo/human-recording-runbook.md' and before.startswith('| Official neatlogs post URL |')
            if not keep:
                skipped.append((path, str(before)[:75]))
                continue
            kept.append(path)
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'spec' for t in node.targets):
        new_body.extend(ast.parse(source_updates).body)
        inserted += 1
    new_body.append(node)
assert inserted == 1, inserted
assert kept.count('README.md') == 3 and kept.count('docs/collateral-handoff.md') == 2
assert kept.count('demo/human-recording-runbook.md') == 1
assert kept.count('launch/announcement-copy.md') == 1 and kept.count('launch/deliverable-briefs.md') == 1
print('PINNED_RECIPE', PIN, BLOB, flush=True)
print('ADAPTED_SOURCE_CALLS_KEPT', kept, flush=True)
print('SUPERSEDED_SOURCE_CALLS_NOT_EXECUTED', skipped, flush=True)
module.body = new_body
ast.fix_missing_locations(module)
exec(compile(module, '<pinned-r09-recipe-adapted-for-pr30>', 'exec'), {'__name__': '__main__'})
