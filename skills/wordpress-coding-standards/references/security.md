# Security

Security is the most consequential part of WPCS. A style violation is ugly; a security violation is a CVE in the WordPress.org Plugin Directory's monthly vulnerability report. This file is the long form of the rules summarized in SKILL.md section 1–3.

The mental model is three distinct operations, applied at three different points in the request lifecycle:

| Step       | When                        | Goal                                                          |
| ---------- | --------------------------- | ------------------------------------------------------------- |
| Sanitize   | As input enters the system  | Strip out anything that doesn't belong in this data type      |
| Validate   | Before using the value      | Confirm the cleaned value is actually what you expect         |
| Escape     | Immediately before output   | Render the value safe for the specific output context         |

All three are required. None of them substitutes for the others. Sanitize before validation, validate before use, escape just before printing.

---

## Sanitization (on input)

Every read from `$_POST`, `$_GET`, `$_REQUEST`, `$_COOKIE`, `$_SERVER`, `$_FILES`, an external API response, an uploaded file's contents, or anything else not under your control, must be sanitized **as early as possible** — ideally on the same line as the read.

WordPress superglobals are also magic-quoted. Always `wp_unslash()` before sanitizing string values to remove the slashes.

### Choosing the right sanitizer

| Data type                 | Function                                | Notes                                                   |
| ------------------------- | --------------------------------------- | ------------------------------------------------------- |
| Plain single-line text    | `sanitize_text_field()`                 | Strips tags, normalizes whitespace, removes line breaks |
| Multiline text            | `sanitize_textarea_field()`             | Like above but preserves newlines                       |
| Email address             | `sanitize_email()`                      | Strips invalid characters                                |
| URL (for storage)         | `esc_url_raw()`                         | The "raw" variant is for DB storage, not output         |
| Integer                   | `absint()` or `(int) $value`            | `absint()` returns non-negative integer                  |
| Float                     | `(float) $value`                        | Cast directly                                            |
| Boolean                   | `rest_sanitize_boolean()`               | Handles "1"/"0"/"true"/"false"/"yes"/"no"                |
| Hex color                 | `sanitize_hex_color()`                  | Returns `#xxx` or `#xxxxxx` or null                      |
| HTML class                | `sanitize_html_class()`                 | Single class, no spaces                                  |
| Slug                      | `sanitize_title()`                      | Lowercase, hyphens, URL-safe                             |
| File name                 | `sanitize_file_name()`                  | Safe for filesystems                                    |
| User name (login)         | `sanitize_user()`                       | WordPress username rules                                |
| HTML with allowed tags    | `wp_kses()` / `wp_kses_post()`          | Allowlist of tags/attrs; `wp_kses_post()` matches post content |
| Key (option/meta name)    | `sanitize_key()`                        | Lowercase alphanumeric + `_`/`-`                         |
| MIME type                 | `sanitize_mime_type()`                  | Format `type/subtype`                                   |
| SQL `ORDER BY` etc.       | `sanitize_sql_orderby()`                | Use when you can't use placeholders                     |

For arbitrary structured data (arrays, objects, JSON), recurse into the structure and sanitize each leaf with the appropriate function. Don't `sanitize_text_field()` on a nested array — it'll produce nonsense.

### Example: sanitizing a typical settings form

```php
function my_plugin_sanitize_settings( $input ) {
    $clean = array();

    $clean['api_key']      = isset( $input['api_key'] )      ? sanitize_text_field( $input['api_key'] )      : '';
    $clean['contact_email'] = isset( $input['contact_email'] ) ? sanitize_email( $input['contact_email'] )     : '';
    $clean['homepage_url'] = isset( $input['homepage_url'] ) ? esc_url_raw( $input['homepage_url'] )           : '';
    $clean['post_count']   = isset( $input['post_count'] )   ? absint( $input['post_count'] )                : 10;
    $clean['enable_cache'] = ! empty( $input['enable_cache'] );
    $clean['welcome_html'] = isset( $input['welcome_html'] ) ? wp_kses_post( $input['welcome_html'] )         : '';

    return $clean;
}
```

Note these are called *without* `wp_unslash()` because `register_setting()` already unslashes. When reading directly from `$_POST`, do unslash:

```php
$api_key = isset( $_POST['api_key'] )
    ? sanitize_text_field( wp_unslash( $_POST['api_key'] ) )
    : '';
```

---

## Validation (before use)

Sanitization removes invalid characters. Validation confirms the sanitized value is actually correct for its purpose — that an "email" parses as one, that an "integer" is in range, that an enum value is one of the allowed options.

