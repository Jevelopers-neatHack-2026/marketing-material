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
recipe = replace_once(recipe,
    "archive = f'release/{VERSION}/history/manifest-{old_manifest_digest}.json'",
    "archive = f'release/{VERSION}/history/manifest-{old_manifest_digest[:16]}.json'")
recipe = replace_once(recipe, "    SPEC,\n}", "    SPEC, 'tests/test_recording_handoff_review.py', 'tests/test_producer_go_handoff.py',\n}")
# A recorded null is an existing exclusion, not permission to erase a digest.
# Non-null inventory values follow the existing exact-digest path below.
recipe = replace_once(recipe,
    "    if path in {INV, PROV, 'messaging/claims.json'}:\n        assert row['sha256'] is None\n        continue\n",
    "    if path in {INV, PROV, 'messaging/claims.json'}:\n        print('RECORDED_CHECKSUM_POLICY', path, row.get('sha256'), flush=True)\n        if row.get('sha256') is None:\n            continue\n")
recipe = replace_once(recipe,
    "new_record('tests/test_announcement_submission.py', 'tests/test_narrative_handoff.py', 'Register offline announcement and consumer regression tests')",
    "new_record('tests/test_announcement_submission.py', 'tests/test_narrative_handoff.py', 'Register inherited PR28 announcement regression tests')\nnew_record('tests/test_recording_handoff_review.py', 'tests/test_narrative_handoff.py', 'Register PR30 companion and exact frozen-input regression tests')\nnew_record('tests/test_producer_go_handoff.py', 'tests/test_narrative_handoff.py', 'Register current dated producer GO regression tests')")
recipe = recipe.replace("'pullRequest': f'https://github.com/{REPO}/pull/28'", "'pullRequest': f'https://github.com/{REPO}/pull/30'")
# Keep inherited identity/history while accurately naming this combined operation.
recipe = recipe.replace('Current r09 submission-source/integration correction by GPT-6 Astra Pro;', 'Current combined PR27/28/30 r09 integration by GPT-6 Astra Pro;')
recipe = recipe.replace('Current correction: GPT-6 Astra Pro, source-only;', 'Current combined PR27/28/30 integration: GPT-6 Astra Pro, source-only;')

recipe = replace_once(recipe,
    "The later owner-selected landing + StudioStart/five-edition opening is a conditional human instruction, not deployed-build or recording evidence. The final take, exact owner review and separate submission receipts remain pending; agent capture stays cancelled.",
    "The dated producer GO at issuecomment-6129152479 selects the reported live 6daafba build without waiting for #104 or #112. This is the producer's human instruction, not a new marketing runtime measurement or completed recording. The final take, exact media/claim review and distinct submission receipts remain pending; agent capture stays cancelled.")

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

# The public producer GO supersedes the older intended opening and legacy fallback.
go = ('\n## Current producer GO — 6daafba\n\n'
    'At **2026-10-12T17:21:38Z**, the [producer reported `/api/health` commit `6daafba` and issued GO for the human take](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6129152479). This is the producer\'s observation, not a new marketing runtime measurement. It selects the deployed #96 pack with the existing home paste box, agent actions, Tear off, wall and Download. **Do not wait for #104 or #112**: the producer says the new landing and checkout changes are not in this deployed take. This selected pack supersedes both the earlier intended landing/StudioStart opening and the no-health-commit legacy fallback for this take. Earlier source pins, proposed allocations and fallback notes below are historical, not additional recording gates.\n\n'
    'This is a human recording GO, **not a completed recording**, final media review, new public-claim approval, Finance waiver, publication or submitted entry. The human contributors retain the owner\'s roles and existing authorizations; this note gives **no new provider authorization** or spending authority. Agent capture stays `CANCELLED_USER_REQUEST_NO_RESTART`; no agent executes the pack. If the observed build changes, return the discrepancy to the producer rather than mix packs or invent a deployed revision.\n\n')
