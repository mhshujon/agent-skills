# Agent Skills for Claude

A collection of Claude AI skills — each one teaches Claude a focused domain of expertise that it applies automatically when relevant.

---

## Available Skills

| Skill | Description |
|---|---|
| [`wordpress-coding-standards`](skills/wordpress-coding-standards/) | Enforces WordPress Coding Standards (WPCS) when writing, reviewing, or refactoring WordPress PHP — plugins, themes, blocks, and anything in `wp-content/` |

---

## Installation

Choose the method that matches how you use Claude.

### Option A — Claude Code (CLI)

Claude Code reads skills from two locations:

| Path | Scope |
|---|---|
| `~/.claude/skills/` | Personal — available in every project |
| `.claude/skills/` | Project — committed to the repo, shared with teammates |

**Personal install (recommended for individuals):**

```bash
# Clone the repo
git clone git@github.com:mhshujon/agent-skills.git

# Copy the skill(s) you want to your global Claude skills directory
cp -r agent-skills/skills/wordpress-coding-standards ~/.claude/skills/wordpress-coding-standards
```

**Project-level install (recommended for teams):**

```bash
# From your project repo root
mkdir -p .claude/skills
git clone git@github.com:mhshujon/agent-skills.git
cp -r agent-skills/skills/wordpress-coding-standards .claude/skills/wordpress-coding-standards
```

Or add it as a git submodule so the team always gets updates:

```bash
git submodule add git@github.com:mhshujon/agent-skills.git _agent-skills
cp -r _agent-skills/skills/wordpress-coding-standards .claude/skills/wordpress-coding-standards
git submodule update --init
```

Claude Code picks up skills automatically on the next session. No restart needed.

**Verify a skill is loaded:**

```
/skills
```

You should see the skill name in the list. You can also invoke it explicitly:

```
/wordpress-coding-standards Review this function for WPCS compliance.
```

---

### Option B — Claude Desktop App

The desktop app reads from the same `~/.claude/skills/` directory as Claude Code.

```bash
git clone git@github.com:mhshujon/agent-skills.git
cp -r agent-skills/skills/wordpress-coding-standards ~/.claude/skills/wordpress-coding-standards
```

Restart Claude Desktop after copying. The skill will be available in your next conversation.

---

### Option C — Claude.ai (Web) or Claude Desktop via UI upload

The web and desktop UIs let you upload a pre-packaged `.skill` file — no terminal required.

**Step 1 — Get the `.skill` file**

Either download the latest release from the [Releases page](https://github.com/YOUR_USERNAME/agent-skills/releases), or build it yourself:

```bash
git clone git@github.com:mhshujon/agent-skills.git
cd agent-skills

# List all available skills
python3 scripts/package.py --list

# Build a specific skill
python3 scripts/package.py wordpress-coding-standards
# Output: wordpress-coding-standards.skill (in the repo root)
```

Requires Python 3.8+. No additional dependencies.

**Step 2 — Upload to Claude**

1. Open [claude.ai/customize/skills](https://claude.ai/customize/skills) (or in the desktop app: **Settings → Customize → Skills**)
2. Click the **+** button → **Create skill** → **Upload a skill**
3. Select the `.skill` file you built
4. Toggle the skill **on**

---

## Repo structure

```
agent-skills/
├── scripts/
│   └── package.py          ← Build tool: packages any skill into a .skill file
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md         ← Entry point loaded by Claude
│       ├── references/      ← Reference docs loaded on demand
│       └── assets/          ← Drop-in config files and templates
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

Each skill is a self-contained directory under `skills/`. Claude loads reference files on demand based on the task — not all at once.

---

## Updating

**Git clone installs:**

```bash
cd agent-skills
git pull
cp -r skills/wordpress-coding-standards ~/.claude/skills/wordpress-coding-standards
```

**Git submodule installs:**

```bash
git submodule update --remote _agent-skills
cp -r _agent-skills/skills/wordpress-coding-standards .claude/skills/wordpress-coding-standards
```

**UI uploads:** download the new release `.skill` file, delete the old skill in Claude settings, and re-upload.

---

## Contributing

Want to add a new skill or improve an existing one? See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
