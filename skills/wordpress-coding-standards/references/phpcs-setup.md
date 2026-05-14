# PHPCS Setup

This file is the operations guide for getting WordPress Coding Standards running on a project — install, configure, integrate with editors, run in CI, and suppress false positives without making a mess.

The four bundled rulesets in `assets/` (plugin, theme, strict, lenient) are the starting templates. Choose one, copy it to the project root as `phpcs.xml.dist`, and fill in the text domain and prefix placeholders. The rest of this file covers the surrounding setup.

---

## Installation

WPCS is distributed as a Composer package. The current version (WPCS 3.x) supports PHP 7.4+ and requires PHP_CodeSniffer 3.10+.

### Project-local install (recommended)

```bash
composer config allow-plugins.dealerdirect/phpcodesniffer-composer-installer true
composer require --dev wp-coding-standards/wpcs:"^3.0"
```

The `dealerdirect/phpcodesniffer-composer-installer` plugin auto-discovers installed standards (WPCS, PHPCompatibility, etc.) and registers them with PHPCS. Without it, you'd have to point PHPCS at the WPCS install path manually.

To run:

```bash
vendor/bin/phpcs              # check
vendor/bin/phpcbf             # auto-fix what can be auto-fixed
vendor/bin/phpcs path/to/file.php   # check a single file
```

The `-ps` flags (progress + summary) are useful: `vendor/bin/phpcs -ps`. Most bundled rulesets here set that as a default with `<arg value="sp"/>`.

### Global install

```bash
composer global config allow-plugins.dealerdirect/phpcodesniffer-composer-installer true
composer global require --dev wp-coding-standards/wpcs:"^3.0"
```

Then run `phpcs` directly if `~/.composer/vendor/bin` is in your `$PATH`.

Project-local is preferable for team projects — the version is pinned in `composer.json` so everyone runs the same one.

### What gets installed alongside WPCS

WPCS depends on:

- `squizlabs/php_codesniffer` — the PHPCS engine itself
- `phpcsstandards/phpcsextra` — additional cross-language sniffs WPCS uses
- `phpcsstandards/phpcsutils` — utilities for sniff authors

You'll also typically install:

- `phpcompatibility/phpcompatibility-wp` — checks code is compatible with the PHP versions WordPress supports

```bash
composer require --dev phpcompatibility/phpcompatibility-wp:"*"
```

---

## Configuring `phpcs.xml.dist`

