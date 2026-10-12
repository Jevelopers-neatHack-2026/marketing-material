#!/usr/bin/env python3
"""Recover the pinned r09 adapter in an isolated checkout, without pushing.

Retain the actual failed recipe parse, repair only its quoted prose, then run
all inherited integrity, test, historical-byte and reproduction gates. Source
owners, approvals, media, and external submission are deliberately untouched.
"""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ADAPTER_PIN = '15fb1f5ed336cf00562619582b80ed4b9e6bc466'
ADAPTER_PATH = '.github/diagnostics/mm30_package_adapter.py'
ADAPTER_SHA256 = 'b7bc1a2818c7909afa0a62b63a8a96ee08fa4d4243e29f0cc338cd9abbc08c18'
BOUNDARY = "module = ast.parse(recipe, filename=PIN + ':' + PATH)\n"
TEST_PATH = 'tests/test_current_handoff_status.py'
TARGET = 'integration/mm07-package-recovery-20261012'

TESTS = r'''"""Offline handoff regression tests; no recording or submission execution."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ('demo/human-recording-runbook.md', 'demo/recording-checklist.md', 'docs/collateral-handoff.md')
CLOSED = '## Submission window status — closed'
AMENDMENT = '## Latest producer amendment — 01c65ae'


def section(text, heading):
    if heading not in text:
        return ''
    return text.split(heading, 1)[1].split('\n## ', 1)[0]


class CurrentHandoffStatusTests(unittest.TestCase):
    def test_closed_window_is_not_an_entry_or_deadline_receipt(self):
        for path in DOCUMENTS:
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding='utf-8')
                body = section(text, CLOSED)
                for phrase in ('Submissions closed', 'https://neatlogs.com/hackathon',
                               'not a Discord cutoff confirmation', 'not proof of a submitted entry',
                               'organizer-authorized late-entry exception',
                               'CANCELLED_USER_REQUEST_NO_RESTART'):
                    self.assertIn(phrase, body)
                self.assertLess(text.index(CLOSED), text.index(AMENDMENT))

    def test_newer_opening_keeps_two_turns_and_source_attribution(self):
        for path in DOCUMENTS:
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding='utf-8')
                body = section(text, AMENDMENT)
                for phrase in ('2026-10-12T18:06:34Z', '6129852860', '01c65ae',
                               '/make', 'two separate turns', '17 OCT',
                               'Generate art only once', 'not a new marketing runtime measurement',
                               'not a completed recording'):
                    self.assertIn(phrase, body)
                self.assertIn('6129152479', text)
                self.assertIn('CFO-R2-001', text)

    def test_organizer_availability_has_no_fabricated_completion(self):
        data = json.loads((ROOT / 'review/official-format-sources.json').read_text())
        current = data.get('availabilitySnapshot', {})
        self.assertEqual(current.get('status'), 'submissions_closed')
        self.assertEqual(current.get('checkedAt'), '2026-10-12 UTC')
        self.assertEqual(current.get('url'), 'https://neatlogs.com/hackathon')
        self.assertEqual(current.get('observedText'), 'Submissions closed')
        self.assertIsNone(current.get('lateEntryException'))
        self.assertIsNone(current.get('submittedEntryEvidence'))
        self.assertFalse(current.get('interactiveFormExecuted', True))
        self.assertEqual(data['currentSubmissionProcedureSourceId'], 'OFFICIAL-NEATHACK-SUBMISSION-20261012')

    def test_availability_does_not_replace_historical_format_observations(self):
        data = json.loads((ROOT / 'review/official-format-sources.json').read_text())
        self.assertIn('availabilitySnapshot', data)
        self.assertEqual(len(data['sources']), 4)
        self.assertEqual(data['sources'][-1]['sourceId'], data['currentSubmissionProcedureSourceId'])
        rules = data['sources'][-1]['observedRequirements']
        self.assertIsNone(rules['confirmedFinalCutoff']['value'])
        self.assertIsNone(rules['completionReceipts']['postedEntryUrl'])
        self.assertIsNone(rules['completionReceipts']['finalFormAcknowledgement'])
        self.assertEqual(rules['officialQuotePost']['targetReadHttpStatus'], 403)

    def test_frozen_narration_is_not_rewritten(self):
        self.assertEqual(hashlib.sha256((ROOT / 'demo/narration.md').read_bytes()).hexdigest(),
                         '818dcf3f2796bd2a29a2f3597d2a0fcc36b36fd7e87e50454af94616058e5cf6')

    def test_unescaped_generated_prose_is_rejected(self):
        with self.assertRaises(SyntaxError):
            ast.parse("value = 'This is the producer's human instruction.'")

    def test_safe_literal_roundtrip_handles_apostrophes(self):
        # Synthetic negative/recovery control; the actual pinned recipe parse is
        # separately retained in the native integration run, not simulated here.
        for value in ("producer's instruction", 'quoted "text"', 'new\nline'):
            tree = ast.parse('value = ' + repr(value))
            self.assertEqual(ast.literal_eval(tree.body[0].value), value)


if __name__ == '__main__':
    unittest.main()
'''

