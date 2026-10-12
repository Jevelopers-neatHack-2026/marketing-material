#!/usr/bin/env python3
"""Keep r08/r09 naming coverage while recovering the exact pinned r09 run.

Run 38299861323: 175 tests, 174 passed and one stale r08 expectation failed.
Its actual failure remains evidence. This wrapper changes that test only;
production naming, collisions, source snapshots and all qualification gates
are unchanged. Pure-method preflight is not the full manifest fixture suite.
"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
import subprocess
from unittest.mock import patch

PIN = 'c8aa304febadfc5307687cc586e679672daf88e6'
WRAPPER = '.github/diagnostics/mm07_recovery.py'
WRAPPER_SHA256 = 'bb5d9c686b0c5f0578c1a2eee4c6853f0957ef56abac4baaf2cca4adc925184e'
TEST_PATH = 'tests/test_package_collateral.py'
TEST_BLOB = 'b2e8bcbbf728d2a1f3e2e30b135e2ba2ec421efd'
METHOD = 'test_package_name_encodes_asset_variant_and_destination_without_overwriting_legacy_source'
OLD = '''    def test_package_name_encodes_asset_variant_and_destination_without_overwriting_legacy_source(self) -> None:
        spec = package.read_json(ROOT / "release/v0.1.0-rehearsal/package-spec.json")
        row = next(item for item in spec["assets"] if item["assetId"] == "DEMO-RECORDING-CHECKLIST-001")
        name = package.package_filename(row, ROOT / row["path"], {"status": "not_applicable"}, spec)
        self.assertEqual(
            "demo-001-demo-recording-checklist-001-r08-repository-internal-review-text-en-us-rehearsal-recording-plan.md",
            name,
        )
        self.assertTrue((ROOT / row["path"]).is_file())
'''
NEW = '''    def test_package_name_encodes_asset_variant_and_destination_without_overwriting_legacy_source(self) -> None:
        spec = package.read_json(ROOT / "release/v0.1.0-rehearsal/package-spec.json")
        row = next(item for item in spec["assets"] if item["assetId"] == "DEMO-RECORDING-CHECKLIST-001")
        source = ROOT / row["path"]
        original_source = source.read_bytes()
        original_spec = package.json.dumps(spec, sort_keys=True)
        name = package.package_filename(row, source, {"status": "not_applicable"}, spec)
        self.assertEqual(
            "demo-001-demo-recording-checklist-001-"
            f"{spec['assetRevision']}-repository-internal-review-text-en-us-rehearsal-recording-plan.md",
            name,
        )
        # Explicit old/new fixtures catch a stale constant; the current package
        # assertion follows its declared revision rather than freezing r08.
        names = {}
        for revision in ("r08", "r09"):
            with self.subTest(revision=revision):
                revised_spec = dict(spec, assetRevision=revision)
                names[revision] = package.package_filename(
                    row, source, {"status": "not_applicable"}, revised_spec
                )
                self.assertEqual(
                    "demo-001-demo-recording-checklist-001-"
                    f"{revision}-repository-internal-review-text-en-us-rehearsal-recording-plan.md",
                    names[revision],
                )
        self.assertNotEqual(names["r08"], names["r09"])
        self.assertEqual(original_source, source.read_bytes())
        self.assertEqual(original_spec, package.json.dumps(spec, sort_keys=True))
'''


def once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, ('Pinned context changed', old[:100])
    return text.replace(old, new, 1)


def main() -> None:
    test_path = Path(TEST_PATH).resolve()
    raw = test_path.read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == TEST_BLOB
    old_source = raw.decode('utf-8')
    new_source = once(old_source, OLD, NEW)
    ast.parse(new_source, filename=TEST_PATH)
    # Isolate the pure naming method before building the expensive pinned
    # inspector. No setUpClass/manifest pass is implied by these controls.
    old_ns = {'__file__': str(test_path), '__name__': 'mm07_old_naming_preflight'}
    exec(compile(old_source, TEST_PATH, 'exec'), old_ns)
    package = old_ns['package']
    spec = package.read_json(Path('release/v0.1.0-rehearsal/package-spec.json'))
    with patch.object(package, 'read_json', return_value=dict(spec, assetRevision='r09')):
        try:
            getattr(old_ns['PackagePolicyTests'](METHOD), METHOD)()
        except AssertionError as error:
            assert 'r08' in str(error) and 'r09' in str(error), error
            print('SYNTHETIC_R09_SPEC_REPRODUCES_RETAINED_R08_TEST_FAILURE', flush=True)
        else:
            raise AssertionError('Old naming expectation unexpectedly accepted r09')
    new_ns = {'__file__': str(test_path), '__name__': 'mm07_new_naming_preflight'}
    exec(compile(new_source, TEST_PATH, 'exec'), new_ns)
    getattr(new_ns['PackagePolicyTests'](METHOD), METHOD)()
    print('PURE_NAMING_METHOD_PASS_CURRENT_R08_R09_DISTINCT_SOURCE_AND_SPEC_UNCHANGED', flush=True)
    assert test_path.read_bytes() == raw, 'Preflight must not mutate the checkout'

    wrapper_bytes = subprocess.check_output(['git', 'show', PIN + ':' + WRAPPER])
    assert hashlib.sha256(wrapper_bytes).hexdigest() == WRAPPER_SHA256
    wrapper_source = wrapper_bytes.decode('utf-8')
    patch_source = (
        "\nname_path = ROOT / " + repr(TEST_PATH) + "\n"
        "name_source = name_path.read_text(encoding='utf-8')\n"
        "assert name_source.count(" + repr(OLD) + ") == 1, 'Pinned naming test changed'\n"
        "name_path.write_text(name_source.replace(" + repr(OLD) + ', ' + repr(NEW) + ", 1), encoding='utf-8')\n"
    )
    insertion = (
        "    repaired = once(repaired, " + repr("'tests/test_current_handoff_status.py',\n}") + ', '
        + repr("'tests/test_current_handoff_status.py', 'tests/test_package_collateral.py',\n}") + ')\n'
        + '    updates += ' + repr(patch_source) + '\n'
    )
    wrapper_source = once(wrapper_source, "    context['recipe'] = repaired\n",
                          insertion + "    context['recipe'] = repaired\n")
    ast.parse(wrapper_source, filename=WRAPPER)
    exec(compile(wrapper_source, '<pinned-mm07-with-naming-regression>', 'exec'), {'__name__': '__main__'})


if __name__ == '__main__':
    main()