The ruleset file is XML. Place it in the project root as `phpcs.xml.dist` (the `.dist` suffix means "distributable default"; individual developers can override with a personal `phpcs.xml` that's gitignored).

Two things every project must customize:

### Text domain

So the i18n sniff knows what slug to expect:

```xml
<rule ref="WordPress.WP.I18n">
    <properties>
        <property name="text_domain" type="array">
            <element value="your-plugin-slug"/>
        </property>
    </properties>
</rule>
```

### Prefix

So the `PrefixAllGlobals` sniff knows what prefix your plugin uses:

```xml
<rule ref="WordPress.NamingConventions.PrefixAllGlobals">
    <properties>
        <property name="prefixes" type="array">
            <element value="your_plugin"/>
            <element value="Your_Plugin"/>
            <element value="YOUR_PLUGIN"/>
        </property>
    </properties>
</rule>
```

Include all three casings (snake, Pascal, upper) — they cover functions, classes, and constants respectively.

### Minimum WP and PHP versions

```xml
<config name="minimum_wp_version" value="6.0"/>
<config name="testVersion" value="7.4-"/>
<rule ref="PHPCompatibilityWP"/>
```

`minimum_wp_version` is what WPCS uses for deprecated-function checks. `testVersion` is for the PHPCompatibility sniffs (the `-` means "and up").

---

## Choosing among the bundled rulesets

The four templates in `assets/` differ in strictness. Use them as starting points, customize, commit as `phpcs.xml.dist`.

| Ruleset                       | When to use                                                                 |
| ----------------------------- | --------------------------------------------------------------------------- |
| `phpcs-plugin.xml.dist`       | New plugin, or existing plugin with reasonable existing code quality        |
| `phpcs-theme.xml.dist`        | Theme or child theme                                                        |
| `phpcs-strict.xml.dist`       | Client work, agency projects, anything destined for security review         |
| `phpcs-lenient.xml.dist`      | Legacy codebase you're adding WPCS to — security/i18n strict, style relaxed |

A reasonable progression for a legacy codebase: start with lenient, get the build green, then incrementally tighten — re-enable `WordPress.Files.FileName` after renaming class files, re-enable `WordPress.Arrays.ArrayDeclarationSpacing` after a round of cleanup, etc.

---

## IDE integration

### VS Code

Install [PHP Sniffer & Beautifier](https://marketplace.visualstudio.com/items?itemName=ValeryanM.vscode-phpsab) (or the alternative [phpcs](https://marketplace.visualstudio.com/items?itemName=shevaua.phpcs)).

`.vscode/settings.json`:

```json
{
  "phpsab.executablePathCS": "./vendor/bin/phpcs",
  "phpsab.executablePathCBF": "./vendor/bin/phpcbf",
  "phpsab.standard": "./phpcs.xml.dist",
  "phpsab.snifferEnable": true,
  "phpsab.fixerEnable": true,
  "[php]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "valeryanm.vscode-phpsab"
  }
}
```

The fixer auto-corrects what `phpcbf` can fix on save — whitespace, brace placement, simple naming issues. The sniffer underlines what's left.

### PHPStorm

Settings → PHP → Quality Tools → PHP_CodeSniffer:

1. Set the configuration → "Local" → path to `vendor/bin/phpcs`
2. Settings → Editor → Inspections → PHP → Quality Tools → PHP Code Sniffer validation: enable
3. Coding Standard: set to "Custom" and point at `phpcs.xml.dist`

Reformat code (`Ctrl+Alt+L` / `Cmd+Alt+L`) will then apply WPCS rules.

### Vim/Neovim

ALE handles this transparently:

```vim
let g:ale_linters = { 'php': [ 'phpcs' ] }
let g:ale_fixers  = { 'php': [ 'phpcbf' ] }
let g:ale_php_phpcs_executable = 'vendor/bin/phpcs'
let g:ale_php_phpcbf_executable = 'vendor/bin/phpcbf'
let g:ale_php_phpcs_standard = './phpcs.xml.dist'
let g:ale_fix_on_save = 1
```

---

## CI integration

### GitHub Actions

`.github/workflows/lint.yml`:

```yaml
name: Lint

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  phpcs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.1'
          coverage: none
          tools: composer

      - name: Get composer cache directory
        id: composer-cache
        run: echo "dir=$(composer config cache-files-dir)" >> $GITHUB_OUTPUT

      - name: Cache composer dependencies
        uses: actions/cache@v4
        with:
          path: ${{ steps.composer-cache.outputs.dir }}
          key: ${{ runner.os }}-composer-${{ hashFiles('**/composer.lock') }}
          restore-keys: ${{ runner.os }}-composer-

      - name: Install dependencies
        run: composer install --prefer-dist --no-progress

      - name: Run PHPCS
        run: vendor/bin/phpcs -ps
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
phpcs:
  image: composer:2
  script:
    - composer install --prefer-dist --no-progress
    - vendor/bin/phpcs -ps
  only:
    - merge_requests
    - main
```

### Pre-commit hook (local)

To catch issues before they hit CI, use a pre-commit hook:

```bash
#!/bin/sh
# .git/hooks/pre-commit
CHANGED_PHP=$( git diff --cached --name-only --diff-filter=ACM | grep '\.php$' )

if [ -n "$CHANGED_PHP" ]; then
    echo "$CHANGED_PHP" | xargs vendor/bin/phpcs --standard=./phpcs.xml.dist || exit 1
fi
```

Make it executable: `chmod +x .git/hooks/pre-commit`.

For team distribution, prefer [Husky](https://typicode.github.io/husky/) or similar — `.git/hooks/` isn't versioned.

---

## Suppressing false positives

PHPCS isn't always right. When it isn't, suppress with a comment that explains why. The narrower the suppression, the better.

### Single line

```php
// phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared -- $table is a class constant, not user input.
$rows = $wpdb->get_results( "SELECT * FROM {$table}" );
```

### Specific block

```php
// phpcs:disable WordPress.Security.EscapeOutput -- This entire section outputs pre-escaped HTML from wp_kses_post().
echo $sanitized_html;
echo $more_sanitized_html;
// phpcs:enable WordPress.Security.EscapeOutput
```

### Whole file

In the file's docblock:

```php
<?php
/**
 * Database migrations.
 *
 * @package My_Plugin
 *
 * phpcs:disable WordPress.DB.DirectDatabaseQuery -- Schema management requires direct queries.
 */
```

### Rules for suppression

1. **Always include a reason** after `--`. Bare suppressions are red flags in review.
2. **Use the narrowest scope possible.** A line-level `phpcs:ignore` is far better than a file-level `phpcs:disable`.
3. **Suppress specific sniffs, not "everything".** `phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared` is fine; bare `phpcs:ignore` suppresses every rule on that line, which often hides things you didn't mean to hide.
4. **Periodically audit suppressions.** Code that needed a suppression a year ago might have been refactored and no longer does.

---

## Running phpcbf (auto-fixer)

`phpcbf` automatically fixes the violations PHPCS can fix safely — whitespace, brace placement, alignment, some naming, missing trailing commas, etc. It can't fix logic issues (security, validation, naming that requires knowing intent).

```bash
vendor/bin/phpcbf                 # fix everything PHPCS finds
vendor/bin/phpcbf path/to/file    # fix one file
```

Workflow on existing code:

1. Run `phpcbf` once to auto-fix the easy stuff.
2. Run `phpcs` to see what's left.
3. Address remaining issues manually.
4. Commit the auto-fixes as a separate commit from your actual changes, so the diff for your changes stays clean.

---

## Performance

On large codebases, PHPCS can be slow. Two speedups:

### Parallel processing

```xml
<arg name="parallel" value="8"/>
```

8 is a reasonable default; tune to the CPU count.

### Restrict file types

```xml
<arg name="extensions" value="php"/>
```

Without this, PHPCS scans `.inc`, `.js`, `.css`, etc. too, often slowly.

### Caching

```bash
vendor/bin/phpcs --cache
```

Or set in the ruleset:

```xml
<arg name="cache" value=".phpcs.cache"/>
```

Add `.phpcs.cache` to `.gitignore`. Cached runs skip unchanged files entirely.

---

## Common errors and how to fix them

### `WordPress.Files.FileName.InvalidClassFileName`

The class file isn't named `class-foo-bar.php`. Either rename the file or, if using PSR-4, exclude the sniff in `phpcs.xml.dist`.

### `WordPress.NamingConventions.PrefixAllGlobals.NonPrefixedFunctionFound`

A global-namespace function doesn't have the configured prefix. Rename it, or put it in a class/namespace.

### `WordPress.Security.NonceVerification.Missing` / `Recommended`

`$_POST` / `$_GET` is being read without a preceding nonce check. Add the check, or — if this is a read context where CSRF doesn't apply (like a GET endpoint that only reads) — suppress with explanation.

### `WordPress.Security.EscapeOutput.OutputNotEscaped`

Variable is being echoed without an escape function. Add the appropriate `esc_*()`.

### `WordPress.WP.I18n.MissingArgDomain`

A translation call is missing its text domain. Add the second argument.

### `WordPress.WP.I18n.NonSingularStringLiteralDomain`

The text domain isn't a literal string. Replace whatever (variable, constant, concatenation) with the literal slug.

### `WordPress.WP.I18n.MissingTranslatorsComment`

A `printf` / `sprintf` with placeholders doesn't have the `/* translators: */` comment above it. Add it.

### `WordPress.DB.PreparedSQL.InterpolatedNotPrepared`

SQL is being interpolated with values that should be placeholders. Use `$wpdb->prepare()` with `%s`/`%d`/`%i`.

### `WordPress.DB.DirectDatabaseQuery.DirectQuery`

A raw `$wpdb` call is being made. Either switch to a high-level WordPress API, add a cache layer, or — if the direct query is truly necessary — suppress with explanation.

### `WordPress.PHP.YodaConditions.NotYoda`

A `==`/`===` comparison has the variable on the left. Swap the sides.

### `Squiz.Commenting.FunctionComment.Missing`

A function lacks a docblock. Add one (see inline-docs.md).

---

## What to do when WPCS disagrees with you

The three cases from SKILL.md, restated:

1. **PHPCS is right** → fix the code.
2. **PHPCS sees a real risk but the context makes it safe** → narrow `phpcs:ignore` with a reason.
3. **PHPCS is wrong for this codebase** → exclude the rule in `phpcs.xml.dist` with a comment.

A useful test: if a teammate asked you "why does this code violate the standard?", and your answer is a clear technical explanation rather than "we just decided not to follow that one", suppress at the line level. If your answer is "we follow PSR-4, not WordPress file naming", exclude the sniff globally and document the choice in the ruleset.