| Check                          | Function or pattern                                       |
| ------------------------------ | --------------------------------------------------------- |
| Email                          | `is_email( $email )`                                      |
| URL                            | `wp_http_validate_url( $url )` or `filter_var( $url, FILTER_VALIDATE_URL )` |
| Integer in range               | `$x >= $min && $x <= $max` after casting                  |
| Value in allowed set           | `in_array( $value, $allowed, true )` (always strict)      |
| Post exists                    | `get_post( $id ) instanceof WP_Post`                      |
| User exists                    | `get_userdata( $id ) instanceof WP_User`                  |
| Term exists                    | `term_exists( $term, $taxonomy )` (returns array or 0)    |
| File MIME type                 | `wp_check_filetype( $file )` against an allowlist         |
| Date string                    | `DateTime::createFromFormat( $format, $value ) !== false` |

**Always use strict comparisons** (`===`, `!==`, `in_array( ..., true )`) when validating. Loose comparison is a regular source of authentication bugs in PHP.

### Example: validation after sanitization

```php
$post_id = isset( $_POST['post_id'] ) ? absint( $_POST['post_id'] ) : 0;
if ( ! $post_id || ! get_post( $post_id ) instanceof WP_Post ) {
    wp_die( esc_html__( 'Invalid post.', 'your-text-domain' ) );
}

$allowed_statuses = array( 'draft', 'publish', 'private' );
$status = isset( $_POST['status'] ) ? sanitize_key( wp_unslash( $_POST['status'] ) ) : '';
if ( ! in_array( $status, $allowed_statuses, true ) ) {
    wp_die( esc_html__( 'Invalid status.', 'your-text-domain' ) );
}
```

---

## Escaping (on output)

Sanitization protects the database. Escaping protects the user's browser. The two are different operations because the contexts they defend against are different — XSS attacks happen at output time, not storage time. Even data you sanitized on input must be escaped on output, because:

- Another plugin's filter might have modified the value between storage and display
- The data might come from a source you didn't sanitize (core options, third-party plugins, etc.)
- Defence in depth — multiple layers, none of which has to be perfect alone

### Choosing the right escape function

| Output context                       | Function                                  |
| ------------------------------------ | ----------------------------------------- |
| HTML body text                       | `esc_html( $value )`                      |
| HTML attribute value                 | `esc_attr( $value )`                      |
| URL in `href`/`src`                  | `esc_url( $value )`                       |
| URL for DB storage                   | `esc_url_raw( $value )` (not for output)  |
| Inline JavaScript variable           | `esc_js( $value )` (or `wp_json_encode`)  |
| XML node                             | `esc_xml( $value )`                       |
| Textarea content                     | `esc_textarea( $value )`                  |
| Translated string in HTML body       | `esc_html__()` / `esc_html_e()`           |
| Translated string in attribute       | `esc_attr__()` / `esc_attr_e()`           |
| Allowed HTML (post content, etc.)    | `wp_kses_post( $value )`                  |
| Allowed HTML (custom allowlist)      | `wp_kses( $value, $allowed_html )`        |

### The translation-then-escape pattern

For literal strings, use the combined translate+escape functions:

```php
echo '<h2>' . esc_html__( 'Plugin Settings', 'your-text-domain' ) . '</h2>';
echo '<input type="text" placeholder="' . esc_attr__( 'Enter your API key', 'your-text-domain' ) . '">';
```

For strings with placeholders, escape both the format and each placeholder:

```php
printf(
    /* translators: %s: user display name */
    esc_html__( 'Welcome back, %s!', 'your-text-domain' ),
    esc_html( $user->display_name )
);
```

### Escape immediately before output, not "somewhere upstream"

A common mistake: escaping in a helper function, then trusting the return value. Don't:

```php
// Bad — caller has to remember the return is "safe"
function get_user_display( $user ) {
    return esc_html( $user->display_name );
}
echo get_user_display( $user );

// Good — caller explicitly escapes at the output site
function get_user_display( $user ) {
    return $user->display_name;
}
echo esc_html( get_user_display( $user ) );
```

The second form is auditable: every `echo` in the codebase has an explicit escape next to it, and you can grep for unsafe ones. The first form means a reviewer has to trace every value to its source to confirm safety.

---

## Nonces (CSRF protection)

Every state-changing request triggered by a user — form submissions, AJAX actions, admin links that perform an action — needs a nonce. The flow is:

1. **Generate** the nonce when rendering the form/link.
2. **Verify** the nonce on the server when processing the request.
3. Reject the request if verification fails.

### Forms

```php
// In the form:
<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
    <input type="hidden" name="action" value="save_my_plugin_settings">
    <?php wp_nonce_field( 'save_my_plugin_settings', 'my_plugin_nonce' ); ?>
    <!-- form fields -->
    <button type="submit"><?php esc_html_e( 'Save', 'your-text-domain' ); ?></button>
</form>

// In the handler:
function my_plugin_handle_settings_save() {
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

    // Sanitize + validate + save
}
add_action( 'admin_post_save_my_plugin_settings', 'my_plugin_handle_settings_save' );
```

