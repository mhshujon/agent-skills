# PHP Style

This is the long form of SKILL.md section 5. Use it when:

- Setting up a new file and you want to make sure structural decisions are right
- Writing OOP code (classes, traits, namespaces, type declarations)
- Doing anything multiline or non-obvious where the summary in SKILL.md doesn't cover it
- Reviewing existing code and needing to cite the specific rule that's being broken

## File structure

### Tags

Pure-PHP files start with `<?php` on the first line. They **do not** end with `?>`. The closing tag is omitted to prevent accidental output from trailing whitespace or newlines after it — a real cause of "headers already sent" errors that's nearly impossible to debug.

Mixed PHP/HTML files (template files) use both tags as needed. Use the alternative syntax for control structures (`if (…) :`, `endif;`) when embedding control flow inside markup; it reads much better than braces inside HTML.

### One thing per file

One class, interface, trait, or enum per file. The file is named after what it contains.

### File naming

Class files use the `class-` prefix, lowercase, hyphens replacing underscores:

| Class                          | File                                       |
| ------------------------------ | ------------------------------------------ |
| `My_Plugin_Settings_Page`      | `class-my-plugin-settings-page.php`        |
| `My_Plugin\Admin\Settings_Page` | `class-settings-page.php` (in `admin/`)   |
| `WP_Query`                     | `class-wp-query.php`                       |

The same hyphenated-lowercase convention applies to non-class files, just without the `class-` prefix: `template-functions.php`, `admin-menu.php`, `rest-routes.php`.

**Exception**: PSR-4 autoloaded code. If the project uses Composer's PSR-4 autoloader, file naming follows PSR-4 (`Settings_Page.php` matching the class name exactly). In that case, exclude `WordPress.Files.FileName` in `phpcs.xml.dist` and document the choice — don't half-and-half.

---

## Indentation and whitespace

### Tabs for indentation, spaces for alignment

Indent every line with tabs. Use spaces only to align things mid-line, after the leading tabs:

```php
function example() {
→   $short      = 'a';   // <- spaces here, after the tab, to align
→   $much_longer = 'b';
}
```

The arrow shows where tabs are; the spaces between the variable name and `=` are normal spaces.

A tab width of 4 is conventional for display, but the actual character must be a tab.

### Trailing whitespace

Strip trailing whitespace from every line, including blank lines. Most editors do this on save; configure it.

### Blank lines

One blank line between logical sections within a function. Two blank lines between top-level functions/classes is uncommon in WordPress core; one is fine.

### Spaces around operators and after commas

```php
$x = $a + $b;
$result = foo( $a, $b, $c );
$y .= 'string';
$flag = ! $disabled;
$obj instanceof Class_Name;
$z = 2 ** 3;
```

### Spaces inside parens

Function calls, control structures, and array constructors put a space inside the parens:

```php
if ( $condition ) {
    foo( $a, $b );
}

$arr = array( 1, 2, 3 );
```

Empty parens have no internal space:

```php
function noop() {
    return array();
}
```

Type casts have no space between the cast and the value:

```php
$x = (int) $raw;
$y = (array) $maybe;
```

### Spaces around array keys

```php
$arr['key'] = 'value';      // <- no space inside the brackets for simple keys
$arr[ $variable_key ] = 1;  // <- spaces inside when the key is a variable/expression
$arr[ MY_CONST ] = 1;       // <- spaces around constants/function calls too
```

The rule is: spaces around any non-literal key. Bare string keys and integer literals get tight brackets; everything else gets spaces.

---

## Brace style

Opening brace on the same line as the declaration, closing brace on its own line:

```php
function my_function( $arg ) {
    if ( $arg ) {
        do_thing();
    } else {
        do_other();
    }
}

class My_Class {
    public function method() {
        // ...
    }
}
```

Always use braces, even when PHP allows you to omit them. This:

```php
// Good
if ( $error ) {
    return false;
}

// Bad — PHP allows it, WPCS doesn't
if ( $error ) return false;
```

The reasoning: adding a second line to a braceless block silently creates a bug. The braces are cheap; the bug isn't.

### Alternative syntax in templates

When embedding PHP control flow inside HTML, use the alternative syntax:

```php
<?php if ( have_posts() ) : ?>
    <ul>
        <?php while ( have_posts() ) : the_post(); ?>
            <li><?php the_title(); ?></li>
        <?php endwhile; ?>
    </ul>
<?php endif; ?>
```

This is much easier to scan than `}` mixed with `</tag>`. Note: this is why `elseif` is mandated over `else if` — only `elseif` works with the alternative syntax.

---

## Control structures

### `elseif`, not `else if`

```php
if ( $a ) {
    // ...
} elseif ( $b ) {
    // ...
}
```

### Yoda conditions for equality

For `==`, `!=`, `===`, `!==`, put the constant/literal/function-call on the left and the variable on the right:

```php
if ( 'publish' === $post->post_status ) {
    // ...
}

if ( null === $value ) {
    // ...
}

if ( true === my_check() ) {
    // ...
}
```

The reason is typo defence: `if ( $x = 'publish' )` silently assigns; `if ( 'publish' = $x )` is a syntax error. The compiler catches the second.

**Don't** use Yoda for `<`, `>`, `<=`, `>=` — it reads like nonsense (`if ( 10 > $count )` parses as "if 10 is greater than count", which is the same meaning but harder to verify against the prose intent).

### Strict comparisons

Always prefer `===` and `!==` over `==` and `!=`. Loose comparison in PHP has bizarre corner cases (`0 == 'string'` was `true` until PHP 8). When in doubt, strict.

The same applies to `in_array()` and `array_search()` — always pass `true` as the third argument:

```php
if ( in_array( $value, $allowed, true ) ) {
    // ...
}
```

### Switch statements

```php
switch ( $type ) {
    case 'post':
        do_post();
        break;

    case 'page':
    case 'attachment':
        do_other();
        break;

    default:
        do_default();
        break;
}
```

Each `case` indented one level from `switch`; body indented one level from `case`. Always include a `default`.

### Ternary

Use parens around the condition, always test for truth not falseness:

```php
$state = ( 'on' === $value ) ? 'active' : 'inactive';
```

The exception is `! empty()` which is more natural than its inverse:

```php
$result = ( ! empty( $array ) ) ? $array[0] : null;
```

For complex conditions, use an `if`/`else` block; ternaries should fit on one line clearly.

---

## Naming

### Functions, variables, hooks

`snake_case`, lowercase, with a project prefix on anything global:

```php
// Function — prefixed because it's in the global namespace
function my_plugin_get_active_users() { /* ... */ }

// Variable — no prefix needed for locals
$active_users = my_plugin_get_active_users();

// Hook tag — prefixed
do_action( 'my_plugin_user_registered', $user_id );
apply_filters( 'my_plugin_default_settings', $defaults );
```

The prefix should be unique enough to never collide. Use the plugin slug, not a generic word. `wp_` is reserved for WordPress core; never use it.

### Classes

`PascalCase_With_Underscores` separating words:

```php
class My_Plugin_Settings_Page { }
class WP_Query { }
class WP_REST_Posts_Controller { }
```

Acronyms stay uppercase: `WP_REST_API`, not `WP_Rest_Api`.

### Constants

`UPPER_SNAKE_CASE`:

```php
define( 'MY_PLUGIN_VERSION', '1.0.0' );
define( 'MY_PLUGIN_PATH', plugin_dir_path( __FILE__ ) );

class My_Plugin {
    const STATUS_ACTIVE = 'active';
    const MAX_ITEMS     = 100;
}
```

### Hooks — naming the action/filter tag

Choose verb-based names for actions (something just happened), noun-based names for filters (something is being filtered):

```php
// Actions — verbs
do_action( 'my_plugin_settings_saved', $settings );
do_action( 'my_plugin_user_logged_in', $user );

// Filters — nouns describing what's filtered
apply_filters( 'my_plugin_default_options', $defaults );
apply_filters( 'my_plugin_post_meta_keys', $keys );
```

### Dynamic hook tags

When interpolating variables into hook names, wrap the variables in `{}` and the whole tag in double quotes:

```php
do_action( "my_plugin_status_changed_{$new_status}", $post );
apply_filters( "my_plugin_value_for_{$type}", $value );
```

This is the only place double quotes are needed; everywhere else, use single quotes by default.

---

## Quotes and strings

Single quotes for everything that doesn't need interpolation. Double quotes only when interpolating a variable or using an escape sequence (`\n`, `\t`):

```php
$msg = 'Plain string';                  // <- single
$msg = "User: {$user->name}";           // <- double, with {} around the var
$msg = sprintf( 'User: %s', $user->name ); // <- often clearer than interpolation
```

