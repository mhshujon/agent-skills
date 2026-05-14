# Inline Documentation

WordPress uses PHPDoc blocks extensively. They serve three purposes:

1. **IDE support** — autocomplete, parameter hints, type info
2. **Generated documentation** — developer.wordpress.org parses these
3. **Reader comprehension** — the docblock answers questions the code can't

The WordPress core handbook on inline documentation specifies the format. This reference covers the practical patterns.

## When to write a docblock

Required:
- Every file (file-level docblock at the top)
- Every function (including methods)
- Every class, interface, trait, enum
- Every class property
- Every class constant
- Every custom hook (`do_action` / `apply_filters` you publish for other developers)

Skip:
- Trivial getters/setters where the property docblock already says everything
- Closures used as callbacks (the docblock goes on the registration, e.g., the `add_action` call, if anywhere)
- Generated code (mark it `@generated` or skip — but the file header should still explain how it was generated)

---

## File-level docblock

Every file starts with a docblock that describes what's in the file:

```php
<?php
/**
 * Settings page rendering and handlers.
 *
 * Builds the plugin's admin settings UI under Settings → My Plugin
 * and handles form submission, sanitization, and persistence.
 *
 * @package    My_Plugin
 * @subpackage Admin
 * @since      1.0.0
 */
```

Tags:

- `@package` — top-level grouping, usually the plugin name (with underscores)
- `@subpackage` — area within the plugin (`Admin`, `REST`, `Blocks`, etc.)
- `@since` — version this file was introduced

The file-level block stands alone; don't merge it with a class block below it. Two separate blocks.

---

## Function docblock

```php
/**
 * Save plugin settings after sanitization and validation.
 *
 * Verifies the nonce and capability, sanitizes each field, validates
 * against the schema, and writes to the options table. On validation
 * failure, sets a settings error and returns false.
 *
 * @since 1.0.0
 *
 * @param array  $raw_input  Raw submitted form data, expected to contain
 *                           keys 'api_key', 'email', 'enable_cache'.
 * @param string $capability Capability required to save. Defaults to
 *                           'manage_options'.
 *
 * @return bool True on success, false if validation failed or the user
 *              lacks the required capability.
 */
function my_plugin_save_settings( $raw_input, $capability = 'manage_options' ) {
    // ...
}
```

The structure:

1. **Short description** (one line, sentence case, ends with period)
2. **Blank line**
3. **Long description** (optional, multiple lines, fuller context)
4. **Blank line** (only if long description present)
5. **`@since`** tag
6. **Blank line** (before tag group changes)
7. **`@param`** tags, aligned
8. **Blank line**
9. **`@return`** tag (if applicable)

### `@param` alignment

Align the type, variable name, and description across all `@param` lines in the same block, with at least one space between each column. This is conventional in WordPress core:

```php
 * @param int    $post_id   Post ID.
 * @param string $meta_key  Meta key to update.
 * @param mixed  $value     New value.
```

### Types

Use the same type names PHP uses internally. Common types:

- `int`, `float`, `string`, `bool`, `array`, `object`, `mixed`
- `callable`, `iterable`
- A specific class: `WP_Post`, `WP_Error`, `My_Plugin\Settings`
- `null` for nullable: `string|null` (older) or `?string` (modern)
- Multiple possible types: `int|WP_Error`
- Array element types in description: `int[]` or `array<string, mixed>`

For arrays with a known structure, document the keys:

```php
 * @param array $args {
 *     Optional. Array of arguments for the query.
 *
 *     @type int    $posts_per_page Number of posts. Default 10.
 *     @type string $orderby        Sort field. Accepts 'date', 'title', 'menu_order'.
 *                                  Default 'date'.
 *     @type string $order          'ASC' or 'DESC'. Default 'DESC'.
 * }
```

The `{ ... }` block with inner `@type` tags is the WordPress core convention for documenting hash-shaped arrays. It works in IDEs and renders cleanly in generated docs.

### Optional parameters

Document defaults in prose, not just in the signature:

```php
 * @param int $limit Optional. Maximum results to return. Default 10.
```

### Return values

If the function can return multiple types, list each and what condition produces it:

```php
 * @return WP_Post|null Post object, or null if no post matches.
```

```php
 * @return int|WP_Error Post ID on success, WP_Error on failure.
```

For functions that don't return anything, omit `@return` entirely. Don't write `@return void`.

---

## Class docblock

```php
/**
 * Manages the plugin's settings page in the admin area.
 *
 * Registers the menu, renders the form, and dispatches submissions to
 * the appropriate handler. Uses the WordPress Settings API for field
 * registration and storage.
 *
 * @since 1.0.0
 */
class My_Plugin_Settings_Page {
    // ...
}
```

Tags often omitted for classes (most metadata lives on individual methods):

