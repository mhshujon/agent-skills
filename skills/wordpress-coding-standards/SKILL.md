---
name: wordpress-coding-standards
description: "Apply WordPress Coding Standards (WPCS) when writing, reviewing, or refactoring WordPress PHP — plugins, themes, or anything in wp-content/. Use this skill whenever code touches WordPress — files mentioning add_action / add_filter / \\$wpdb / wp_*() / get_option / the_post / WP_Query / WP_REST_*, REST API endpoints, Gutenberg or block code, admin or settings pages, shortcodes, custom post types, or PHPCS rulesets for WordPress projects. Trigger this skill even when the user does NOT say 'WPCS' or 'coding standards' — if the work is WordPress PHP, this skill applies. Also use when the user asks to set up linting, phpcs.xml.dist, or CI for a WordPress project. Covers PHP style (tabs, braces, Yoda, spacing, naming), security (sanitize/validate/escape, nonces, capability checks, prepared SQL via wpdb), inline docs (PHPDoc), i18n with text domains, JavaScript conventions for WP, and bundles four ready-to-use phpcs.xml.dist variants (plugin / theme / strict / lenient)."
---

# WordPress Coding Standards

This skill is for writing WordPress PHP that reads like every other WordPress codebase, ships without security holes, translates correctly for non-English users, and passes WordPress.org plugin review and PHPCS on the first try.

WPCS is not about pedantic style. It's about three goals stacked in priority order:

1. **Safety** — sanitize input, validate before use, escape output, verify nonces, check capabilities, use prepared SQL. Violations here are CVEs.
2. **Translatability** — every user-facing string flows through a translation function with a text domain. Violations here lock out non-English users.
3. **Consistency** — naming, formatting, and file layout match what a WordPress developer expects. Violations here aren't bugs, but they slow every future reader down.

Keep this priority order in mind when you make trade-off decisions.

---

## The strictness rule (read this first)

How aggressively to apply WPCS depends on whether the code is **new** or **legacy**:

| Concern                                                          | New file/code     | Existing/legacy file                            |
| ---------------------------------------------------------------- | ----------------- | ----------------------------------------------- |
| **Security** (sanitize, escape, nonces, caps, prepared SQL)      | Always WPCS       | Always WPCS — fix violations even on edit       |
| **i18n** (translation functions, text domains)                   | Always WPCS       | Always WPCS — fix violations even on edit       |
| **Style** (tabs, braces, Yoda, spacing)                          | Always WPCS       | Match the file's existing style; don't rewrite  |
| **Naming** (snake_case, class file names)                        | Always WPCS       | Match for new symbols; never rename existing    |

The reasoning: security and i18n bugs are *functional* — they make code unsafe or untranslatable. Style and naming inconsistencies in code that already runs in production are *cosmetic*. Mass-rewriting cosmetic violations in legacy code creates merge nightmares, kills git blame, and exhausts code reviewers without delivering value. Be surgical.

A useful mental check on every edit in a legacy file: "Is this a real bug, or a style mismatch with WPCS?" Real bug → fix it. Style mismatch in a file that's otherwise internally consistent → leave it, and match the local style for any new lines you add.

When a file mixes styles or it's genuinely unclear, **surface the choice** instead of deciding silently: "This file uses PSR-12 style. I can match it for consistency, or convert to full WPCS. Which do you prefer?"

---

## Critical rules — apply on every WordPress file

These are the rules that get violated most often and matter most. The full details for each live in the reference files; the summaries here cover the 80% case.

### 1. Sanitize on input. Validate before use. Escape on output.

The single most important rule in WordPress. Three distinct operations, all required:

```php
// INPUT — sanitize $_POST, $_GET, $_REQUEST, $_COOKIE, $_SERVER, and any
// external data (API responses, file contents) as early as possible.
$email = isset( $_POST['email'] )
    ? sanitize_email( wp_unslash( $_POST['email'] ) )
    : '';

// VALIDATE — check the sanitized value is actually what you expect before
// using it for anything that matters.
if ( ! is_email( $email ) ) {
    wp_die( esc_html__( 'Invalid email address.', 'your-text-domain' ) );
}

// OUTPUT — escape immediately before printing. Match the escape function
// to the context (HTML body, attribute, URL, JS, etc.).
echo '<p>' . esc_html( $email ) . '</p>';
```

Always pair `wp_unslash()` with sanitization when reading from superglobals — WordPress magic-quotes them. Always escape at the point of output, not at the point of storage; data can be modified between storage and output by other code.

Load **`references/security.md`** when writing form handlers, AJAX endpoints, REST routes, settings pages, shortcodes, or anything that reads superglobals or writes user-facing markup.

### 2. Every form submission needs a nonce. Every privileged action needs a capability check.