### Why `wp_unslash` and `sanitize_text_field` around the nonce

`wp_verify_nonce()` is *pluggable* — another plugin can replace it. WPCS treats it as if it doesn't sanitize its input. The two wrapper calls satisfy `WordPress.Security.NonceVerification` and also genuinely protect you if a custom replacement doesn't sanitize.

The same applies to `check_admin_referer()` and `check_ajax_referer()`.

### Action links (delete, approve, etc.)

For action links rather than forms, use `wp_nonce_url()`:

```php
$delete_url = wp_nonce_url(
    add_query_arg(
        array(
            'action'  => 'delete_my_item',
            'item_id' => $item->id,
        ),
        admin_url( 'admin-post.php' )
    ),
    'delete_my_item_' . $item->id
);
```

Notice the nonce action includes the item ID — this ties the nonce to the specific item being deleted, so a stolen nonce can't delete a different item.

### AJAX

```php
// Localize the nonce to JS:
wp_localize_script( 'my-plugin-admin', 'myPluginData', array(
    'ajaxUrl' => admin_url( 'admin-ajax.php' ),
    'nonce'   => wp_create_nonce( 'my_plugin_ajax' ),
) );

// In the handler:
add_action( 'wp_ajax_my_plugin_save', 'my_plugin_ajax_save' );
function my_plugin_ajax_save() {
    check_ajax_referer( 'my_plugin_ajax', 'nonce' );

    if ( ! current_user_can( 'edit_posts' ) ) {
        wp_send_json_error( 'forbidden', 403 );
    }

    // sanitize + validate + process
    wp_send_json_success( array( 'message' => 'Saved.' ) );
}
```

`check_ajax_referer()` dies automatically if the nonce fails, so no manual check needed.

For REST API endpoints, use the `permission_callback` argument when registering routes — that's the REST-native equivalent of a nonce + capability check.

---

## Capability checks (authorization)

A nonce proves *the request came from a user*. A capability check proves *that user is allowed to do this*. Both are needed; neither replaces the other.