NOTICE = '''
## Submission window status — closed

On 2026-10-12 UTC, after the published 18:25 UTC window, the [public organizer page](https://neatlogs.com/hackathon) displayed **Submissions closed**. This is an availability observation, not a Discord cutoff confirmation and not proof of a submitted entry. Earlier GO instructions, recording packs and website times below are dated history, not a current instruction to record, spend, publish or submit.

Before any external submission work resumes, the authorized human submitter must provide an **organizer-authorized late-entry exception** with its scope and deadline. For an entry already completed, obtain its actual public post URL and a separate sanitized final form acknowledgement; absent receipts remain unknown, not evidence that nobody submitted. Do not backdate commits, recordings or eligibility claims. The final media, owner review, rights, exact claims and submission receipts remain separate prerequisites. Agent capture stays `CANCELLED_USER_REQUEST_NO_RESTART`; this note authorizes no provider use, recording, upload, publication or form action.

## Latest producer amendment — 01c65ae

At **2026-10-12T18:06:34Z**, [the producer amended the recording pack](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6129852860), reporting health commit `01c65ae` and the #104 landing page at `/`, with the paste box under the hero, Try the studio and Make yours. The alternative `/make` was reported unchanged. This is the producer observation, **not a new marketing runtime measurement** and **not a completed recording**. The earlier [17:21:38 UTC GO for `6daafba`](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6129152479) remains a historical take-specific instruction, not the latest opening.

The producer retained **two separate turns** because #100 and #112 were not live in that observation: first correct the date and Apply, visually check **17 OCT**, then request moodier art and Apply. **Generate art only once** under the human contributor's existing authorization; this document supplies none. Keep the same-session timestamp/Neatlogs handoff, Entire evidence limits, guarded CFO workbook and hypothetical forecast labels, including `CFO-R2-001`. A person already mid-take was not instructed to restart; the producer allowed changing only the opening. These are preserved human instructions, not execution, fixed-defect, timing, provider-cost, approval or submission evidence. The closed-window notice above governs current external-action readiness.

'''