These two checks together prevent the two most common WordPress vulnerabilities — CSRF and privilege escalation.

```php
// In the form/link:
wp_nonce_field( 'save_my_plugin_settings', 'my_plugin_nonce' );

// In the handler:
if ( ! current_user_can( 'manage_options' ) ) {
    wp_die( esc_html__( 'Insufficient permissions.', 'your-text-domain' ) );
}

if (
    ! isset( $_POST['my_plugin_nonce'] )
    || ! wp_verify_nonce(
        sanitize_text_field( wp_unslash( $_POST['my_plugin_nonce'] ) ),
        'save_my_plugin_settings'
    )
) {
    wp_die( esc_html__( 'Security check failed.', 'your-text-domain' ) );
}
```

Note `wp_unslash` + `sanitize_text_field` around the nonce value — `wp_verify_nonce` is pluggable, so WPCS treats its input as untrusted. Without this, the WordPress.Security.NonceVerification sniffs will fail.

### 3. Database queries go through `$wpdb->prepare()`.

Never interpolate user data into SQL. Use placeholders:

```php
// Correct — placeholders + prepare()
$results = $wpdb->get_results(
    $wpdb->prepare(
        "SELECT * FROM {$wpdb->prefix}my_table WHERE user_id = %d AND status = %s",
        $user_id,
        $status
    )
);

// Even safer for common cases — use the high-level API
$post = get_post( $post_id );
$user = get_user_by( 'email', $email );
```

Prefer high-level WordPress APIs (`WP_Query`, `get_posts()`, `get_user_meta()`, etc.) over raw `$wpdb` whenever they fit. Direct `$wpdb` calls trigger additional PHPCS sniffs that want you to justify them.

### 4. Every user-facing string goes through a translation function.

```php
// Translated, then HTML-escaped on output (almost always what you want):
echo '<h2>' . esc_html__( 'Plugin Settings', 'your-text-domain' ) . '</h2>';

// With a placeholder — separate translator comment is required:
printf(
    /* translators: %s: user display name */
    esc_html__( 'Welcome back, %s!', 'your-text-domain' ),
    esc_html( $user->display_name )
);
```

The text domain string must be a plain literal — never a variable, constant, or concatenation. WordPress.org's translation infrastructure parses it statically. Load **`references/i18n.md`** any time you're writing or reviewing user-facing strings, settings labels, admin notices, error messages, or anything rendered to a browser.

### 5. Naming, files, and formatting.

The minimum you need to remember without opening the reference:

- **Indent with tabs.** Spaces only for mid-line alignment.
- **Functions, variables, hooks**: `snake_case`. (`my_plugin_save_settings`, `$user_meta`)
- **Classes**: `PascalCase_With_Underscores`. (`My_Plugin_Settings_Page`)
- **Constants**: `UPPER_SNAKE_CASE`. (`MY_PLUGIN_VERSION`)
- **Class files**: `class-` prefix, lowercase, hyphens. `My_Plugin_Settings_Page` → `class-my-plugin-settings-page.php`. (Exception: if the project uses a PSR-4 autoloader, follow PSR-4 — but be explicit about which convention is in force.)
- **Brace style**: opening brace on the same line; always use braces, even for single-statement bodies.
- **Yoda conditions** for `==`, `!=`, `===`, `!==`: `if ( 'active' === $status )`. Not required (and harder to read) for `<`, `>`, `<=`, `>=`.
- **`elseif`**, not `else if`.
- **Spaces inside parens** for control structures and function calls: `if ( $x )`, `foo( $a, $b )`. None for empty `()`.
- **Prefix everything global** with a unique plugin/theme prefix (`my_plugin_`, `My_Plugin_`, `MY_PLUGIN_`) — functions, classes, constants, hooks, options, post meta keys, transients.
- **Omit the closing `?>` tag** in pure-PHP files.

For anything beyond this — array syntax, type declarations, ternaries, OOP visibility, multiline calls, namespaces — load **`references/php-style.md`**.

### 6. Every function, class, and hook gets a PHPDoc block.

```php
/**
 * Save plugin settings after sanitization and validation.
 *
 * Hooked to `admin_post_save_my_plugin_settings`. Verifies the
 * nonce and capability before writing to the options table.
 *
 * @since 1.0.0
 *
 * @param array $raw_input Raw submitted form data.
 * @return bool True on success, false if validation failed.
 */
function my_plugin_save_settings( $raw_input ) {
    // ...
}
```

Required tags depend on what's being documented. For full reference (file-level blocks, class blocks, hook documentation, `@since`/`@param`/`@return`/`@throws` patterns) load **`references/inline-docs.md`**.

---

## When to load each reference file

The reference files exist to keep this main file lean. Pull them in based on what the task involves:

