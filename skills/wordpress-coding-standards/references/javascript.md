# JavaScript

WordPress has its own JavaScript Coding Standards, layered on top of the jQuery style guide with some WordPress-specific differences. The standards have evolved as the block editor (Gutenberg) brought modern JS/React patterns into WordPress core; what follows captures both worlds since most plugins straddle them.

Load this reference when working on:

- Admin scripts (settings page UI, meta box scripts)
- Block editor blocks (`registerBlockType`, edit/save components)
- Block editor sidebars, slots, fills
- Front-end scripts (subject to the same standards even if simpler)
- Anything in a plugin's `js/`, `src/`, or `assets/js/` directory

---

## The two JS worlds in WordPress

| World                          | Tools                                          | Style                                       |
| ------------------------------ | ---------------------------------------------- | ------------------------------------------- |
| **Classic admin / front-end** | Vanilla JS, possibly jQuery, no build step    | WordPress JS Coding Standards (this file)   |
| **Block editor / modern**     | React, JSX, `@wordpress/*` packages, `@wordpress/scripts` build | WordPress + `@wordpress/eslint-plugin` defaults |

The two share most rules. The modern world adds React-specific conventions and modern syntax that the classic world either avoids or transpiles.

Pick the world that matches the project. Most plugins built since 2020 lean modern even for admin pages, using `@wordpress/scripts` to bundle and `@wordpress/components` for UI.

---

## Common rules (both worlds)

### Indentation

Tabs for indentation, same as PHP. This is one of the places WordPress differs from common JS conventions (which typically use 2 or 4 spaces).

### Quotes

Single quotes for strings. Double quotes only when the string contains a single quote, or for JSX attributes:

```js
const greeting = 'Hello';
const message  = "Don't worry";

// JSX uses double quotes for attributes by convention
<Button label="Save" />
```

### Semicolons

Always. ASI (automatic semicolon insertion) has corner cases that bite when you don't expect them; explicit semicolons remove the ambiguity:

```js
const x = 1;
const y = 2;
return x + y;
```

### Braces and `if` style

Same as PHP: opening brace on the same line, always use braces even for single-statement bodies:

```js
if ( isValid ) {
    save();
}

if ( hasError ) {
    showError();
} else if ( isWarning ) {
    showWarning();
} else {
    showSuccess();
}
```

### Spaces inside parens

Same as PHP — space inside parens for function calls and control structures:

```js
if ( condition ) {
    doSomething( arg1, arg2 );
}
```

Empty parens have no internal space:

```js
function noop() {
    return [];
}
```

### Naming