def once(text: str, before: str, after: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError('Pinned recipe context changed: %r (%d)' % (before[:100], count))
    return text.replace(before, after, 1)


def main() -> None:
    raw = subprocess.check_output(['git', 'show', ADAPTER_PIN + ':' + ADAPTER_PATH])
    assert hashlib.sha256(raw).hexdigest() == ADAPTER_SHA256, 'Adapter bytes changed'
    adapter = raw.decode('utf-8')
    assert adapter.count(BOUNDARY) == 1
    prefix, suffix = adapter.split(BOUNDARY, 1)
    context = {'__name__': '__main__'}
    # Prefix reads only pinned Git objects and assembles source strings.
    exec(compile(prefix, '<pinned-adapter-prefix>', 'exec'), context)
    broken = context['recipe']
    try:
        ast.parse(broken)
    except SyntaxError as error:
        assert "producer's human instruction" in (error.text or ''), error
        print('RETAINED_BASELINE_PARSE_FAILURE', error.msg, 'line', error.lineno, flush=True)
    else:
        raise AssertionError('Expected original run 38286181903 parse failure was not reproduced')
    repaired = once(broken, "producer's human instruction", 'human instruction reported by the producer')
    ast.parse(repaired)
    print('REPAIRED_PINNED_RECIPE_SYNTAX_PASS', hashlib.sha256(repaired.encode()).hexdigest(), flush=True)

    # Register the new source test using the existing registry procedure.
    repaired = once(repaired,
        "'tests/test_producer_go_handoff.py',\n}",
        "'tests/test_producer_go_handoff.py', '" + TEST_PATH + "',\n}")
    anchor = "new_record('tests/test_producer_go_handoff.py', 'tests/test_narrative_handoff.py', 'Register current dated producer GO regression tests')"
    repaired = once(repaired, anchor, anchor + "\nnew_record('" + TEST_PATH + "', 'tests/test_narrative_handoff.py', 'Register offline current-status and generated-literal negative/recovery checks')")
    repaired = once(repaired,
        "'pullRequest': f'https://github.com/{REPO}/pull/30',",
        "'predecessorPullRequest': f'https://github.com/{REPO}/pull/30',\n    'integrationBranch': '" + TARGET + "',")
    repaired = once(repaired, 'dump(SPEC, spec)\n',
        "for selected in spec['assets']:\n"
        "    if selected['assetId'] in {'LAUNCH-X-COPY-001', 'DEMO-HUMAN-RECORDING-RUNBOOK-001'}:\n"
        "        selected['limitations'].append('The producer amended the opening at 18:06:34 UTC to reported 01c65ae; retain the two-turn workaround. The organizer page subsequently displayed Submissions closed. No prior-entry receipt or late-entry exception is supplied. Historical GO and procedure are not present authorization; capture remains cancelled.')\n"
        'dump(SPEC, spec)\n')

    baseline = "\n(ROOT / " + repr(TEST_PATH) + ").write_text(" + repr(TESTS) + ", encoding='utf-8')\n"
    baseline += "command('current-status-baseline', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_current_handoff_status.py', '-v'], expected=1)\n"
    baseline += "baseline_output = (LOGS / 'current-status-baseline.log').read_text()\nassert 'FAILED (failures=' in baseline_output and 'ERROR:' not in baseline_output, 'Unexpected baseline error instead of source regression'\n"
    updates = "\nnotice = " + repr(NOTICE) + "\n"
    updates += "for name in ('demo/human-recording-runbook.md', 'demo/recording-checklist.md', 'docs/collateral-handoff.md'):\n    document = (ROOT / name).read_text(encoding='utf-8')\n    title, rest = document.split('\\n', 1)\n    assert '## Submission window status — closed' not in document\n    (ROOT / name).write_text(title + '\\n' + notice + rest, encoding='utf-8')\n"
    updates += "formats = load('review/official-format-sources.json')\nassert 'availabilitySnapshot' not in formats\nformats['availabilitySnapshot'] = {'sourceId': 'OFFICIAL-NEATHACK-AVAILABILITY-20261012-CLOSED', 'url': 'https://neatlogs.com/hackathon', 'checkedAt': '2026-10-12 UTC', 'status': 'submissions_closed', 'observedText': 'Submissions closed', 'lateEntryException': None, 'submittedEntryEvidence': None, 'interactiveFormExecuted': False, 'scope': 'Public-page availability observation after the displayed 18:25 UTC window; not Discord confirmation, actual entry evidence or permission. Prior format observations are unchanged.'}\ndump('review/official-format-sources.json', formats)\n"
    updates += "command('current-status-corrected', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_current_handoff_status.py', '-v'])\n"
    context['recipe'] = repaired
    context['source_updates'] = baseline + context['source_updates'] + updates
    ast.parse(context['source_updates'])
    ast.parse(context['recipe'])
    if '--preflight' in sys.argv:
        print('ALL_GENERATED_SOURCE_PREFLIGHT_PASS_NO_MUTATION', flush=True)
        return
    # The unchanged inherited adapter suffix assembles the recipe AST and runs
    # its complete gates. The recipe cannot push or approve anything.
    exec(compile(BOUNDARY + suffix, '<pinned-adapter-recovered>', 'exec'), context)


if __name__ == '__main__':
    main()
