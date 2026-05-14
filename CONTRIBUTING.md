# Contributing to Agent Skills

Thanks for contributing. This repo is a community resource — the more people who refine and extend it, the more useful it gets for everyone using Claude.

---

## What kind of contributions are welcome

**Improving an existing skill:**
- **Rule corrections** — a rule in a reference file is wrong, outdated, or conflicts with current tool behaviour
- **Missing coverage** — a pattern, sniff, or concept isn't documented
- **Better examples** — a code example could be clearer, more realistic, or better annotated
- **Asset fixes** — a drop-in config file (e.g. `phpcs.xml.dist`) has false positives, missing rules, or doesn't compile
- **New reference file** — an area deserves its own reference doc (e.g. REST API, multisite, unit testing)

**Adding a new skill:**
- A well-scoped domain with clear, consistent rules that Claude can reliably apply
- See [Adding a new skill](#adding-a-new-skill) below

**Repo tooling:**
- `scripts/package.py` improvements — robustness, ergonomics, new options

If you're unsure whether something is worth a PR, open an issue first. Small fixes (a wrong function name, a broken config attribute) don't need a prior issue.

---

## Setting up locally

```bash
git clone git@github.com:mhshujon/agent-skills.git
cd agent-skills
```

No build step required for editing. Everything is plain Markdown and XML — edit in any text editor.

To test `.skill` packaging:

```bash
# List all available skills
python3 scripts/package.py --list

# Build a specific skill
python3 scripts/package.py wordpress-coding-standards
```

Requires Python 3.8+. The script produces `<skill-name>.skill` in the repo root. The repo root `.gitignore` already excludes `.skill` files.

---

## Adding a new skill

Each skill lives in its own directory under `skills/`:

```
skills/
└── your-skill-name/
    ├── SKILL.md        ← Required: frontmatter + entry point instructions
    ├── references/     ← Optional: reference docs loaded on demand
    └── assets/         ← Optional: drop-in config files, templates, etc.
```

Steps:

1. Create `skills/your-skill-name/` with at minimum a `SKILL.md`
2. Follow the `SKILL.md` structure used by existing skills (frontmatter: `name`, `description`, `version`, `trigger`)
3. Keep the `description` field under 1024 characters (checked below)
4. Add a row to the **Available Skills** table in `README.md`
5. Run through the testing checklist below before opening a PR

---

## Testing your changes

Because skills are prompt-based rather than executable code, testing is manual. Run through the relevant checklist before opening a PR.

### 1. Verify the skill packages cleanly

```bash
python3 scripts/package.py <skill-name>
```

Confirm it exits with no errors and produces a `.skill` file of a reasonable size.

### 2. Check the SKILL.md description length

The `description` field in `SKILL.md` frontmatter must be under 1024 characters:

```bash
python3 -c "
import re
with open('skills/<skill-name>/SKILL.md') as f:
    m = re.search(r'^description: \"(.+?)\"', f.read(), re.MULTILINE | re.DOTALL)
    if m:
        d = m.group(1)
        print(f'Description length: {len(d)} chars')
        print('OK' if len(d) <= 1024 else 'Too long — trim to 1024')
"
```

### 3. Validate any XML assets

If your skill ships XML config files (e.g. `phpcs.xml.dist`):

```bash
python3 -c "
import xml.etree.ElementTree as ET, glob, sys
errors = []
for f in glob.glob('skills/<skill-name>/assets/*.xml.dist'):
    try:
        ET.parse(f)
        print(f'OK  {f}')
    except ET.ParseError as e:
        errors.append(f'{f}: {e}')
        print(f'ERR {f}: {e}')
sys.exit(1 if errors else 0)
"
```

All files must parse without errors. Note: XML comments cannot contain `--` — write them as `(dash-dash)` in prose if needed.

### 4. Install and test in Claude

Upload the `.skill` file to Claude Desktop or claude.ai, enable it, and test with prompts that exercise your changes. For each area you changed, write a prompt that should trigger it and verify Claude responds correctly.

---

## Markdown style

- Use fenced code blocks with a language identifier (` ```php `, ` ```bash `, ` ```xml `, etc.)
- Every code example must be syntactically valid
- Keep reference files self-contained; avoid cross-reference dependencies not already in the routing table in `SKILL.md`
- One blank line between sections; two before a `##` heading

---

## Updating SKILL.md routing table

If you add a new reference file to an existing skill, update the routing table in that skill's `SKILL.md` (the "When to load each reference file" section). Keep the description to one line per file — the reference file is where the detail lives.

---

## Commit message format

```
<area>: <short description>

<optional body — what and why, not how>
```

Areas: `skill`, `scripts`, `readme`, `contrib`, `license` — or a skill-specific area like `security`, `i18n`, `php-style`, `inline-docs`, `javascript`, `phpcs-setup`, `assets`.

Examples:

```
security: add wp_unslash() reminder to nonce verification pattern
```

```
scripts: support --output flag for custom .skill output directory
```

```
skill: add new rest-api-patterns skill
```

---

## Pull request checklist

Before submitting:

- [ ] `python3 scripts/package.py <skill-name>` exits clean
- [ ] `SKILL.md` description is under 1024 characters
- [ ] Any XML assets pass the validator above
- [ ] `README.md` Available Skills table is updated (for new skills)
- [ ] Commit messages follow the format above
- [ ] PR description explains what changed and why (not just "updated X")

---

## Reporting issues

Open a GitHub issue with:

1. **What the skill does** — paste the exact Claude response that was wrong
2. **What it should do** — describe the correct behaviour
3. **The reference** — link to the relevant rule in the [WordPress Coding Standards repo](https://github.com/WordPress/WordPress-Coding-Standards) or the [WordPress Coding Standards handbook](https://developer.wordpress.org/coding-standards/) if you have it

---

## Acknowledgements

The `wordpress-coding-standards` skill is based on the rules and sniffs maintained by the WordPress community in the [WordPress Coding Standards](https://github.com/WordPress/WordPress-Coding-Standards) repository. When updating rules or examples, always verify against that repo to ensure accuracy.

## Maintainer notes

When merging a PR that changes any reference file, test with prompts that cover the changed area. When cutting a release, run `python3 scripts/package.py <skill-name>` for each changed skill, verify the output size is reasonable, and attach the `.skill` files to the GitHub release.