WordPress capabilities are documented in the [Roles and Capabilities](https://wordpress.org/documentation/article/roles-and-capabilities/) article. The ones you'll use most:

| Capability         | Typical use                                              |
| ------------------ | -------------------------------------------------------- |
| `manage_options`   | Settings pages, plugin configuration                     |
| `edit_posts`       | Anything operating on posts in general                   |
| `edit_post`, `$id` | Editing a specific post (use the meta-capability form)   |
| `delete_post`, `$id` | Deleting a specific post                               |
| `publish_posts`    | Making content public                                    |
| `upload_files`     | Media uploads                                            |
| `edit_users`       | User management                                          |
| `read`             | Any logged-in user                                       |

Use meta-capabilities (`edit_post`, `delete_post`) with the specific post ID when acting on a single object — they route through WordPress's permissions system and honor things like custom post types, multisite super-admin checks, and role plugins:

```php
if ( ! current_user_can( 'edit_post', $post_id ) ) {
    wp_die( esc_html__( 'You cannot edit this post.', 'your-text-domain' ) );
}
```

For admin pages, the cap check goes in the menu registration *and* the handler — defence in depth:

```php
add_options_page(
    __( 'My Plugin', 'your-text-domain' ),
    __( 'My Plugin', 'your-text-domain' ),
    'manage_options',  // <-- cap here
    'my-plugin-settings',
    'my_plugin_render_settings_page'
);
```

---

## SQL: use `$wpdb->prepare()` for anything with variables

WordPress provides high-level APIs (`WP_Query`, `get_posts()`, `get_user_meta()`, `wp_insert_post()`, etc.) that should be your first choice. They handle escaping and validation for you. Drop to `$wpdb` only when you genuinely need a custom query.

When you do, every value that comes from variables must go through a placeholder in `$wpdb->prepare()`:

```php
// Correct
$results = $wpdb->get_results(
    $wpdb->prepare(
        "SELECT id, name FROM {$wpdb->prefix}my_table
         WHERE user_id = %d AND status = %s AND created_at > %s
         LIMIT %d",
        $user_id,
        $status,
        $cutoff_date,
        $limit
    )
);
```

| Placeholder | Type                                |
| ----------- | ----------------------------------- |
| `%d`        | Integer                             |
| `%f`        | Float                               |
| `%s`        | String (auto-quoted)                |
| `%i`        | Identifier (table/column name) — WP 6.2+ |

### Table and column names

Table and column names can't be placeholdered in older WordPress versions, so they must come from a trusted source. Two patterns:

1. **WP 6.2+**: use `%i` for identifiers.

   ```php
   $wpdb->prepare(
       "SELECT * FROM {$wpdb->prefix}my_table ORDER BY %i %i",
       $sort_column,  // validated against allowlist
       $sort_direction  // 'ASC' or 'DESC'
   );
   ```

2. **Older WP / safer default**: build the identifier from an allowlist and interpolate:

   ```php
   $allowed_columns = array( 'created_at', 'updated_at', 'name' );
   $sort_column = in_array( $sort_column, $allowed_columns, true ) ? $sort_column : 'created_at';
   $sort_direction = 'ASC' === strtoupper( $sort_direction ) ? 'ASC' : 'DESC';

   $sql = $wpdb->prepare(
       "SELECT * FROM {$wpdb->prefix}my_table ORDER BY {$sort_column} {$sort_direction} LIMIT %d",
       $limit
   );
   ```

   PHPCS may flag the interpolation; add a targeted `phpcs:ignore` with an explanation:

   ```php
   // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared -- $sort_column and $sort_direction are validated against allowlists above.
   ```

### Caching

For `$wpdb` queries on data that doesn't change every request, WPCS will nag about caching. The pattern:

```php
$cache_key = 'my_plugin_active_users_' . $user_id;
$users = wp_cache_get( $cache_key, 'my_plugin' );

if ( false === $users ) {
    $users = $wpdb->get_results(
        $wpdb->prepare( "...", $user_id )
    );
    wp_cache_set( $cache_key, $users, 'my_plugin', HOUR_IN_SECONDS );
}
```

---

## File operations

`file_get_contents()` and friends are usually fine for local files, but if the path comes from user input, validate it against an allowlist of directories *and* use `realpath()` to defeat traversal attacks:

```php
$base = realpath( WP_CONTENT_DIR . '/my-plugin-data/' );
$requested = realpath( $base . '/' . $user_supplied_filename );

if ( ! $requested || 0 !== strpos( $requested, $base . DIRECTORY_SEPARATOR ) ) {
    wp_die( esc_html__( 'Invalid file path.', 'your-text-domain' ) );
}

$contents = file_get_contents( $requested );
```

For remote URLs, use `wp_remote_get()` / `wp_remote_post()`, not raw cURL or `file_get_contents()`. They respect WordPress's HTTP API filters, honor proxy config, and have a unified error interface.

For file uploads, never trust the file's claimed MIME type from the browser. Use `wp_check_filetype()` against an allowlist:

```php
$allowed_mimes = array(
    'jpg|jpeg' => 'image/jpeg',
    'png'      => 'image/png',
    'pdf'      => 'application/pdf',
);
$filetype = wp_check_filetype( $file['name'], $allowed_mimes );

if ( empty( $filetype['ext'] ) ) {
    wp_die( esc_html__( 'File type not allowed.', 'your-text-domain' ) );
}
```

---

## Discouraged functions

WPCS will flag these. Use the WordPress alternative:

| Don't                      | Do                                                |
| -------------------------- | ------------------------------------------------- |
| `curl_*`                   | `wp_remote_get()` / `wp_remote_post()`            |
| `file_get_contents( $url )`| `wp_remote_get()`                                 |
| `json_encode()`            | `wp_json_encode()`                                |
| `parse_url()`              | `wp_parse_url()`                                  |
| `rand()` / `mt_rand()`     | `wp_rand()`                                       |
| `serialize()` of unknown   | Don't — never `unserialize()` untrusted data      |
| `strip_tags()`             | `wp_strip_all_tags()` or `wp_kses()`              |
| `date()`                   | `gmdate()` or `wp_date()` (locale-aware)          |
| Direct `$_SERVER['HTTP_HOST']` | `home_url()` / `get_site_url()`               |
| `error_log()`              | OK for development; never leave in production code |
| `var_dump`, `print_r` to output | Never in production                          |

---

## Checklist before declaring a feature "done"

- [ ] Every read from a superglobal is wrapped in `wp_unslash()` + the appropriate sanitizer.
- [ ] Every sanitized value is validated before use (especially IDs, enums, dates).
- [ ] Every state-changing endpoint has a nonce check.
- [ ] Every state-changing endpoint has a capability check matching the action's sensitivity.
- [ ] Every `echo` of dynamic data has an explicit escape function next to it.
- [ ] Every translated string uses the project's text domain literally, not via a variable.
- [ ] Every `$wpdb` query with variables uses `prepare()` with placeholders.
- [ ] No raw `curl_*`, `json_encode`, `parse_url`, `rand` — use the `wp_*` equivalents.
- [ ] No leftover `var_dump`, `print_r`, `error_log` calls outside dev-only paths.