| Load this reference                       | When you're working on…                                                                                  |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `references/security.md`                  | Form handlers, AJAX endpoints, REST routes, settings pages, anything reading `$_POST`/`$_GET`, SQL, file ops |
| `references/i18n.md`                      | Any user-facing strings — labels, admin notices, error messages, button text, validation messages         |
| `references/php-style.md`                 | Anything beyond the section 5 summary — OOP, namespaces, type declarations, multiline calls, array syntax, ternaries |
| `references/inline-docs.md`               | Writing new functions/classes/hooks, or documenting custom hooks that other plugins will hook into       |
| `references/javascript.md`                | Block editor (Gutenberg) JS/JSX, admin scripts, anything in a plugin's `js/` or `src/` directory          |
| `references/phpcs-setup.md`               | Setting up linting, choosing a ruleset variant, IDE integration, CI, suppressing false positives          |

You don't need to load every reference for every task. Read SKILL.md, decide what's relevant from the table, and pull only those in.

---

## Bundled rulesets

Four `phpcs.xml.dist` variants live in `assets/`. When the user asks to set up linting, copy one of these into the project root and customize the `text_domain` and `prefixes` properties for their plugin:

- **`assets/phpcs-plugin.xml.dist`** — The default. Standard `WordPress` ruleset, PHP 7.4+ compatibility, text domain + prefix placeholders to fill in.
- **`assets/phpcs-theme.xml.dist`** — Adds theme-presentational rules (escaping in templates, no inline JS/CSS, `wp_enqueue_*`). Use for themes and child themes.
- **`assets/phpcs-strict.xml.dist`** — Plugin baseline plus VIP-style hardening: enforces strict comparisons, flags discouraged WordPress functions, requires capability checks on every form handler. Use for client work, agency projects, or anything you want to take seriously from day one.
- **`assets/phpcs-lenient.xml.dist`** — A staged-migration ruleset for legacy codebases. Enforces security and i18n strictly, but relaxes pure-style rules (file naming, alignment, long arrays). Use as a starting point when bolting WPCS onto a project that didn't follow it from the start, then tighten over time.

Read **`references/phpcs-setup.md`** for how to install, run, integrate with editors and CI, and ratchet from lenient → strict.

---

## When PHPCS disagrees with you

PHPCS sniffs are not infallible. Three cases come up regularly:

1. **PHPCS is right and you should fix the code.** Default assumption. Most warnings indicate real issues, and the suggested fix is usually correct.

2. **PHPCS sees a real risk but the context makes it safe.** For example, a SQL query with a table name interpolated from a class constant, not user input. Suppress the specific sniff with a comment on the specific line, and explain why:

   ```php
   // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared -- $table is a class constant, not user input.
   $rows = $wpdb->get_results( "SELECT * FROM {$table}" );
   ```

   Use the narrowest possible suppression (`phpcs:ignore` for one line, not `phpcs:disable` for a whole file), and always include a reason. A bare `phpcs:ignore` with no explanation is a red flag in code review.

3. **PHPCS is wrong about this codebase.** Edit `phpcs.xml.dist` to exclude the rule globally, with a comment explaining why. Common examples: excluding `WordPress.Files.FileName` when using a PSR-4 autoloader, or excluding `WordPress.NamingConventions.ValidVariableName` when interoperating with a non-WordPress library.

What you should *not* do: silently rewrite code in unidiomatic ways just to satisfy a sniff. If the sniff is wrong, suppress it explicitly so the next reader knows the choice was deliberate.

---

## A note on WPCS versions

WPCS 3.0 (released 2023) modernized several historical rules. The most visible change: short array syntax (`[]`) is now allowed by default; previously WPCS required long syntax (`array()`). When you encounter array syntax decisions:

- **New project**: pick one and apply consistently. Long syntax is the historical WordPress core convention; short syntax is what most modern PHP code uses.
- **Existing project**: match the codebase. Don't mix.
- **Codebase pinned to WPCS ≤ 2.x**: long array syntax may still be enforced — check the ruleset before changing.

When you're unsure which WPCS version a project uses, check `composer.json` for `wp-coding-standards/wpcs` and confirm the version.

---

## The mindset

A useful frame: WordPress runs on a huge variety of servers, hosts, and PHP versions, written by hundreds of thousands of plugin/theme authors of wildly varying skill levels. WPCS isn't trying to make code "elegant" — it's trying to make code that any WordPress developer can read instantly, that doesn't trust input it shouldn't, that translates to any language, and that won't break on the weird shared host running PHP 7.4 with `safe_mode` quirks.

When a WPCS rule feels arbitrary, look up the reason — there's almost always a real war story behind it. The `references/` files explain the *why* alongside the *what*, so a violation isn't just a sniff error but an actual decision you can argue about on its merits.