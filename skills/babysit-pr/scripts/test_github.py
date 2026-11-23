import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parent / 'pr-wait'
MODULE = runpy.run_path(str(SOURCE))
GLOBALS = MODULE['Watcher'].__init__.__globals__
HEAD, BASE = 'a' * 40, 'b' * 40
PR = {'url': 'https://github.com/owner/repo/pull/1', 'state': 'OPEN',
      'isDraft': False, 'headRefOid': HEAD, 'baseRefName': 'main', 'mergeStateStatus': 'CLEAN',
      'baseRef': {'target': {'oid': BASE}}, 'author': {'login': 'author'},
      'comments': {'nodes': []}, 'reviews': {'nodes': []}, 'reviewThreads': {'nodes': [], 'pageInfo': {'hasPreviousPage': False}}}


class GitHubWatcher(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='github-watcher-test-')
        self.addCleanup(temp.cleanup)
        self.pr = copy.deepcopy(PR)
        self.reads = 0
        self.check_reads = 0
        self.before_final_check = None
        self.branch_paths = []
        self.final_pr = None
        self.gates_read = []
        self.checks = [{'name': 'CI', 'bucket': 'pass', 'link': '', 'description': ''}]
        self.branch_metadata = {'protected': False, 'protection': {'enabled': False, 'required_status_checks': {'contexts': [], 'checks': []}}}
        self.gates = {'main': {'CI'}, 'other': {'Missing'}}
        def gh(args, **kwargs):
            if args[:2] == ['api', 'graphql']:
                self.reads += 1
                pr = self.final_pr if self.reads == 3 and self.final_pr else self.pr
                payload = json.dumps({'data': {'repository': {'pullRequest': pr}, 'viewer': {'login': 'viewer'}}})
            elif args[:2] == ['pr', 'checks']:
                self.check_reads += 1
                if self.check_reads == 3 and self.before_final_check:
                    self.before_final_check()
                payload = json.dumps(self.checks)
            elif args[0] == 'api' and '/branches/' in args[1]:
                self.branch_paths.append(args[1])
                payload = json.dumps(self.branch_metadata)
            else:
                payload = '0'
            return subprocess.CompletedProcess(args, 0, payload, '')
        def required(repo, base):
            self.gates_read.append(base)
            return self.gates[base]
        context = patch.dict(GLOBALS, STATE_DIR=Path(temp.name), gh=gh, required_checks=required)
        context.start()
        self.addCleanup(context.stop)
        self.watcher = MODULE['Watcher']('owner/repo', 1, 'green', 5)
        self.output = io.StringIO()

    def poll(self):
        with contextlib.redirect_stdout(self.output), contextlib.redirect_stderr(self.output):
            try:
                self.watcher.poll()
            except SystemExit as result:
                return result.code
        self.watcher.baseline = False
        return None

    def test_new_head_needs_two_polls(self):
        self.assertIsNone(self.poll())
        self.pr['headRefOid'] = 'c' * 40
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 0)
        self.assertIn('green on ccccccc', self.output.getvalue())

    def test_retarget_refreshes_required_checks(self):
        self.assertIsNone(self.poll())
        self.pr['baseRefName'] = 'other'
        self.assertIsNone(self.poll())
        self.assertIsNone(self.poll())
        self.assertEqual(self.gates_read, ['main', 'other', 'other'])

    def test_same_branch_policy_is_refreshed(self):
        self.assertIsNone(self.poll())
        self.gates['main'] = {'CI', 'Missing'}
        self.assertIsNone(self.poll())
        self.assertIsNone(self.poll())

    def test_unknown_policy_is_not_an_empty_gate(self):
        for status in ('403', '404', '500', '429'):
            with self.subTest(status=status):
                def unreadable(args):
                    raise MODULE['GhError']('HTTP ' + status, status != '403')
                with patch.dict(GLOBALS, required_checks=MODULE['required_checks'], gh_lines=unreadable):
                    with self.assertRaises(MODULE['GhError']):
                        self.poll()

    def test_policy_paths_encode_a_branch_as_one_segment(self):
        paths = []
        def lines(args):
            paths.append(args[1])
            return []
        with patch.dict(GLOBALS, gh_lines=lines):
            self.assertEqual(MODULE['required_checks']('owner/repo', 'release/1.x'), set())
        self.assertEqual(paths, ['repos/owner/repo/rules/branches/release%2F1.x'])
        self.assertEqual(self.branch_paths, ['repos/owner/repo/branches/release%2F1.x'])

    def arm_ready(self):
        self.watcher.until = 'ready'
        self.pr['comments']['nodes'] = [{'id': 'bot-comment', 'url': PR['url'],
                                        'author': {'login': 'greptile', '__typename': 'Bot'}, 'body': HEAD[:7] + ' reviewed'}]

    def test_final_ready_read_must_keep_review_feedback(self):
        self.arm_ready()
        self.assertIsNone(self.poll())
        self.final_pr = copy.deepcopy(self.pr)
        self.final_pr['reviewThreads']['nodes'] = [{'isResolved': False, 'comments': {'nodes': []}}]
        self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())

    def test_ready_refuses_truncated_thread_history(self):
        self.arm_ready()
        self.pr['reviewThreads']['pageInfo']['hasPreviousPage'] = True
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 1)
        self.assertIn('thread history', self.output.getvalue())

    def test_policy_reads_classic_checks_from_branch_metadata(self):
        self.branch_metadata = {'protected': True, 'protection': {'enabled': True,
                                'required_status_checks': {'contexts': ['Classic'], 'checks': [{'context': 'App CI'}]}}}
        with patch.dict(GLOBALS, gh_lines=lambda args: [json.dumps({'context': 'Rules CI', 'integration_id': None})]):
            self.assertEqual(MODULE['required_checks']('owner/repo', 'main'), {'Classic', 'App CI', 'Rules CI'})
        self.branch_metadata['protection'] = {}
        with patch.dict(GLOBALS, gh_lines=lambda args: []):
            with self.assertRaises(MODULE['GhError']):
                MODULE['required_checks']('owner/repo', 'main')

    def test_final_confirmation_rechecks_policy(self):
        self.assertIsNone(self.poll())
        def move_policy(*args):
            self.gates['main'] = {'CI', 'Late security'}
            return ''
        with patch.object(self.watcher, 'behind', side_effect=move_policy):
            self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())

    def test_user_name_is_not_a_bot_review(self):
        self.arm_ready()
        self.pr['comments']['nodes'][0]['author']['__typename'] = 'User'
        self.assertIsNone(self.poll())
        self.assertIsNone(self.poll())

    def test_check_completion_does_not_prove_a_review(self):
        self.watcher.until = 'ready'
        self.checks.append({'name': 'greptile', 'bucket': 'pass', 'link': '', 'description': ''})
        self.assertIsNone(self.poll())
        self.assertIsNone(self.poll())

    def test_failed_review_check_prevents_ready(self):
        self.arm_ready()
        self.checks.append({'name': 'greptile', 'bucket': 'fail', 'link': '', 'description': ''})
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 1)
        self.assertIn('review checks failed', self.output.getvalue())

    def test_ready_requires_a_clean_non_draft_pr(self):
        self.arm_ready()
        self.assertIsNone(self.poll())
        self.pr['isDraft'] = True
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 1)
        self.assertIn('merge state', self.output.getvalue())

    def test_final_green_rechecks_actual_results(self):
        self.assertIsNone(self.poll())
        def rerun(*args):
            self.checks[0]['bucket'] = 'pending'
            return ''
        with patch.object(self.watcher, 'behind', side_effect=rerun):
            self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())

    def test_final_ready_rechecks_actual_results(self):
        self.arm_ready()
        self.assertIsNone(self.poll())
        def fail_ci(*args):
            self.checks[0]['bucket'] = 'fail'
            return ''
        with patch.object(self.watcher, 'behind', side_effect=fail_ci):
            self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())

    def test_explicitly_required_advisory_check_is_reconfirmed(self):
        self.gates['main'] = {'CI', 'coderabbit'}
        self.checks.append({'name': 'coderabbit', 'bucket': 'pass', 'link': '', 'description': ''})
        self.assertIsNone(self.poll())
        def rerun(*args):
            self.checks[1]['bucket'] = 'pending'
            return ''
        with patch.object(self.watcher, 'behind', side_effect=rerun):
            self.assertEqual(self.poll(), 1)

    def test_head_is_confirmed_after_reading_check_results(self):
        self.assertIsNone(self.poll())
        def push():
            self.pr['headRefOid'] = 'd' * 40
        self.before_final_check = push
        self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())

    def test_unresolved_thread_blocks_without_visible_comments(self):
        self.arm_ready()
        self.pr['reviewThreads']['nodes'] = [{'isResolved': False, 'path': 'app.py',
                                             'line': 1, 'comments': {'nodes': []}}]
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 1)
        self.assertIn('unresolved threads', self.output.getvalue())

    def test_classic_source_bound_checks_refuse_name_only_verification(self):
        self.branch_metadata = {'protected': True, 'protection': {'enabled': True,
                                'required_status_checks': {'contexts': ['CI'], 'checks': [{'context': 'CI', 'app_id': 123}]}}}
        with patch.dict(GLOBALS, gh_lines=lambda args: []):
            with self.assertRaisesRegex(MODULE['GhError'], 'source-bound'):
                MODULE['required_checks']('owner/repo', 'main')
        self.branch_metadata['protection']['required_status_checks']['checks'][0]['app_id'] = -1
        with patch.dict(GLOBALS, gh_lines=lambda args: []):
            self.assertEqual(MODULE['required_checks']('owner/repo', 'main'), {'CI'})

    def test_ruleset_source_bound_checks_refuse_name_only_verification(self):
        with patch.dict(GLOBALS, gh_lines=lambda args: [json.dumps({'context': 'CI', 'integration_id': 123})]):
            with self.assertRaisesRegex(MODULE['GhError'], 'source-bound'):
                MODULE['required_checks']('owner/repo', 'main')

    def test_explicitly_required_advisory_check_is_labelled_required(self):
        self.gates['main'] = {'CI', 'coderabbit'}
        self.checks.append({'name': 'coderabbit', 'bucket': 'pass', 'link': '', 'description': ''})
        self.assertIsNone(self.poll())
        self.assertEqual(self.poll(), 0)
        self.assertIn('required check', self.output.getvalue())
        self.assertNotIn('advisory, not waited on', self.output.getvalue())

    def test_malformed_classic_check_source_is_unknown(self):
        for source in (True, -1.0, '123', 0):
            with self.subTest(source=source):
                self.branch_metadata = {'protected': True, 'protection': {'enabled': True,
                                        'required_status_checks': {'contexts': ['CI'], 'checks': [{'context': 'CI', 'app_id': source}]}}}
                with patch.dict(GLOBALS, gh_lines=lambda args: []):
                    with self.assertRaisesRegex(MODULE['GhError'], 'unknown'):
                        MODULE['required_checks']('owner/repo', 'main')

    def test_required_rules_on_following_pages_are_not_omitted(self):
        for producer in (None, 123):
            with self.subTest(producer=producer):
                def paged_api(args, **kwargs):
                    if '/rules/branches/' in args[1]:
                        payload = json.dumps({'context': 'Late CI', 'integration_id': producer}) if '--paginate' in args else ''
                    else:
                        payload = json.dumps(self.branch_metadata)
                    return subprocess.CompletedProcess(args, 0, payload, '')
                with patch.dict(GLOBALS, gh=paged_api, gh_lines=MODULE['gh_lines']):
                    if producer is None:
                        self.assertEqual(MODULE['required_checks']('owner/repo', 'main'), {'Late CI'})
                    else:
                        with self.assertRaisesRegex(MODULE['GhError'], 'source-bound'):
                            MODULE['required_checks']('owner/repo', 'main')

    def test_final_read_cannot_confirm_a_closed_pr(self):
        self.assertIsNone(self.poll())
        self.final_pr = {**self.pr, 'state': 'CLOSED'}
        self.assertEqual(self.poll(), 1)
        self.assertIn('changed during verification', self.output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