- `@since` — when the class was introduced
- `@package` / `@subpackage` — usually inherited from file-level

### Property docblocks

```php
class My_Plugin_Settings_Page {

    /**
     * The plugin's option name in the wp_options table.
     *
     * @since 1.0.0
     *
     * @var string
     */
    const OPTION_NAME = 'my_plugin_settings';

    /**
     * Cached settings array. Populated lazily on first access.
     *
     * @since 1.0.0
     *
     * @var array|null
     */
    private $settings = null;
}
```

Even for trivially-typed properties (especially with PHP 7.4+ typed properties), the docblock is still expected:

```php
    /**
     * Settings repository.
     *
     * @since 1.0.0
     *
     * @var Settings_Repository
     */
    private Settings_Repository $repository;
```

---

## Hook docblocks

When you publish a custom action or filter, document it so other developers (and IDE tooling) understand its contract:

```php
/**
 * Fires after plugin settings have been saved.
 *
 * Use this to invalidate related caches, sync external services,
 * or react to specific setting changes.
 *
 * @since 1.0.0
 *
 * @param array $new_settings The settings that were just saved.
 * @param array $old_settings The previous settings, before the save.
 * @param int   $user_id      ID of the user who triggered the save.
 */
do_action( 'my_plugin_settings_saved', $new_settings, $old_settings, $user_id );
```

```php
/**
 * Filters the default plugin settings.
 *
 * Use this to override defaults at activation time, or to inject
 * settings from a network-level configuration in multisite.
 *
 * @since 1.0.0
 *
 * @param array $defaults Associative array of default setting values.
 *                        Keys match the registered settings fields.
 */
$defaults = apply_filters( 'my_plugin_default_settings', $defaults );
```

The docblock immediately precedes the `do_action`/`apply_filters` call. WordPress's hook documentation tooling parses these in place.

---

## Common tags

| Tag             | Purpose                                                    |
| --------------- | ---------------------------------------------------------- |
| `@since`        | Version this was introduced. Required on every block.      |
| `@param`        | Parameter name, type, description.                         |
| `@return`       | Return type and description.                               |
| `@var`          | Property type.                                             |
| `@throws`       | Exception class that may be thrown, and when.              |
| `@deprecated`   | Mark deprecated; include the version and what to use instead. |
| `@see`          | Cross-reference to related symbols.                        |
| `@link`         | URL for further reference.                                 |
| `@global`       | Globals used inside (rare; WordPress-specific).            |
| `@package`      | Top-level package name.                                    |
| `@subpackage`   | Sub-area within the package.                               |
| `@access`       | Rarely needed; visibility keyword suffices.                |
| `@todo`         | Outstanding work. Fine for ongoing development.            |

### `@deprecated` example

```php
/**
 * Get user's preferred language.
 *
 * @since      1.0.0
 * @deprecated 2.0.0 Use get_user_locale() instead.
 *
 * @param int $user_id User ID.
 * @return string Locale code.
 */
function my_plugin_get_user_language( $user_id ) {
    _deprecated_function( __FUNCTION__, '2.0.0', 'get_user_locale' );
    return get_user_locale( $user_id );
}
```

### `@throws`

```php
 * @throws My_Plugin_Validation_Exception When the settings fail schema validation.
 * @throws RuntimeException When the database write fails.
```

---

## Inline comments

Above and beyond docblocks, inline comments are encouraged for non-obvious logic. Two styles:

```php
// Single-line comment, full sentence, capitalized.

/*
 * Multi-line comment for longer prose, blocks of explanation,
 * or temporarily commented-out code with a TODO.
 */
```

Don't use `/** ... */` for inline comments — that's for docblocks specifically and confuses doc generators. Use `//` or `/* */`.

### What's worth commenting

- **Why**, not what. The code shows what; the comment explains why.
- Workarounds for browser/PHP/plugin bugs (include a link to the bug)
- Non-obvious performance trade-offs
- Magic numbers (`60 * 60 * 24 // One day`)
- Anything a code reviewer would have asked "why?" about

Don't comment things the code makes obvious:

```php
// Bad
$i = 0; // Initialize counter to zero
$i++;   // Increment counter

// Good
$i = 0;
$i++;
```

---

## Checklist

- [ ] Every file starts with a file-level docblock with `@package` and `@since`.
- [ ] Every function has a docblock with description, `@param`s, `@return`, `@since`.
- [ ] Every class has a docblock with description and `@since`.
- [ ] Every class property has a `@var` docblock.
- [ ] Every published hook (`do_action` / `apply_filters` your plugin emits) has a docblock above the call.
- [ ] `@param` types match what the function actually accepts.
- [ ] `@return` describes both happy-path and error cases when applicable.
- [ ] `/* translators: */` comments precede translation calls with placeholders (covered in i18n.md).
- [ ] No `@return void` — omit `@return` entirely if there's no return value.