import contextlib
import copy
import io
import json
import os
from pathlib import Path
import runpy
import tempfile

SOURCE = Path(__file__).resolve().parent / 'forgejo-pr-wait'
HEAD, BASE = 'a' * 40, 'b' * 40
PR = {'html_url': 'https://forgejo.invalid/owner/repo/pulls/1', 'head': {'sha': HEAD, 'repo': {'full_name': 'owner/repo'}},
      'base': {'sha': BASE, 'ref': 'main'}, 'mergeable': True, 'merged': False, 'state': 'open',
      'draft': False, 'user': {'login': 'author'}}
PREFIX = 'repos/owner/repo'

with tempfile.TemporaryDirectory(prefix='tstack-tea-') as tmp:
    directory = Path(tmp)
    fixture = directory / 'responses.json'
    tea = directory / 'tea'
    tea.write_text('''#!/usr/bin/env python3
import json, os, re, sys
assert sys.argv[1:4] == ['api', '--login', 'fixture']
endpoint = sys.argv[-1]
assert not endpoint.startswith(('http:', 'https:'))
with open(os.environ['TSTACK_FIXTURE']) as source:
    responses = json.load(source)
if endpoint not in responses:
    page = re.fullmatch(r'(.*[?&]page=)([0-9]+)', endpoint)
    if page and int(page[2]) > 1 and page[1] + '1' in responses:
        print('[]')
        sys.exit(0)
    sys.exit(1)
print(json.dumps(responses[endpoint]))
''')
    tea.chmod(0o755)
    os.environ['PATH'] = str(directory) + os.pathsep + os.environ['PATH']
    os.environ['TSTACK_FIXTURE'] = str(fixture)
    module = runpy.run_path(str(SOURCE))
    globals_ = module['Watcher'].__init__.__globals__
    globals_['LOGIN'] = 'fixture'
    globals_['TARGET_HOST'] = 'forgejo.invalid'

    def responses():
        return {f'{PREFIX}/pulls/1': copy.deepcopy(PR),
                f'{PREFIX}/branches/main': {'status_check_contexts': ['CI'], 'enable_status_check': True, 'required_approvals': 0},
                f'{PREFIX}/pulls/1/reviews?limit=50&page=1': [],
                f'{PREFIX}/issues/1/comments?limit=50&page=1': [],
                f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1': [{'context': 'CI', 'status': 'success'}],
                f'{PREFIX}/compare/{HEAD}...{BASE}': {'total_commits': 0},
                'user': {'login': 'viewer'}}

    def check(data, expected, text='', until='ready', final_pr=None, next_data=None, final_data=None, last_check_pr=None):
        fixture.write_text(json.dumps(data))
        state = directory / str(check.count)
        check.count += 1
        globals_['STATE_DIR'] = state
        state.mkdir()
        watcher = module['Watcher']('owner/repo', 1, until, 5)
        output = io.StringIO()
        result = None
        original_api = globals_['api']
        reads = 0
        status_reads = 0
        def changing_api(endpoint, repo=None):
            nonlocal reads, status_reads
            if '/statuses?' in endpoint and endpoint.endswith('page=1'):
                status_reads += 1
                if status_reads == 3 and last_check_pr is not None:
                    data_now = json.loads(fixture.read_text())
                    data_now[f'{PREFIX}/pulls/1'] = last_check_pr
                    fixture.write_text(json.dumps(data_now))
            if endpoint == f'{PREFIX}/pulls/1':
                reads += 1
                if reads == 3:
                    if final_data is not None:
                        fixture.write_text(json.dumps(final_data))
                    if final_pr is not None:
                        return copy.deepcopy(final_pr)
            return original_api(endpoint, repo)
        globals_['api'] = changing_api
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                watcher.poll()
                watcher.baseline = False
                if next_data is not None:
                    fixture.write_text(json.dumps(next_data))
                watcher.poll()
            except SystemExit as error:
                result = error.code
            except module['ForgejoError']:
                result = 'api-error'
            finally:
                globals_['api'] = original_api
        assert result == expected, (result, expected, output.getvalue())
        assert text in output.getvalue(), output.getvalue()
    check.count = 0

    check(responses(), 0, 'ready on')
    data = responses(); data[f'{PREFIX}/branches/main'].update(enable_status_check=False, status_check_contexts=[])
    data[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'] = []
    check(data, 0, 'ready on')
    check(data, 0, 'green on', until='green')
    data = responses(); data[f'{PREFIX}/branches/main']['status_check_contexts'].append('Missing')
    check(data, None)
    data = responses(); data[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'] = [{'context': 'CI', 'status': 'failure'}]
    check(data, 1, 'failed: CI')
    data = responses(); data[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'].append({'context': 'CI', 'status': 'failure'})
    check(data, 0, 'ready on')
    data = responses(); data[f'{PREFIX}/compare/{HEAD}...{BASE}']['total_commits'] = 1
    check(data, 1, 'BEHIND')
    data = responses(); data[f'{PREFIX}/pulls/1']['mergeable'] = False
    check(data, 1, 'DIRTY')
    data = responses(); data[f'{PREFIX}/branches/main']['required_approvals'] = 1
    check(data, 1, 'required reviews need attention')
    review = {'id': 2, 'state': 'APPROVED', 'commit_id': HEAD, 'official': True, 'stale': False, 'user': {'login': 'reviewer'}}
    data[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [review]
    data[f'{PREFIX}/pulls/1/reviews/2/comments?limit=50&page=1'] = []
    check(data, 0, 'ready on')
    data[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'][0]['commit_id'] = 'c' * 40
    check(data, 1, 'required reviews need attention')
    data = responses(); data[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [{**review, 'state': 'REQUEST_CHANGES'}]
    data[f'{PREFIX}/pulls/1/reviews/2/comments?limit=50&page=1'] = []
    check(data, 1, 'required reviews need attention')
    data = responses(); data[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [review]
    data[f'{PREFIX}/pulls/1/reviews/2/comments?limit=50&page=1'] = [{'id': 3, 'path': 'app.py', 'position': 1, 'body': 'fix', 'user': {'login': 'reviewer'}, 'html_url': PR['html_url'] + '#review-3'}]
    check(data, 1, 'unresolved threads')
    data[f'{PREFIX}/pulls/1/reviews/2/comments?limit=50&page=1'][0]['resolver'] = {'login': 'author'}
    check(data, 0, 'ready on')
    data = responses(); data[f'{PREFIX}/pulls/1']['html_url'] = 'https://wrong.invalid/owner/repo/pulls/1'
    check(data, 'api-error')
    data = responses(); data[f'{PREFIX}/issues/1/comments?limit=50&page=1'] = [{'id': i, 'user': {'login': 'author'}, 'body': ''} for i in range(50)]
    data[f'{PREFIX}/issues/1/comments?limit=50&page=2'] = []
    check(data, 0, 'ready on')
    data = responses(); del data[f'{PREFIX}/branches/main']
    check(data, 'api-error')
    for update in ({'state': 'closed'}, {'merged': True, 'state': 'closed'},
                   {'draft': True}, {'mergeable': False}, {'mergeable': None},
                   {'base': {'sha': BASE, 'ref': 'another-target'}}):
        check(responses(), 1, 'changed during verification', final_pr={**PR, **update})
    for empty in (False, True):
        first = responses()
        first[f'{PREFIX}/branches/main']['enable_status_check'] = False
        if empty:
            first[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'] = []
        second = copy.deepcopy(first)
        new_head = 'c' * 40
        second[f'{PREFIX}/pulls/1']['head']['sha'] = new_head
        second[f'{PREFIX}/commits/{new_head}/statuses?limit=50&page=1'] = second.pop(f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1')
        second[f'{PREFIX}/compare/{new_head}...{BASE}'] = second.pop(f'{PREFIX}/compare/{HEAD}...{BASE}')
        check(first, None, next_data=second)
    first = responses(); second = copy.deepcopy(first)
    second[f'{PREFIX}/branches/main']['status_check_contexts'].append('Missing')
    check(first, None, next_data=second)
    first = responses()
    first[f'{PREFIX}/issues/1/comments?limit=50&page=1'] = [
        {'id': 7, 'user': {'login': 'reviewer'}, 'body': 'Earlier issue comment'}]
    second = copy.deepcopy(first)
    second[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [
        {**review, 'id': 7, 'state': 'REQUEST_CHANGES'}]
    second[f'{PREFIX}/pulls/1/reviews/7/comments?limit=50&page=1'] = []
    check(first, 0, 'review from reviewer', until='any-change', next_data=second)
    second = copy.deepcopy(first)
    second[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [
        {**review, 'id': 8, 'state': 'COMMENTED'}]
    second[f'{PREFIX}/pulls/1/reviews/8/comments?limit=50&page=1'] = [
        {'id': 7, 'path': 'app.py', 'position': 1, 'body': 'New line comment',
         'user': {'login': 'reviewer'}}]
    check(first, 0, 'new thread from reviewer', until='any-change', next_data=second)
    first = responses(); last = copy.deepcopy(first)
    last[f'{PREFIX}/branches/main']['status_check_contexts'].append('Late security')
    check(first, 1, 'changed during verification', final_data=last)
    first = responses()
    first[f'{PREFIX}/branches/main']['required_approvals'] = 1
    first[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = [{**review, 'commit_id': HEAD}]
    first[f'{PREFIX}/pulls/1/reviews/2/comments?limit=50&page=1'] = []
    last = copy.deepcopy(first)
    last[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'][0]['state'] = 'REQUEST_CHANGES'
    check(first, 1, 'changed during verification', final_data=last)
    for until in ('green', 'ready'):
        first = responses(); last = copy.deepcopy(first)
        last[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'][0]['status'] = 'pending'
        check(first, 1, 'changed during verification', until=until, final_data=last)
    first = responses(); pushed = copy.deepcopy(PR)
    pushed['head']['sha'] = 'd' * 40
    check(first, 1, 'changed during verification', last_check_pr=pushed)
    data = responses()
    data[f'{PREFIX}/branches/main']['status_check_contexts'].append('coderabbit')
    data[f'{PREFIX}/commits/{HEAD}/statuses?limit=50&page=1'].append({'context': 'coderabbit', 'status': 'success'})
    check(data, 0, 'required check', until='green')
    data = responses()
    reviews = [{**review, 'id': i, 'commit_id': HEAD, 'user': {'login': f'reviewer-{i}'}}
               for i in range(1, 42)]
    reviews[-1]['state'] = 'REQUEST_CHANGES'
    data[f'{PREFIX}/pulls/1/reviews?limit=50&page=1'] = reviews[:20]
    data[f'{PREFIX}/pulls/1/reviews?limit=50&page=2'] = reviews[20:40]
    data[f'{PREFIX}/pulls/1/reviews?limit=50&page=3'] = reviews[40:]
    for row in reviews:
        data[f"{PREFIX}/pulls/1/reviews/{row['id']}/comments?limit=50&page=1"] = []
    check(data, 1, 'required reviews need attention')
    assert module['parse_target'](PR['html_url'], None) == ('owner/repo', 1)
    print(f'Forgejo watcher scenarios passed: {check.count}')
