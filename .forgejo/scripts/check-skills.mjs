import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';

export function checkSkills(root) {
  const errors = [];
  const documents = new Set(['README.md', 'AGENTS.md', 'NOTICE.md']);
  const directories = readdirSync(join(root, 'skills'), { withFileTypes: true })
    .filter(entry => entry.isDirectory());
  if (!directories.length) errors.push('No skills found');
  for (const entry of directories) {
    const file = join('skills', entry.name, 'SKILL.md');
    if (!existsSync(join(root, file))) {
      errors.push(`${file}: missing skill instructions`);
      continue;
    }
    const header = readFileSync(join(root, file), 'utf8').match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
    let metadata;
    try {
      if (!header) throw new Error('Missing frontmatter');
      // https://bun.com/docs/runtime/yaml
      metadata = Bun.YAML.parse(header[1]);
    } catch {
      errors.push(`${file}: missing or invalid YAML frontmatter`);
      continue;
    }
    if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
      errors.push(`${file}: frontmatter must be a mapping`);
      continue;
    }
    const { name, description } = metadata;
    if (typeof name !== 'string' || name !== entry.name || name.length > 64 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name))
      errors.push(`${file}: invalid or missing name`);
    if (typeof description !== 'string' || !description.trim() || Array.from(description).length > 1024)
      errors.push(`${file}: invalid or missing description`);
  }
  const pending = ['skills'];
  while (pending.length) {
    const directory = pending.pop();
    for (const entry of readdirSync(join(root, directory), { withFileTypes: true })) {
      if (entry.name === 'node_modules') continue;
      const file = join(directory, entry.name);
      if (entry.isDirectory()) pending.push(file);
      else if (entry.isFile() && file.endsWith('.md')) documents.add(file);
    }
  }
  for (const document of documents) {
    if (!existsSync(join(root, document))) {
      errors.push(`${document}: missing document`);
      continue;
    }
    const text = readFileSync(join(root, document), 'utf8')
      .replace(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/, '');
    const checkTarget = link => {
      if (/^[a-z][a-z\d+.-]*:/i.test(link) || link.startsWith('//')) return;
      let target;
      try { target = decodeURIComponent(link.split(/[?#]/, 1)[0]); }
      catch { errors.push(`${document}: invalid link target`); return; }
      if (target && !existsSync(join(root, dirname(document), target))) errors.push(`${document}: missing local target ${target}`);
    };
    // https://bun.com/reference/bun/markdown/render
    Bun.markdown.render(text, {
      link(_children, { href }) { checkTarget(href); return ''; },
      image(_children, { src }) { checkTarget(src); return ''; },
    });
  }
  return errors;
}

if (import.meta.main) {
  const errors = checkSkills(process.cwd());
  if (errors.length) {
    console.error(errors.join('\n'));
    process.exitCode = 1;
  } else console.log('Skill metadata and local documentation links are valid');
}
