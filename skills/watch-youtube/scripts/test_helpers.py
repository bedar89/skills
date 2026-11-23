import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True
import common
import local
import openrouter

URL = 'https://www.youtube.com/watch?v=hWe-j78vNpc'


class VideoRoutes(unittest.TestCase):
    def test_youtube_links_become_one_canonical_video_without_tracking_or_playlist(self):
        for source in ['https://youtu.be/hWe-j78vNpc?t=42',
                       'https://www.youtube.com/shorts/hWe-j78vNpc', URL + '&list=other']:
            self.assertEqual(common.youtube_url(source), URL)
        for source in ['https://youtube.com.evil.test/watch?v=hWe-j78vNpc',
                       'https://user:secret@youtube.com/watch?v=hWe-j78vNpc',
                       'https://www.youtube.com/playlist?list=other', '/tmp/private.mp4']:
            with self.assertRaises(ValueError):
                common.youtube_url(source)

    def test_gemini_uses_video_input_and_only_the_youtube_capable_provider(self):
        data = openrouter.payload(URL, 'What is shown?', openrouter.DEFAULT_MODEL, 1024)
        self.assertEqual(data['provider'], {'only': ['google-ai-studio'], 'allow_fallbacks': False})
        video = data['messages'][0]['content'][1]
        self.assertEqual(video, {'type': 'video_url', 'video_url': {'url': URL, 'processing': 'agentic'}})
        self.assertEqual(data['max_tokens'], 1024)
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            openrouter.payload(URL, '  ', openrouter.DEFAULT_MODEL, 1024)

    def test_compact_transcript_keeps_cue_times_and_removes_rolling_markup(self):
        vtt = ('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello <c>world</c>\n\n'
               '00:00:02.000 --> 00:00:04.000\nHello world\nA &amp; B\n\n'
               '00:00:04.000 --> 00:00:06.000\nA &amp; B <00:00:04.200><c>work.</c>\n')
        self.assertEqual(local.compact_transcript(vtt, rolling=True),
                         '[00:00:00.000] Hello world\n[00:00:02.000] A & B\n[00:00:04.000] work.\n')
        self.assertEqual(local.compact_transcript('WEBVTT\n'), '')

    def test_youtube_auto_caption_space_line_does_not_separate_words_from_cue(self):
        vtt = ('WEBVTT\nKind: captions\nLanguage: en\n\n'
               '00:00:00.030 --> 00:00:02.869 align:start position:0%\n \n'
               'hello<00:00:00.300><c> and</c><00:00:00.600><c> welcome</c>\n\n'
               '00:00:02.869 --> 00:00:02.879 align:start position:0%\nhello and welcome\n\n'
               '00:00:02.879 --> 00:00:04.000 align:start position:0%\n'
               'hello and welcome\nto<00:00:03.000><c> the show</c>\n\n'
               '00:00:12.000 --> 00:00:14.000 align:start position:0%\n \nlast words\n')
        self.assertEqual(local.compact_transcript(vtt, rolling=True),
                         '[00:00:00.030] hello and welcome\n[00:00:02.879] to the show\n[00:00:12.000] last words\n')

    def test_manual_caption_boundaries_preserve_real_spoken_repetition(self):
        vtt = ('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nI said no\n\n'
               '00:00:03.000 --> 00:00:05.000\nno way.\n')
        self.assertEqual(local.compact_transcript(vtt),
                         '[00:00:01.000] I said no\n[00:00:03.000] no way.\n')

    def test_existing_credentials_are_read_without_copy_and_environment_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            auth = Path(directory) / 'auth.json'
            original = json.dumps({'openrouter': {'type': 'api_key', 'key': 'fixture-only-file-key'}})
            auth.write_text(original)
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(openrouter.credential(str(auth)), 'fixture-only-file-key')
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture-only-environment-key'}):
                self.assertEqual(openrouter.credential(str(auth)), 'fixture-only-environment-key')
            self.assertEqual(auth.read_text(), original)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['auth.json'])

    def test_partial_cloud_answer_is_saved_with_usage_and_secret_redacted(self):
        response = {'model': 'google/test', 'provider': 'Google AI Studio',
                    'usage': {'cost': 0.012}, 'choices': [{'finish_reason': 'length',
                    'message': {'content': 'Visible code, fixture-only-secret'}}]}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(openrouter, 'credential', return_value='fixture-only-secret'), \
                patch.object(openrouter, 'urlopen', return_value=io.StringIO(json.dumps(response))), \
                contextlib.redirect_stdout(io.StringIO()):
            code = openrouter.ask(URL, 'Question', out_dir=directory)
            evidence = json.loads(next(Path(directory).rglob('evidence.json')).read_text())
            self.assertEqual(code, 2)
            self.assertEqual(evidence['status'], 'partial')
            self.assertEqual(evidence['cost_usd'], 0.012)
            self.assertNotIn('fixture-only-secret', next(Path(directory).rglob('report.md')).read_text())

    def test_empty_cloud_response_and_provider_error_are_not_success_or_retried(self):
        with patch.object(openrouter, 'credential', return_value='fixture-only-secret'):
            for content in ['', None]:
                with patch.object(openrouter, 'urlopen', return_value=io.StringIO(json.dumps(
                        {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}))) as call:
                    with self.assertRaisesRegex(ValueError, 'no usable answer'):
                        openrouter.ask(URL, 'Question')
                    self.assertEqual(call.call_count, 1)
            error = HTTPError(openrouter.API, 429, 'private detail', {}, io.BytesIO(b'fixture-only-secret'))
            with patch.object(openrouter, 'urlopen', side_effect=error) as call:
                with self.assertRaisesRegex(ValueError, 'HTTP 429') as caught:
                    openrouter.ask(URL, 'Question')
                self.assertNotIn('fixture-only-secret', str(caught.exception))
                self.assertEqual(call.call_count, 1)

    def test_native_caption_is_preferred_over_manual_translation(self):
        info = {'subtitles': {'nl': [{}]}, 'automatic_captions': {'en-orig': [{}], 'en': [{}]}}
        self.assertEqual(local.caption_track(info), ('automatic', 'en-orig', True))
        info['subtitles']['en'] = [{}]
        self.assertEqual(local.caption_track(info), ('manual', 'en', True))

    def test_documented_cli_does_not_write_bytecode_beside_live_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / 'scripts'
            shutil.copytree(SCRIPTS, scripts)
            for name in ['local.py', 'openrouter.py']:
                result = subprocess.run([sys.executable, str(scripts / name), '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(scripts.rglob('*.pyc')), [])

    def test_local_errors_keep_reason_without_credentials_or_false_http_status(self):
        for diagnostic, expected in [
                ('[youtube] ID429: Requested format is not available', 'exit 1'),
                ('HTTP Error 429: Too Many Requests', 'HTTP 429')]:
            command = [sys.executable, '-c', 'import sys;sys.stderr.write(sys.argv[1]);sys.exit(1)', diagnostic]
            with self.assertRaises(ValueError) as caught:
                local.run(command)
            self.assertIn(expected, str(caught.exception))
            self.assertIn(diagnostic.split(':')[-1].strip(), str(caught.exception))
        command[-1] = 'api_key=fixture-only-secret https://example.invalid/?token=fixture-only-secret'
        with self.assertRaises(ValueError) as caught:
            local.run(command)
        self.assertNotIn('fixture-only-secret', str(caught.exception))

    def test_caption_rate_limit_keeps_metadata_and_frames_in_cli_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / 'tool'
            executable.write_text(r'''#!/usr/bin/env python3
import sys,json,pathlib,os
args=sys.argv[1:];tool=pathlib.Path(sys.argv[0]).name
if tool=='yt-dlp':
 if '--ignore-config' not in args: pathlib.Path(os.environ['SIDE_EFFECT']).write_text('inherited config write')
 if '--dump-single-json' in args:
  print(json.dumps({'title':'Fixture video','description':'Source link','subtitles':{'en':[{}]}}))
 elif '--skip-download' in args:
  pathlib.Path(os.environ['SIDE_EFFECT']+'.caption-called').write_text('called')
  if os.environ.get('CAPTION_SUCCESS'):
   p=pathlib.Path(args[args.index('-o')+1].replace('%(ext)s','en.vtt'))
   p.write_text('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello <c>world</c>\n\n00:00:02.000 --> 00:00:04.000\nworld matters.\n')
  else: print('HTTP Error 429',file=sys.stderr);sys.exit(1)
 else:
  p=pathlib.Path(args[args.index('-o')+1].replace('%(ext)s','mp4'));p.write_bytes(b'fixture');print(p)
elif tool=='ffprobe': print(json.dumps({'format':{'duration':'20'}}))
else: pathlib.Path(args[-1]).write_bytes(b'fixture-frame')
''')
            executable.chmod(0o755)
            for name in ['yt-dlp', 'ffprobe', 'ffmpeg']:
                (root / name).symlink_to(executable)
            result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'local.py'), URL,
                                     '--max-frames', '2', '--out-dir', str(root / 'evidence')],
                                    env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                                         'SIDE_EFFECT': str(root / 'unexpected-config-write')},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            evidence = json.loads(next(root.rglob('evidence.json')).read_text())
            self.assertEqual(evidence['metadata']['title'], 'Fixture video')
            self.assertIsNone(evidence['caption'])
            self.assertEqual(len(evidence['frames']), 2)
            self.assertTrue(any('429' in e for e in evidence['errors']))
            self.assertEqual(evidence['frames'][1]['requested_seconds'], 19.75)
            self.assertFalse((root / 'unexpected-config-write').exists())
            self.assertIn(evidence['media'], next(root.rglob('report.md')).read_text())

            result = subprocess.run([sys.executable, str(SCRIPTS / 'local.py'), URL, '--transcript-only',
                                     '--out-dir', str(root / 'metadata-only')],
                                    env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                                         'SIDE_EFFECT': str(root / 'unexpected-config-write')},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            evidence = json.loads(next((root / 'metadata-only').rglob('evidence.json')).read_text())
            self.assertEqual(evidence['status'], 'unavailable')

            result = subprocess.run([sys.executable, str(SCRIPTS / 'local.py'), URL, '--transcript-only',
                                     '--out-dir', str(root / 'caption-success')],
                                    env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                                         'CAPTION_SUCCESS': '1', 'SIDE_EFFECT': str(root / 'unexpected-config-write')},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            evidence = json.loads(next((root / 'caption-success').rglob('evidence.json')).read_text())
            self.assertEqual(evidence['status'], 'complete')
            self.assertEqual(Path(evidence['caption']['transcript']).read_text(),
                             '[00:00:00.000] Hello world\n[00:00:02.000] world matters.\n')
            self.assertTrue(Path(evidence['caption']['path']).is_file())
            self.assertNotIn('media', evidence)

            caption_marker = Path(str(root / 'unexpected-config-write') + '.caption-called')
            caption_marker.unlink()
            result = subprocess.run([sys.executable, str(SCRIPTS / 'local.py'), URL, '--skip-captions',
                                     '--max-frames', '1', '--out-dir', str(root / 'no-repeat')],
                                    env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                                         'SIDE_EFFECT': str(root / 'unexpected-config-write')},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(caption_marker.exists())
            evidence = json.loads(next((root / 'no-repeat').rglob('evidence.json')).read_text())
            self.assertEqual(len(evidence['frames']), 1)


if __name__ == '__main__':
    unittest.main()
