import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { expect, test } from 'bun:test';
import { checkSkills } from './check-skills.mjs';

function fixture(run, name = 'example') {
  const root = mkdtempSync(join(tmpdir(), 'skill-check-'));
  mkdirSync(join(root, 'skills', name), { recursive: true });
  for (const file of ['README.md', 'AGENTS.md', 'NOTICE.md']) writeFileSync(join(root, file), '# Example\n');
  try {
    run(root, join(root, 'skills', name, 'SKILL.md'));
  } finally {
    rmSync(root, { recursive: true });
  }
}

test('accepts valid YAML with a folded description', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: example\ndescription: >-\n  A useful description.\n---\n# Example\n');
    expect(checkSkills(root)).toEqual([]);
  });
});

test.each([
  ['malformed YAML', 'name: example\ndescription: "unterminated'],
  ['non-string description', 'name: example\ndescription: [Brief]'],
  ['empty folded description', 'name: example\ndescription: >-'],
  ['oversized description', `name: example\ndescription: ${'x'.repeat(1025)}`],
  ['mismatched name', 'name: different\ndescription: Brief'],
  ['missing description', 'name: example'],
])('rejects %s', (_label, metadata) => {
  fixture((root, skill) => {
    writeFileSync(skill, `---\n${metadata}\n---\n# Example\n`);
    expect(checkSkills(root).length).toBeGreaterThan(0);
  });
});

test('rejects invalid skill names even when matching the directory', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: bad--name\ndescription: Brief\n---\n');
    expect(checkSkills(root).length).toBeGreaterThan(0);
  }, 'bad--name');
});

test('rejects a directory without SKILL.md', () => {
  fixture(root => expect(checkSkills(root).length).toBeGreaterThan(0));
});

test('checks inline titles and reference-style local links', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: example\ndescription: Brief\n---\n');
    writeFileSync(join(root, 'README.md'), '[Skill](skills/example/SKILL.md "Instructions")\n');
    expect(checkSkills(root)).toEqual([]);
    writeFileSync(join(root, 'README.md'), '[Skill][instructions]\n\n[instructions]: skills/missing/SKILL.md\n');
    expect(checkSkills(root).length).toBeGreaterThan(0);
  });
});

test('ignores fenced and inline code examples but checks links after them', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: example\ndescription: Brief\n---\n');
    const examples = '````css\n[popover]:popover-open {}\n```\n[Example](missing.md)\n````\nUse `[Example](missing.md)` as sample text.\n';
    writeFileSync(join(root, 'README.md'), examples);
    expect(checkSkills(root)).toEqual([]);
    writeFileSync(join(root, 'README.md'), examples + '\n[Missing](missing.md)\n');
    expect(checkSkills(root).length).toBeGreaterThan(0);
  });
});

test('checks real links between paragraphs containing unmatched backticks', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: example\ndescription: Brief\n---\n');
    writeFileSync(join(root, 'README.md'), 'An unmatched ` in this paragraph.\n\n[Broken](missing.md)\n\nAnother ` in a separate paragraph.\n');
    expect(checkSkills(root).length).toBeGreaterThan(0);
  });
});

test('uses Markdown semantics for escaped examples, indented code and query links', () => {
  fixture((root, skill) => {
    writeFileSync(skill, '---\nname: example\ndescription: Brief\n---\n');
    writeFileSync(join(root, 'README.md'), '\\[Example](missing.md)\n\n    [Example](missing.md)\n\n[Notice](NOTICE.md?plain=1#license)\n');
    expect(checkSkills(root)).toEqual([]);
  });
});