JavaScript uses `camelCase` for variables and functions (this is where it differs from PHP's `snake_case`):

```js
const userName = getUserName();
function calculateTotal( items ) { /* ... */ }
```

Classes and React components use `PascalCase`:

```js
class SettingsManager { /* ... */ }
function SettingsPanel( props ) { /* ... */ }
```

Constants that are truly compile-time invariants use `UPPER_SNAKE_CASE`:

```js
const MAX_ITEMS = 100;
const API_BASE  = '/wp-json/my-plugin/v1';
```

Regular `const` declarations of computed values stay camelCase — `const` doesn't automatically mean "constant" in the SCREAMING_SNAKE sense.

### Equality

Strict (`===`, `!==`) always. Loose equality (`==`, `!=`) is banned by the standards for the same reason as in PHP.

### Comments

`//` for single-line, `/* */` for blocks, `/** */` for JSDoc:

```js
// Single-line comment.

/*
 * Multi-line comment for longer explanations.
 */

/**
 * JSDoc block for a function.
 *
 * @param {string} name The user's name.
 * @return {string} A greeting.
 */
function greet( name ) {
    return `Hello, ${ name }`;
}
```

### Template literals

Use template literals for string interpolation; they're clearer than `+` concatenation:

```js
// Good
const url = `${ apiBase }/users/${ userId }`;

// Less good
const url = apiBase + '/users/' + userId;
```

Note the spaces inside `${ }` — WPCS-style JS puts spaces inside the placeholder delimiters too.

---

## jQuery (classic admin only)

Some plugins still use jQuery for admin scripts. The rules:

### Use `jQuery`, not `$`

WordPress loads jQuery in no-conflict mode. `$` may be claimed by another library. Use the full name, or alias it inside an IIFE:

```js
( function( $ ) {
    $( document ).on( 'click', '.my-button', function() {
        $( this ).addClass( 'clicked' );
    } );
} )( jQuery );
```

The IIFE pattern is conventional — it scopes `$` to the wrapper without polluting the global.

### Selectors

Cache selectors when used more than once:

```js
// Bad — re-queries the DOM each time
$( '.my-element' ).addClass( 'a' );
$( '.my-element' ).addClass( 'b' );

// Good
const $element = $( '.my-element' );
$element.addClass( 'a' );
$element.addClass( 'b' );
```

The `$` prefix on the variable name signals "this is a jQuery-wrapped element", a convention worth keeping for readability.

---

## Modern (Block editor / React)

For block development and modern admin UIs:

### Use `@wordpress/scripts`

Don't roll your own Webpack/Babel config. `@wordpress/scripts` includes the standard build with all the right presets:

```bash
npm install --save-dev @wordpress/scripts
```

```json
// package.json
{
  "scripts": {
    "build": "wp-scripts build",
    "start": "wp-scripts start",
    "lint:js": "wp-scripts lint-js"
  }
}
```

### React-specific conventions

Function components, hooks, JSX:

```jsx
import { useState } from '@wordpress/element';
import { TextControl, Button } from '@wordpress/components';
import { __ } from '@wordpress/i18n';

function SettingsPanel( { initialValue, onSave } ) {
    const [ value, setValue ] = useState( initialValue );

    return (
        <div className="my-plugin-settings">
            <TextControl
                label={ __( 'API Key', 'my-awesome-plugin' ) }
                value={ value }
                onChange={ setValue }
            />
            <Button
                variant="primary"
                onClick={ () => onSave( value ) }
            >
                { __( 'Save', 'my-awesome-plugin' ) }
            </Button>
        </div>
    );
}

export default SettingsPanel;
```

Notes:

- Import from `@wordpress/element`, not `react` directly. It's an aliased re-export that ensures you get the version WordPress is shipping.
- Use `@wordpress/components` for built-in UI — `Button`, `TextControl`, `SelectControl`, `Notice`, `Panel`, etc. They're styled to match the admin and accessible by default.
- Use `@wordpress/i18n` for translations. The `__()` function works just like its PHP counterpart, including text domains.
- JSX attributes use double quotes; expressions use `{ }` with spaces inside.

### i18n in JS

```js
import { __, _x, _n, sprintf } from '@wordpress/i18n';

const label = __( 'Settings', 'my-awesome-plugin' );

const message = sprintf(
    /* translators: %d: number of items */
    _n(
        '%d item selected.',
        '%d items selected.',
        count,
        'my-awesome-plugin'
    ),
    count
);
```

The `/* translators: */` comment goes immediately before the call, same as in PHP.

To make these translatable end-to-end, run `wp i18n make-pot` from WP-CLI (with the JS support flag) to extract strings, and use the `wp-set-script-translations` PHP helper to associate translations with your enqueued script:

```php
wp_set_script_translations( 'my-plugin-admin', 'my-awesome-plugin', plugin_dir_path( __FILE__ ) . 'languages' );
```

### Hooks (React hooks, not WP hooks)

Standard React rules apply:

- Only call hooks at the top level of a component, never inside conditionals or loops
- Custom hook names start with `use`
- Dependency arrays in `useEffect` / `useMemo` / `useCallback` must list every value from the surrounding scope they reference

### Block registration

The modern block registration pattern uses `block.json` as the source of truth and a thin `index.js` that registers the edit/save components:

```js
// src/index.js
import { registerBlockType } from '@wordpress/blocks';
import Edit from './edit';
import save from './save';
import metadata from './block.json';

registerBlockType( metadata.name, {
    edit: Edit,
    save,
} );
```

`block.json` describes the block (name, title, icon, attributes, supports, etc.) and is the single source of truth WordPress reads at registration time.

---

## ESLint

Use `@wordpress/eslint-plugin` (bundled with `@wordpress/scripts`). It includes the WordPress coding standards plus the React rules.

A minimal `.eslintrc.json`:

```json
{
  "extends": [ "plugin:@wordpress/eslint-plugin/recommended" ]
}
```

For projects without `@wordpress/scripts`, install separately:

```bash
npm install --save-dev eslint @wordpress/eslint-plugin
```

Add a script:

```json
{
  "scripts": {
    "lint:js": "eslint 'src/**/*.{js,jsx}' 'js/**/*.js'"
  }
}
```

---

## Common pitfalls

### Don't pollute the global scope

Wrap classic scripts in an IIFE; for modern code, use modules.

### Always enqueue, never inline

Use `wp_enqueue_script()` from PHP to load JS, not inline `<script>` tags. Inline scripts can't be deduplicated, can't be deferred, and don't participate in the dependency graph.

### Localize, don't inline server data

To pass PHP data to JS, use `wp_localize_script()` or the newer `wp_add_inline_script()`:

```php
wp_localize_script( 'my-plugin-admin', 'myPluginData', array(
    'ajaxUrl' => admin_url( 'admin-ajax.php' ),
    'nonce'   => wp_create_nonce( 'my_plugin_ajax' ),
    'i18n'    => array(
        'confirmDelete' => __( 'Really delete?', 'my-awesome-plugin' ),
    ),
) );
```

Then in JS: `myPluginData.nonce`, `myPluginData.i18n.confirmDelete`.

### Treat data from the server as untrusted

Even data your own PHP sent down. Another plugin's filter might have modified it. Same defence-in-depth principle as escaping in PHP — when rendering user-supplied or otherwise dynamic data into the DOM, use `textContent` not `innerHTML`, or use the React equivalent (just pass strings as children; React handles escaping automatically).

---

## Checklist

- [ ] Tabs for indentation.
- [ ] Single quotes for JS strings; double for JSX attributes.
- [ ] Semicolons everywhere.
- [ ] `===` / `!==` only — no loose equality.
- [ ] `camelCase` for variables/functions, `PascalCase` for classes/components, `UPPER_SNAKE_CASE` only for true constants.
- [ ] Spaces inside parens and `${ }` placeholders.
- [ ] Translations use `@wordpress/i18n` with the project's text domain.
- [ ] `/* translators: */` comments above `sprintf` / `_n` calls.
- [ ] No inline `<script>` tags; everything enqueued via PHP.
- [ ] PHP→JS data passes through `wp_localize_script` / `wp_add_inline_script`, never echoed mid-page.
- [ ] React components import from `@wordpress/element`, not `react`.
- [ ] Block registration uses `block.json` as source of truth.