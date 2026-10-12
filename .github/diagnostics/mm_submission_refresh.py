#!/usr/bin/env python3
"""One-shot, guarded PR28 draft refresh. No providers, media rendering, or pushing.

Run only in the exact isolated source checkout. The separate workflow may push
successful commits to its one explicit owned branch; this script cannot push.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = '80ed73f3b86c32b1cc0139174cad6f390afd39c4'
REPO = 'Jevelopers-neatHack-2026/marketing-material'
VERSION = 'v0.1.0-rehearsal'
ROOT = Path.cwd().resolve()
INV = 'docs/collateral-inventory.json'
PROV = 'review/provenance.json'
SPEC = f'release/{VERSION}/package-spec.json'
MANIFEST = f'release/{VERSION}/manifest.json'
POST = 'https://x.com/bettersayAJ/status/2109639214723932495'
SOURCE_ID = 'OFFICIAL-NEATHACK-SUBMISSION-20261012'
CANCEL = 'CANCELLED_USER_REQUEST_NO_RESTART'
SOURCE_PATHS = {
    'README.md', 'launch/announcement-copy.md', 'launch/deliverable-briefs.md',
    'demo/human-recording-runbook.md', 'demo/recording-checklist.md',
    'docs/collateral-handoff.md', 'review/official-format-sources.json',
    'tests/test_announcement_submission.py', 'tests/test_submission_workflow.py',
    SPEC,
}
RUN = os.environ['GITHUB_RUN_ID']
WORKFLOW_SHA = os.environ['GITHUB_SHA']
RUN_URL = f'https://github.com/{REPO}/actions/runs/{RUN}'
LOGS = Path(os.environ['RUNNER_TEMP']) / 'mm-results'
LOGS.mkdir(exist_ok=True)


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def dump(path: str, value) -> None:
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def replace(path: str, before: str, after: str) -> None:
    content = (ROOT / path).read_text(encoding='utf-8')
    if content.count(before) != 1:
        raise RuntimeError(f'{path}: expected exactly one known source block, got {content.count(before)}')
    (ROOT / path).write_text(content.replace(before, after, 1), encoding='utf-8')


def commit(message: str) -> str:
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    subprocess.run(['git', '-c', 'user.name=github-actions[bot]', '-c',
                    'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                    'commit', '-m', message], cwd=ROOT, check=True)
    result = git('rev-parse', 'HEAD')
    print('CREATED_LOCAL_COMMIT', result, flush=True)
    return result


def command(name: str, args: list[str], expected: int = 0, cwd: Path = ROOT) -> int:
    print('COMMAND', name, json.dumps(args), 'cwd=', str(cwd), flush=True)
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, check=False)
    text = result.stdout
    (LOGS / (name + '.log')).write_text(text, encoding='utf-8')
    (LOGS / (name + '.exit')).write_text(str(result.returncode) + '\n')
    print(text, end='' if text.endswith('\n') else '\n', flush=True)
    print('RESULT', name, result.returncode, 'LOG_SHA256', hashlib.sha256(text.encode()).hexdigest(), flush=True)
    if result.returncode != expected:
        raise RuntimeError(f'{name}: expected exit {expected}, observed {result.returncode}')
    return result.returncode


def protected(row: dict) -> dict:
    fields = ('permission', 'publishability', 'reviewDate', 'reviewStatus',
              'reviewer', 'allowedDestinations', 'allowedModifications', 'consent',
              'attribution', 'expiry', 'blockers', 'redaction', 'reviewTrigger')
    return {field: copy.deepcopy(row.get(field)) for field in fields}


assert git('rev-parse', 'HEAD') == BASE, 'Source branch moved'
assert not git('status', '--porcelain'), 'Dirty checkout'
assert sys.version_info[:3] == (3, 9, 6), sys.version
import PIL
assert PIL.__version__ == '11.3.0', PIL.__version__
print('ENVIRONMENT', sys.version, PIL.__version__, flush=True)
original_inv, original_prov, original_spec = load(INV), load(PROV), load(SPEC)
assert original_spec['assetRevision'] == 'r08'
rights = {row['assetId']: protected(row) for row in original_prov['records']}
submission_scope = copy.deepcopy(original_inv['submissionScope'])
original_files = set(git('ls-files').splitlines())
old_release = {p: digest(p) for p in original_files if p.startswith('release/') and p not in {SPEC, MANIFEST}}
old_manifest_digest = digest(MANIFEST)
archive = f'release/{VERSION}/history/manifest-{old_manifest_digest}.json'
archive_existing = archive in original_files
if archive_existing:
    assert (ROOT / archive).read_bytes() == (ROOT / MANIFEST).read_bytes()
else:
    (ROOT / archive).write_bytes((ROOT / MANIFEST).read_bytes())

# Retain the original observations exactly; identify the newer submission record.
format_path = 'review/official-format-sources.json'
formats = load(format_path)
original_observations = copy.deepcopy(formats['sources'])
historical_hash = hashlib.sha256(json.dumps(original_observations, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
assert all(row['sourceId'] != SOURCE_ID for row in formats['sources'])
formats['checkedAt'] = '2026-10-12 UTC'
formats['currentSubmissionProcedureSourceId'] = SOURCE_ID
formats['historicalObservationNote'] = 'The three 2026-10-11 records are retained unchanged as dated observations. Their previously unknown launch locator is not the latest observation. Use currentSubmissionProcedureSourceId for the two-step submission procedure; this does not refresh or waive the historical five-facet repository acceptance or any approval.'
formats['sources'].append({
    'sourceId': SOURCE_ID, 'publisher': 'neatlogs',
    'title': 'Current public submission procedure and supplied launch locator',
    'url': 'https://neatlogs.com/submission', 'relatedUrl': 'https://neatlogs.com/hackathon',
    'checkedAt': '2026-10-12 UTC',
    'usedFor': ['Required sponsor tags', 'Separate public quote-post and completed leader form', 'Launch locator observed separately from human verification', 'Published window distinguished from authoritative Discord cutoff'],
    'observedRequirements': {
        'bothStepsRequired': True,
        'steps': ['public_quote_post_with_attached_final_demo', 'human_team_leader_completed_submission_form'],
        'requiredSponsorHandles': ['@neatlogs', '@EntireHQ', '@arithecfo'],
        'videoMaximumSeconds': 180,
        'officialQuotePost': {'url': POST, 'sourceLinkLabel': 'View launch post', 'status': 'locator_observed_target_not_verified', 'targetReadHttpStatus': 403, 'humanTargetAndAttachmentVerification': 'pending'},
        'form': {'url': 'https://neatlogs.com/submission', 'leader': 'pending', 'continueAction': 'saves_draft', 'finalAction': 'Submit project', 'completedSubmissionAcknowledgement': 'pending', 'inspectionScope': 'public_first_step_only_no_interactive_form_email_verification_draft_save_or_submission'},
        'websiteWindow': {'date': '2026-10-12', 'startUtc': '13:30', 'endUtc': '18:25', 'displayedIst': '19:00-23:55', 'status': 'website_schedule_not_discord_confirmation'},
        'confirmedFinalCutoff': {'value': None, 'status': 'pending_discord_confirmation'},
        'completionReceipts': {'postedEntryUrl': None, 'finalFormAcknowledgement': None, 'collection': 'after_the_take_and_actual_authorized_human_actions', 'redaction': 'confirmation_reference_and_timestamp_only_no_private_form_contents'},
    },
    'scopeNote': 'An observed organizer procedure is not sponsor-use evidence, a final movie, permission, a completed form or a submitted entry. The human roles, final media, exact claims, Finance, brand, rights and destination decisions remain separate. Agent capture remains ' + CANCEL + '; no agent posts, uploads or submits.'
})
assert formats['sources'][:-1] == original_observations
dump(format_path, formats)

replace('README.md', 'immutable current r08 asset copies with retained prior r01/r02/r03/r04/r05/r06/r07 copies', 'immutable current r09 asset copies with retained prior r01/r02/r03/r04/r05/r06/r07/r08 copies')
replace('README.md', 'There is no CI workflow; these run locally and make no network or paid-provider calls.', 'There is no CI workflow on the delivery branch; these checks run locally without network or paid-provider calls. Separate owned diagnostic-branch Actions runs also execute these offline checks in a pinned clean checkout; they are not release approval.')
replace('README.md', '## Checks\n', '## Checks\n\nAgent capture remains `CANCELLED_USER_REQUEST_NO_RESTART`. Do not execute the render recipes below without separate fresh authorization. This r09 change copies existing media bytes and refreshes text/package bindings; it does not render, record, upload or submit a demo.\n')

replace('demo/recording-checklist.md',
        '**Current result:** local silent rehearsal may be rendered at 150 seconds.',
        '**Current result:** the historical 150-second silent synthetic rehearsal exists; agent capture remains `CANCELLED_USER_REQUEST_NO_RESTART` and must not be restarted by this checklist.')
replace('demo/recording-checklist.md', '## Current rehearsal build\n', '## Historical rehearsal build recipe — not execution authorization\n\nThe following recipe documents the existing concept rehearsal. It is not permission to render again; agent capture remains cancelled. Preserve the existing video and receipt bytes.\n')
replace('demo/recording-checklist.md',
        '- **Submission details:** current organizer page, official X post URL, actual Discord cutoff, accountable submitter authorization and name, public demo URL, and supporting evidence links. Team, project, repository and business-plan values are known (wording review pending). Verify those values immediately before submission.',
        '- **Submission details:** verify the supplied official X locator and actual quote attachment, the latest Discord cutoff, accountable human X submitter authorization/name, separate authorized form leader, final public demo URL, supporting evidence and final composer count. Team, project, repository and business-plan values remain known draft fields with wording review pending. Both the public quote-post with attached final video and the leader’s completed form are required; Continue saves a draft, while Submit project is the final action. Completion receipts are collected after the take, not required to begin human recording.')
replace('demo/recording-checklist.md',
        '- **Entry fields:** Team Jevelopers, Project TicketStub, the public repository URL and the required business-plan URL are known (four `CLAIM-X-DEST-*` rows, wording review pending). Still unknown: submitter name, demo URL, official post URL, Discord cutoff and posted-entry URL.',
        '- **Entry fields:** Team Jevelopers, Project TicketStub, the public repository URL and required business-plan URL remain known draft fields (four `CLAIM-X-DEST-*` rows, wording review pending). The official submission page supplies ' + POST + '; the X target returned HTTP 403, so human target verification and the actual quote attachment remain pending. Unknown: human submitter and form leader, final demo URL, Discord cutoff, posted-entry URL and separate final form acknowledgement.')
replace('demo/recording-checklist.md', '## Final capture sequence\n', '## Final capture sequence\n\nFor authorized human teammates only. Agents remain cancelled and must not execute this sequence.\n')
replace('demo/recording-checklist.md',
        '6. Check the official submission post, Discord cutoff, and ordinary X post composer constraints again. No post, upload, or submission is part of this handoff.',
        '6. Recheck the official post, Discord cutoff and current X composer. The completed quote-post must retain `@neatlogs @EntireHQ @arithecfo` and attach the final approved video. The authorized human leader must also complete [the submission form](https://neatlogs.com/submission) through Submit project; a saved draft is not submission. After those actual human actions, record the public posted-entry URL and a separate redacted form confirmation reference/timestamp. Never include private form contents. No agent posts, uploads or submits.')
replace('demo/recording-checklist.md',
        '| Official post, cutoff, required links, submitter authority | `PENDING` | Current organizer/Discord information and confirmed fields |',
        '| Official post, cutoff, links, human X submitter and form leader | `PENDING` | Verify the supplied locator/attachment and latest Discord deadline; confirm roles and final fields; record distinct post and completed-form receipts after actual human actions |')

replace('demo/human-recording-runbook.md',
        '| Official neatlogs post URL | | **Unknown.** Recheck before submitting. |',
        '| Official neatlogs post URL | `' + POST + '` | **Locator observed** in the organizer submission page’s View launch post link on 2026-10-12 UTC. The target returned HTTP 403; public accessibility, contents and actual quote attachment remain unverified and need human confirmation. |')
replace('demo/human-recording-runbook.md',
        '| Style set | Current 5 editions versus 8 new SVG templates, undecided | [issue 22 comment 6118297805](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6118297805). The style count may be omitted until the owner confirms the deployed set. |',
        '| Style set and product slice | Owner-selected landing + StudioStart with five editions; no new SVG templates in this demo slice | [Owner decision, issue 22 comment 6127105138](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6127105138) supersedes the earlier undecided choice. This is selected scope, not deployed-build evidence. The producer must confirm the actual deployed set before a style count is shown or said. |')
replace('demo/human-recording-runbook.md',
        '3. The deployed style set, if any style count will be shown or said.',
        '3. That the deployed build actually matches the selected landing + StudioStart/five-edition scope, if any style count will be shown or said. Inspect the producer handoff for product PRs #96 and #104 and their current successors; a source PR or passing source test alone is not deployment or phone-QA evidence.')
replace('demo/human-recording-runbook.md',
        'Shot modes depend on the producer-confirmed deployed build. Until it is confirmed, shots 2 to 5 are placeholders and carry the mode "as the confirmed build reports".',
        'The later [owner-selected opening](https://github.com/Jevelopers-neatHack-2026/marketing-material/issues/22#issuecomment-6127105138) is hero 0:00–0:08, paste 0:08–0:12 and printer 0:12–0:30, followed by the readable result. It replaces the older title-card-first opening without changing the 170-second planning budget or the three sponsor segments. These timings are a plan, not a measured take. Shot modes depend on the producer-confirmed deployed build; until it is confirmed, product shots are conditional instructions and carry the mode "as the confirmed build reports".')
replace('demo/human-recording-runbook.md',
        '| 1 | 0:00–0:12 | Desktop | Title card: Team Jevelopers, Project TicketStub. | `PLANNED LIVE DEMO`, plus the confirmed build\'s mode | `CLAIM-RUNBOOK-ENTRY-FIELDS-001` (planned, pending; project name only, product availability unverified) |',
        '| 1 | 0:00–0:08 | Phone | **Landing hero:** open the confirmed deployed landing page. Keep the known team/project title values in the review notes/end card; do not invent a public capability caption. | confirmed build mode | Instruction only; no new product claim or availability approval |')
replace('demo/human-recording-runbook.md',
        '| 2 | 0:12–0:30 | Phone | **Input:** open the confirmed deployed URL, enter the cleared example. | build mode as reported | `CLAIM-PRODUCT-CAPABILITY-001` (pending-only wording) |',
        '| 2 | 0:08–0:12 | Phone | **Paste:** enter the cleared example in StudioStart on that exact build. | build mode as reported | `CLAIM-PRODUCT-CAPABILITY-001` (pending-only wording) |')
replace('demo/human-recording-runbook.md',
        '| 3 | 0:30–0:50 | Phone | **Research:** show the research result. | build mode as reported | same |',
        '| 3 | 0:12–0:50 | Phone | **Printer and result:** planned printer ritual 0:12–0:30, then show the readable research/result state through 0:50. Show only what the confirmed build actually does; no physical fulfillment is implied. | build mode as reported; `PREVIEW ONLY` where applicable | same pending-only limits |')
replace('demo/human-recording-runbook.md',
        'These are internal planning instructions, not an entry, permission to publish, or a completed submission.',
        'The website window observed on 2026-10-12 is 13:30–18:25 UTC (19:00–23:55 IST), not a Discord-confirmed cutoff. Only the public first-step form page was read; no interactive form flow, email verification, draft save or submission was performed. These are internal planning instructions, not an entry, permission to publish, or a completed submission.')

replace('docs/collateral-handoff.md',
        'demo-001-demo-recording-checklist-001-r08-repository-internal-review-text-en-us-rehearsal-recording-plan.md',
        'demo-001-demo-recording-checklist-001-r09-repository-internal-review-text-en-us-rehearsal-recording-plan.md')
replace('docs/collateral-handoff.md',
        'Existing r01 package-copy names remain immutable; the current rehearsal rebuild uses r08 after the human recording runbook wording was clarified (r02, r03, r04, r05, r06 and r07 copies are likewise retained; r07 remains the prior revision):',
        'Existing r01 package-copy names remain immutable; the current draft rebuild uses r09 for the reconciled human submission procedure, owner-selected opening and sponsor-tagged announcement (r02, r03, r04, r05, r06, r07 and r08 copies are likewise retained; r08 remains the prior revision). Existing media bytes are copied, not rendered or recorded again:')
replace('docs/collateral-handoff.md',
        'The official organizer page currently requires a public repository, supporting evidence, and a public X quote-post attaching the official post with team, submitter/name, project, repository, and demo link. It requires a demo of three minutes or less covering architecture, implementation, runtime, reasoning, and result for each of neatlogs, Entire, and cfo.ai; the final cutoff is announced on Discord. The checked record does not specify a video aspect ratio, file-size maximum, official post URL, or final cutoff. Refresh [neatHack\'s official page](https://neatlogs.com/hackathon) immediately before submission.',
        'The 2026-10-12 organizer observation requires both a public quote-post with the attached final demo and `@neatlogs @EntireHQ @arithecfo`, and the authorized human team leader’s completed [submission form](https://neatlogs.com/submission). Continue saves a draft; Submit project is the final action. Keep the posted-entry URL and redacted final form acknowledgement separate, and collect them after the take and actual authorized human actions. The supplied launch locator is ' + POST + '; its target returned HTTP 403, so human target/attachment verification remains pending. The published October 12 window is 13:30–18:25 UTC, not confirmation of the authoritative Discord cutoff.\n\nThe three-minute maximum and all three sponsors remain required. Preserve the repository’s separate architecture, implementation, runtime, reasoning and result requirements for each sponsor; that detailed five-facet wording was not reverified on the current organizer pages. No aspect ratio or video file-size limit is invented. The original 2026-10-11 observations remain unchanged in `review/official-format-sources.json`; its `currentSubmissionProcedureSourceId` selects the new observation. Agent capture remains `CANCELLED_USER_REQUEST_NO_RESTART`; these instructions authorize no agent recording, uploads, posts or submissions.')

replace('launch/announcement-copy.md',
        'Current source/package joins and exact wording review must be refreshed for this changed draft, including its required tags. Historical released or rehearsal copies are not updated in place. The handoff procedure does not change any claim, sponsor, Finance, brand, rights or release status.',
        'The r09 draft package binds this source and its required tags without changing historical rehearsal copies. Integrity binding does not supply the required exact wording, destination, rights or independent review. The handoff procedure does not change any claim, sponsor, Finance, brand, rights or release status.')
replace('launch/deliverable-briefs.md',
        'This changed source still requires exact claim/provenance joins, a new immutable package revision and independent review.',
        'The r09 draft package binds this source without replacing earlier revisions; exact owner wording, destination/rights and independent review remain pending. Package integrity is not approval.')

# New regression checks bind the unchanged historical observations and changed consumers.
test_path = 'tests/test_announcement_submission.py'
extra_tests = '''\n\nclass SubmissionConsumerConsistencyTests(unittest.TestCase):
    def test_latest_observation_preserves_historical_sources(self):
        import hashlib
        import json
        data = json.loads((ROOT / 'review/official-format-sources.json').read_text())
        self.assertEqual(data['currentSubmissionProcedureSourceId'], 'OFFICIAL-NEATHACK-SUBMISSION-20261012')
        current = [row for row in data['sources'] if row['sourceId'] == data['currentSubmissionProcedureSourceId']]
        self.assertEqual(len(current), 1)
        historical = [row for row in data['sources'] if row['sourceId'] != data['currentSubmissionProcedureSourceId']]
        self.assertEqual(hashlib.sha256(json.dumps(historical, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(), '__HISTORICAL_HASH__')
        rules = current[0]['observedRequirements']
        self.assertTrue(rules['bothStepsRequired'])
        self.assertEqual(rules['requiredSponsorHandles'], list(HANDLES))
        self.assertEqual(rules['steps'], ['public_quote_post_with_attached_final_demo', 'human_team_leader_completed_submission_form'])
        self.assertEqual(rules['officialQuotePost']['targetReadHttpStatus'], 403)
        self.assertEqual(rules['officialQuotePost']['humanTargetAndAttachmentVerification'], 'pending')
        self.assertIsNone(rules['confirmedFinalCutoff']['value'])
        self.assertIsNone(rules['completionReceipts']['postedEntryUrl'])
        self.assertIsNone(rules['completionReceipts']['finalFormAcknowledgement'])
        self.assertEqual(rules['form']['finalAction'], 'Submit project')
        self.assertEqual(rules['form']['completedSubmissionAcknowledgement'], 'pending')

    def test_checklist_and_receiver_require_both_steps_without_capture_restart(self):
        for relative in ('demo/recording-checklist.md', 'docs/collateral-handoff.md'):
            document = (ROOT / relative).read_text()
            with self.subTest(path=relative):
                for value in (*HANDLES, 'Submit project', 'form acknowledgement', 'CANCELLED_USER_REQUEST_NO_RESTART', '403'):
                    self.assertIn(value, document)
        checklist = (ROOT / 'demo/recording-checklist.md').read_text()
        self.assertIn('Historical rehearsal build recipe', checklist)
        self.assertNotIn('local silent rehearsal may be rendered', checklist)
        self.assertNotIn('Still unknown: submitter name, demo URL, official post URL', checklist)

    def test_human_opening_uses_owner_scope_without_claiming_a_deployed_result(self):
        document = (ROOT / 'demo/human-recording-runbook.md').read_text()
        self.assertIn('6127105138', document)
        self.assertIn('landing + StudioStart with five editions', document)
        self.assertIn('no new SVG templates', document)
        self.assertNotIn('Current 5 editions versus 8 new SVG templates, undecided', document)
        for value in ('hero 0:00–0:08', 'paste 0:08–0:12', 'printer 0:12–0:30', '170 seconds', 'CFO-R2-001', 'CANCELLED_USER_REQUEST_NO_RESTART'):
            self.assertIn(value, document)
        self.assertIn('not deployed-build evidence', document)
        self.assertIn('hypothetical', document.lower())
        self.assertIn('no interactive form flow', document)
'''.replace('__HISTORICAL_HASH__', historical_hash)
replace(test_path, '\n\nif __name__ == "__main__":\n', extra_tests + '\n\nif __name__ == "__main__":\n')

# Package revision only: approval/readiness policies and asset membership unchanged.
spec = copy.deepcopy(original_spec)
spec['assetRevision'] = 'r09'
for row in spec['assets']:
    if row['assetId'] == 'LAUNCH-X-COPY-001':
        row['limitations'].append('The 2026-10-12 submission procedure requires all three sponsor handles, a quote-post with final video, and the separate completed leader form. The launch locator is observed, not verified; human roles, Discord cutoff and distinct receipts remain pending. This does not upgrade any claim or approval.')
    if row['assetId'] == 'DEMO-HUMAN-RECORDING-RUNBOOK-001':
        row['limitations'].append('The later owner-selected landing + StudioStart/five-edition opening is a conditional human instruction, not deployed-build or recording evidence. The final take, exact owner review and separate submission receipts remain pending; agent capture stays cancelled.')
dump(SPEC, spec)
loader = importlib.util.spec_from_file_location('package_collateral_refresh', ROOT / 'tools/package_collateral.py')
package = importlib.util.module_from_spec(loader)
loader.loader.exec_module(package)
package.copy_package_files(ROOT, VERSION)
new_files = {str(p.relative_to(ROOT)) for p in (ROOT / f'release/{VERSION}').rglob('*') if p.is_file()} - original_files
if not archive_existing:
    assert archive in new_files
new_copies = new_files - {archive}
assert new_copies and all('-r09-' in p for p in new_copies), new_copies
assert not any(Path(p).suffix.lower() in {'.ttf', '.otf', '.woff', '.woff2'} for p in new_files)
for path in old_release:
    assert digest(path) == old_release[path], 'Historical release changed: ' + path
for path in SOURCE_PATHS:
    if path in original_files:
        subprocess.run(['git', 'add', '--', path], cwd=ROOT, check=True)
subprocess.run(['git', 'add', '--', *sorted(new_files)], cwd=ROOT, check=True)
staged = set(git('diff', '--cached', '--name-only').splitlines())
assert staged <= SOURCE_PATHS | new_files, staged
source_commit = commit('Reconcile submission consumers and materialize immutable r09 draft copies\n\nRefs #9, #10, #11, #22. Preserve earlier observations, media, source-owner\napprovals and cancelled agent capture. Source/metadata split is intentional;\nregistry integration and the final manifest follow in this isolated branch.\n\nExecution receipt: ' + RUN_URL)

inventory = copy.deepcopy(original_inv)
provenance = copy.deepcopy(original_prov)
by_path = {row['path']: row for row in inventory['trackedFiles']}
by_id = {row['assetId']: row for row in provenance['records']}


def record_for_path(path: str) -> dict:
    record_id = by_path[path].get('provenanceRecordId')
    assert record_id in by_id, (path, record_id)
    return by_id[record_id]


def new_record(path: str, template_path: str, role: str, parents=None) -> None:
    assert path not in by_path
    identifier = hashlib.sha256(path.encode()).hexdigest()[:12].upper()
    file_id, asset_id = 'FILE-' + identifier, 'PROV-FILE-' + identifier
    assert asset_id not in by_id
    template = record_for_path(template_path)
    assert template.get('publishability') != 'approved', 'Do not inherit public approval'
    row = copy.deepcopy(template)
    row['assetId'] = asset_id
    row['source'] = {'repo': REPO, 'path': path, 'revision': source_commit, 'revisionKind': 'git_commit', 'url': f'https://github.com/{REPO}/blob/{source_commit}/{path}', 'restrictedOriginalReference': None}
    row['checksum'] = {'algorithm': 'SHA-256', 'value': digest(path), 'status': 'Exact bytes at the pinned source commit; internal draft/support only.'}
    row['createdAt'] = '2026-10-12'
    row['creator'] = f'{role} under GPT-6 Astra Pro orchestration on GitHub Actions. Exact operation receipt: {RUN_URL}; source commit {source_commit}. No model review or new permission is implied.'
    row['toolModel'] = 'GPT-6 Astra Pro; Python 3.9.6 package/registration orchestration. No renderer or provider inference call; no effort or served-tier claim.'
    row['reviewStatus'] = 'pending'
    row['reviewDate'] = None
    row['publishability'] = 'blocked'
    row['lineage'] = {'derivedFrom': list(parents or []), 'derivatives': [], 'transformations': [role + '; exact source/copy identity only, not approval or new media execution.']}
    row['compositionDependencies'] = copy.deepcopy(template.get('compositionDependencies', [])) if parents else []
    if path == 'tests/test_submission_workflow.py':
        row['creator'] = 'Test source reused unchanged from PR #27 at e2344438b4c95bc874539277893614e9598cefa9; this change registers its exact bytes without re-attesting the original writer runtime. Registration receipt: ' + RUN_URL
        row['toolModel'] = 'Original PR #27 implementation runtime is not re-attested here. Registration by GPT-6 Astra Pro with Python 3.9.6.'
    inv_row = copy.deepcopy(by_path[template_path])
    inv_row.update({'path': path, 'fileId': file_id, 'sha256': digest(path), 'provenanceRecordId': asset_id, 'trackedAtRevision': source_commit, 'exists': True, 'pathAvailability': 'created_in_candidate', 'releaseEligible': False})
    if path.startswith('tests/'):
        inv_row['lifecycleState'] = 'not_applicable'
        inv_row['classification'] = 'validation_test'
    inventory['trackedFiles'].append(inv_row)
    provenance['records'].append(row)
    by_path[path], by_id[asset_id] = inv_row, row
    for parent in row['lineage']['derivedFrom']:
        assert parent in by_id, (path, parent)
        siblings = by_id[parent]['lineage']['derivatives']
        assert asset_id not in siblings
        siblings.append(asset_id)


new_record('tests/test_submission_workflow.py', 'tests/test_narrative_handoff.py', 'Register inherited offline submission regression test')
new_record('tests/test_announcement_submission.py', 'tests/test_narrative_handoff.py', 'Register offline announcement and consumer regression tests')
if not archive_existing:
    old_archive = next(p for p in sorted(original_files) if p.startswith(f'release/{VERSION}/history/manifest-') and p.endswith('.json'))
    new_record(archive, old_archive, 'Archive exact prior r08 draft manifest ' + old_manifest_digest)
for path in sorted(new_copies):
    previous = path.replace('-r09-', '-r08-')
    assert previous in by_path, ('Missing prior revision template', path, previous)
    template = record_for_path(previous)
    new_record(path, previous, 'Byte-for-byte r09 package copy; existing media was not re-rendered', template.get('lineage', {}).get('derivedFrom', []))

# Refresh only changed bytes; do not erase earlier creator/model provenance.
for row in provenance['records']:
    source = row.get('source', {})
    path = source.get('path')
    if source.get('repo') != REPO or path in {INV, PROV, MANIFEST}:
        continue
    actual = digest(path)
    if row['checksum'].get('value') == actual:
        continue
    assert path in SOURCE_PATHS, 'Unexpected modified provenance source: ' + path
    assert row.get('publishability') != 'approved', 'Changed approved source needs explicit new decision'
    row['checksum']['value'] = actual
    row['source'].update({'revision': source_commit, 'revisionKind': 'git_commit', 'url': f'https://github.com/{REPO}/blob/{source_commit}/{path}'})
    row['creator'] = 'Current r09 submission-source/integration correction by GPT-6 Astra Pro; inherited PR #27 source is explicitly retained where applicable. Receipt: ' + RUN_URL + '; earlier provenance: ' + str(row.get('creator', 'not recorded'))
    row['toolModel'] = 'Current correction: GPT-6 Astra Pro, source-only; no model review, capture or provider result implied. Earlier provenance: ' + str(row.get('toolModel', 'not recorded'))

for row in inventory['trackedFiles']:
    path = row['path']
    if path in {INV, PROV, 'messaging/claims.json'}:
        assert row['sha256'] is None
        continue
    actual = digest(path)
    if row.get('sha256') != actual:
        assert path in SOURCE_PATHS | {MANIFEST}, 'Unexpected inventory drift: ' + path
        row['sha256'] = actual
        row['trackedAtRevision'] = source_commit

for row in inventory['plannedDeliverables']:
    if row.get('assetId') == 'LAUNCH-X-COPY-001':
        row['intendedUse'] = 'Draft announcement with the known team/project/repository/plan locators and required sponsor tags, plus an internal two-step human handoff. The official launch locator is observed but unverified; the human roles, demo URL, Discord cutoff, separate completion receipts and all exact-use approvals remain pending.'
        row['type'] = 'Draft X announcement and internal two-step submission handoff; not publication approval.'
        row['provenanceReferences'].append('Current organizer procedure observed 2026-10-12 in review/official-format-sources.json; target HTTP 403, human verification pending.')
inventory['execution']['announcementSubmissionFollowup'] = {
    'pullRequest': f'https://github.com/{REPO}/pull/28',
    'sourcePredecessor': BASE,
    'sourceAndCopyCommit': source_commit,
    'assetRevision': 'r09',
    'status': 'Draft integration candidate; independent exact-candidate review and producer acceptance pending.',
    'executionEvidence': RUN_URL,
    'workflowRevision': WORKFLOW_SHA,
    'capture': CANCEL,
    'scope': 'Reconcile submission instructions and selected human opening; preserve prior release bytes, source-owner decisions and distinct readiness gates. No media rendering, publication or provider execution.'
}
assert inventory['submissionScope'] == submission_scope
for row in provenance['records']:
    if row['assetId'] in rights:
        assert protected(row) == rights[row['assetId']], 'Approval/permission field changed: ' + row['assetId']
assert set(by_path) == set(git('ls-files').splitlines()), 'Inventory does not cover exact index'
dump(INV, inventory)
inv_record = by_id['PROV-FILE-E018FDB8D981']
inv_record['source'].update({'revision': 'sha256:' + digest(INV), 'revisionKind': 'sha256_content_digest', 'url': None})
inv_record['checksum']['value'] = digest(INV)
dump(PROV, provenance)
subprocess.run(['git', 'add', '--', INV, PROV], cwd=ROOT, check=True)
input_commit = commit('Bind r09 sources, inherited tests and immutable package provenance\n\nRefs #9, #10, #11, #22. Preserve all existing permission/review decisions and\nsubmission requirements. The exact input snapshot retains the prior manifest\nwith valid digest joins; build and bind only its documented self-references.\n\nExecution receipt: ' + RUN_URL)
print('MANIFEST_INPUT_COMMIT', input_commit, flush=True)

command('draft-input', [sys.executable, '-B', 'tools/validate_collateral.py', '--mode', 'draft'])
command('package-build', [sys.executable, '-B', 'tools/package_collateral.py', 'build', '--version', VERSION])
command('manifest-self-binding', [sys.executable, '-B', 'tools/package_collateral.py', 'bind-self-reference', '--version', VERSION])
modified = set(git('diff', '--name-only').splitlines())
assert modified <= {INV, PROV, MANIFEST}, modified
assert set(git('ls-files', '--others', '--exclude-standard').splitlines()) == set(), 'Unexpected build files'
for path in old_release:
    assert digest(path) == old_release[path], 'Historical release changed after build: ' + path
subprocess.run(['git', 'add', '--', INV, PROV, MANIFEST], cwd=ROOT, check=True)
delivery_commit = commit('Deliver exact r09 draft manifest without changing readiness\n\nRefs #9, #10, #11, #22. Manifest generated by the existing package builder\nand documented self-reference binder from input ' + input_commit + '.\nHistorical copies and manifests are retained. Capture remains cancelled;\ncollateral and external submission readiness remain blocked.\n\nExecution receipt: ' + RUN_URL)

command('full-suite', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
command('visual-suite', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_visual_*.py', '-v'])
command('draft-delivery', [sys.executable, '-B', 'tools/validate_collateral.py', '--mode', 'draft'])
command('package-integrity', [sys.executable, '-B', 'tools/package_collateral.py', 'validate', MANIFEST])
for mode, asset in [('selected', 'DEMO-SCREENSHOT-SET-001'), ('submission', 'LAUNCH-X-KEY-VISUAL-001')]:
    name = mode + '-blocked'
    args = [sys.executable, '-B', 'tools/validate_collateral.py', '--mode', mode, '--select', asset]
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (LOGS / (name + '.log')).write_text(result.stdout)
    (LOGS / (name + '.exit')).write_text(str(result.returncode) + '\n')
    print('COMMAND', name, json.dumps(args), '\n', result.stdout, 'RESULT', result.returncode, flush=True)
    assert result.returncode != 0 and 'BLOCKED' in result.stdout, 'Required gate unexpectedly passed or errored without BLOCKED'
    assert 'ERROR:' not in result.stdout, 'Structural defect is not an expected readiness block'
manifest = load(MANIFEST)
assert manifest['candidateSourceCommitAtGeneration'] == input_commit
assert manifest['collateralPackageReadiness']['decision'] == 'BLOCKED'
assert manifest['externalSubmissionReadiness']['decision'] == 'BLOCKED'
assert not git('status', '--porcelain'), 'Checks changed source bytes'

repro = Path(tempfile.mkdtemp(prefix='mm-r09-repro-')) / 'source'
subprocess.run(['git', 'worktree', 'add', '--detach', str(repro), input_commit], cwd=ROOT, check=True)
try:
    command('repro-build', [sys.executable, '-B', str(repro / 'tools/package_collateral.py'), 'build', '--root', str(repro), '--version', VERSION], cwd=repro)
    command('repro-bind', [sys.executable, '-B', str(repro / 'tools/package_collateral.py'), 'bind-self-reference', '--root', str(repro), '--version', VERSION], cwd=repro)
    command('repro-integrity', [sys.executable, '-B', str(repro / 'tools/package_collateral.py'), 'validate', '--root', str(repro), str(repro / MANIFEST)], cwd=repro)
    command('repro-draft', [sys.executable, '-B', str(repro / 'tools/validate_collateral.py'), '--mode', 'draft'], cwd=repro)
    assert (ROOT / MANIFEST).read_bytes() == (repro / MANIFEST).read_bytes(), 'Reproduction differs'
    print('REPRODUCTION_BYTE_IDENTICAL', digest(MANIFEST), flush=True)
finally:
    subprocess.run(['git', 'worktree', 'remove', '--force', str(repro)], cwd=ROOT, check=True)
    repro.parent.rmdir()
final_prov = load(PROV)
for row in final_prov['records']:
    if row['assetId'] in rights:
        assert protected(row) == rights[row['assetId']], 'Postbuild approval drift'
assert load(INV)['submissionScope'] == submission_scope
for path in old_release:
    assert digest(path) == old_release[path], 'Historical byte drift'
assert not git('status', '--porcelain')
changed = set(git('diff', '--name-only', BASE, 'HEAD').splitlines())
assert changed <= SOURCE_PATHS | new_files | {INV, PROV, MANIFEST}, changed
assert not any(p.startswith('.github/') for p in changed), 'Diagnostic files must not enter source branch'
print('QUALIFIED_FOR_INDEPENDENT_REVIEW_NOT_MERGE', delivery_commit, flush=True)
print('PRIOR_RELEASE_FILES_PRESERVED', len(old_release), flush=True)
print('NEW_IMMUTABLE_COPY_COUNT', len(new_copies), flush=True)
print('CHANGED_PATHS', json.dumps(sorted(changed)), flush=True)
(LOGS / 'delivery-commit.txt').write_text(delivery_commit + '\n')
(LOGS / 'input-commit.txt').write_text(input_commit + '\n')
(LOGS / 'manifest-sha256.txt').write_text(digest(MANIFEST) + '\n')