steps = ('### Selected human pack (producer instructions, not execution evidence)\n\n'
    'Use the exact cleared example and source link in the producer receipt. Before recording, use the producer-selected browser setup, turn on sound, and resolve the analytics consent card; do not expose private account data or notifications.\n\n'
    'The proposed sequence is home paste box (0:00–0:10), paste/printer/source marks (0:10–0:30), two style swipes (0:30–0:45), and the agent segment (0:45–1:20). Use **two separate turns** because the producer says #100 is not deployed: first correct the date, Apply, and visually check **17 OCT**; only then request the moodier art and Apply. **Generate art only once** under the human\'s existing authorization, and show the agent reply. Do not combine date correction with the art request or portray this workaround as a fixed product defect.\n\n'
    'Then Tear off, pin to the wall, reopen the lamp and Download (the producer allocates 1:30–1:50). Inspect the PNG for the art; the producer permits retrying the download if the art is blank, not generating more art. Show the session\'s Neatlogs evidence, then Entire and CFO.ai (1:50–2:42), retaining the source limits, guarded workbook hash and hypothetical forecast labels below. Close on the wall/URL (2:42–2:50). These are proposed edit allocations, **not measured performance** or a timed continuous-take receipt. Do not promote the producer\'s informal latency estimates to measured marketing claims.\n\n'
    'After the human take, record its **session timestamp** for the producer to retrieve the matching Neatlogs trace IDs; availability is not a claim that retrieval or review has happened. Perform final media review, captions/transcript and redaction checks and measure the selected export at no more than **180 seconds**. The quote-post with attached video and all three tags plus the leader\'s completed form remain separate later human actions; record both sanitized completion receipts.\n\n')
for path in ('demo/human-recording-runbook.md', 'demo/recording-checklist.md', 'docs/collateral-handoff.md'):
    detail = steps if path == 'demo/human-recording-runbook.md' else 'Follow the selected human sequence and session-evidence instructions in [the current recording runbook](%s#current-producer-go--6daafba), then perform final media review and the separate post/form handoff.\n\n' % ('human-recording-runbook.md' if path.startswith('demo/') else '../demo/human-recording-runbook.md')
    replace(path, '## Canonical evidence acceptance versus marketing clearance', go + detail + '## Canonical evidence acceptance versus marketing clearance')
replace('demo/human-recording-runbook.md',
    '**Must be confirmed before recording (all open blockers):**',
    '**Confirmation ledger:** the producer\'s selected `6daafba` build and GO are recorded above. The earlier selection/rehearsal placeholders below are superseded for that take; do not require another deployment or wait for #104/#112. The remaining human roles, cleared input, exact public copy, final media and submission receipts are not established by the GO.')
replace('demo/human-recording-runbook.md',
    '1. The product owner/producer selects the new-build or legacy fallback recording pack in section 6 and records the deployed URL, health observation and exact commit when reported. An absent health commit stays unidentified; never substitute a repository head for the deployed revision.',
    '1. Use the producer-selected `6daafba` pack and record the take\'s observed URL/health state. The producer GO supplies the build observation above; do not substitute a newer repository head or the previous unidentified fallback. Report any changed build to the producer.')
replace('demo/human-recording-runbook.md',
    '2. A human producer rehearsal and go/no-go for the selected build and pack. The legacy fallback is an explicitly separate producer path, not proof of the new-build controls. An unidentified build cannot satisfy the exact-source acceptance requirement; keep that limitation and final claim/release review open.',
    '2. The dated producer GO above resolves the earlier missing go/no-go for this selected pack. It is not an executed final take, a teammate review of this document, or final claim/release acceptance; preserve those remaining checks.')
replace('demo/human-recording-runbook.md',
    '**Producer pack takes precedence over the legacy timing table below.**',
    '**The current `6daafba` producer GO above takes precedence over this historical planning section and legacy timing table.** Do not use the earlier intended #104 opening or no-commit fallback for that selected take.')

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