Always wrap interpolated variables in `{}`. It removes ambiguity (`"$user->name_id"` does not parse the way you'd think; `"{$user->name_id}"` does).

For SQL strings inside `$wpdb->prepare()`, use double quotes so `{$wpdb->prefix}` interpolates:

```php
$wpdb->prepare(
    "SELECT * FROM {$wpdb->prefix}my_table WHERE id = %d",
    $id
);
```

---

## Arrays

### Syntax

WPCS 3.0+ allows both `array()` and `[]`. Pick one per project and stick to it. Long form is the historical WordPress convention; short form is what most modern PHP uses.

### Multiline arrays

When an array spans multiple lines, every element gets its own line, every line ends with a trailing comma (including the last), and alignment of `=>` is optional but conventional:

```php
$args = array(
    'post_type'      => 'post',
    'posts_per_page' => 10,
    'orderby'        => 'date',
    'order'          => 'DESC',
);
```

The trailing comma on the last element means adding a new element doesn't touch the previous line — clean git diffs.

---

## Multiline function calls

When a function call spans multiple lines, each argument goes on its own line. Don't put multiple arguments on the same line of a multiline call:

```php
// Good
$result = some_function(
    $first_argument,
    $second_argument,
    $third_argument
);

// Also good — array literal as argument can open on the call line
$args = wp_parse_args( $input, array(
    'foo' => 'default',
    'bar' => 'default',
) );

// Bad
$result = some_function( $first,
    $second, $third );
```

If a single argument is itself a complex expression that needs multiple lines, assign it to a variable first rather than nesting deeply.

---

## Type declarations (parameter and return types)

WordPress core has historically avoided type declarations for backward compatibility with older PHP versions. For modern plugin code targeting PHP 7.4+ or 8.0+, type declarations are fine and encouraged — they improve readability and catch bugs.

```php
function my_plugin_get_active_users( int $limit = 10, ?string $role = null ): array {
    // ...
    return $users;
}
```

Style rules when you do use them:

- Space after the type, no space before
- Return type: space before `:`, space after
- Nullable: `?Type` with no space between `?` and the type

```php
function example( int $x, ?string $y = null ): ?array {
}
```

---

## Classes (OOP)

### Visibility is required

Every property and method has an explicit visibility keyword:

```php
class Example {
    public $name;
    protected $internal_state;
    private $secret;

    public function get_name() { /* ... */ }
    protected function helper() { /* ... */ }
}
```

Never rely on the implicit `public`.

### Visibility and modifier order

`public|protected|private` first, then `static`, then `function`:

```php
public static function factory() { }
private static $instance;
```

### Constructor signature

If a class has a constructor, name it `__construct`. Don't use the deprecated PHP 4 same-name-as-class style.

### Object instantiation

Always use parens, even with no arguments:

```php
$obj = new My_Class();   // Good
$obj = new My_Class;     // Bad — WPCS will flag
```

### One object structure per file

A file contains one class, interface, trait, or enum — and nothing else (apart from optional namespace and `use` statements at the top). Helper functions don't share a file with a class.

---

## Namespaces and `use` statements

Namespace declaration goes on the line right after the opening `<?php` (with optional file-level docblock between them). One namespace per file.

```php
<?php
/**
 * Settings page handler.
 *
 * @package My_Plugin
 */

namespace My_Plugin\Admin;

use My_Plugin\Core\Settings_Repository;
use My_Plugin\Utils\Sanitizer;
use function My_Plugin\Utils\log_event;
use const My_Plugin\Utils\DEFAULT_TTL;

class Settings_Page {
    // ...
}
```

Rules:

- No leading backslash on `use` statements (`use Foo\Bar`, not `use \Foo\Bar`)
- Group similar imports together — classes, then functions, then constants, separated by blank lines or by `use function`/`use const` syntax
- Aliases should follow WordPress naming conventions (`use Long\Namespace\Path\Class_Name as Aliased_Name`)
- Blank line after the namespace declaration
- Blank line after the `use` block before the class

When using a PSR-4 autoloader with namespaces, exclude `WordPress.Files.FileName` from the ruleset (file naming follows PSR-4 instead of `class-foo.php`).

---

## Operators

### Increment/decrement

Prefer pre-form in standalone statements:

```php
++$counter;  // good
$counter++;  // also valid, but pre-form is preferred
```

The difference matters in expressions; in a standalone statement either works, but the pre-form is the WPCS preference.

### Error control operator `@`

Don't use it. It suppresses *all* errors, including fatal ones, and makes problems invisible. If a function might error, check the return value or wrap with proper error handling:

```php
// Bad
$result = @file_get_contents( $path );

// Good
$result = file_get_contents( $path );
if ( false === $result ) {
    // handle error
}
```

### Spread operator

`...` has no space between it and the variable:

```php
function example( ...$args ) { }
$result = foo( ...$array );
```

---

## Magic constants

Magic constants (`__FILE__`, `__DIR__`, `__LINE__`, `__CLASS__`, etc.) are always uppercase — and they are by language requirement, so this is more a reminder than a rule.

---

## What WPCS won't catch but you should still do

These are conventions WPCS doesn't enforce automatically but that WordPress reviewers will flag:

- **Don't `define()` constants for everything.** Class constants are usually better when the constant is logically tied to a class. Plugin-wide constants (version, path, URL) are fine as `define()`.
- **Keep file headers accurate.** The plugin or theme file header at the top of the main file is what WordPress.org parses; keep `Version`, `Tested up to`, `Requires PHP`, `Text Domain` current.
- **Don't put logic in the main plugin file.** It should bootstrap (define constants, register the autoloader, hook init) and nothing more.
- **Hook init to `plugins_loaded` or later.** Don't run code at file include time. Other plugins and core may not have loaded yet, and you can't use translation functions before `init`.