# Wordlists

## Summary

- A wordlist is a text file where each line is a path.
- In ordinary wordlists, dirsearch replaces the `%EXT%` keyword with extensions from the `-e` flag.
- For wordlists without `%EXT%`, such as [SecLists](https://github.com/danielmiessler/SecLists), use `-f` / `--force-extensions` to append extensions and `/` to every wordlist entry.
- To apply selected extensions to entries that already have extensions, use `--overwrite-extensions`.
- Some extensions are excluded from overwrite behavior, such as `.log`, `.json`, `.xml`, and media extensions like `.jpg` and `.png`.
- Multiple wordlists can be separated with commas, for example `wordlist1.txt,wordlist2.txt`.
- Bundled wordlist categories live in `db/categories/` and can be selected with `--wordlist-categories`.
- Wordlist generation uses `--wordlist-backend=auto` by default. `python` selects the built-in backend and `native` requires a native backend build.
- Template wordlists live in `db/templates/` and support placeholders.
- Use `--wordlist-status` to preview resolved wordlist files and generated entry count before scanning.
- Use `--wordlist-max-size` to cap generation.

## Extensions

Normal extension replacement:

```text
index.%EXT%
```

Passing `asp` and `aspx` as extensions generates:

```text
index
index.asp
index.aspx
```

Force extensions:

```text
admin
```

Passing `php` and `html` as extensions with `-f` / `--force-extensions` generates:

```text
admin
admin.php
admin.html
admin/
```

Overwrite extensions:

```text
login.html
```

Passing `jsp` and `jspa` as extensions with `--overwrite-extensions` generates:

```text
login.html
login.jsp
login.jspa
```

## Categories

Bundled wordlist categories are stored in `db/categories/`.

Available categories:

- `extensions`
- `conf`
- `vcs`
- `backups`
- `db`
- `logs`
- `keys`
- `web`
- `common`
- `aggressive` (opt-in payloads likely to trigger WAF rules)

The default `db/dicc.txt` and `common` category omit `aggressive` entries. Select
that category explicitly when those payloads are appropriate for the target.
The `all` category selector also includes `aggressive`.

```sh
python3 dirsearch.py -u https://target --wordlist-categories aggressive
```

Use `all` to include everything:

```sh
python3 dirsearch.py -u https://target --wordlist-categories all
```

## Templates

Template wordlists live in `db/templates/` and support these placeholders:

- `%EXT%`: extensions supplied with `-e` / `--extensions`.
- `%SUBJECT%`: common resources such as users, accounts, posts, products, orders, and invoices.
- `%CRUD_OP%`: create, read, update, delete, list, get, add, edit, remove, and search.
- `%AUTH_OP%`: login, logout, signin, signout, signup, register, reset, forgot, password, oauth, and sso.
- `%ADMIN_OP%`: admin, dashboard, panel, manage, settings, users, roles, and permissions.
- `%ENV%`: dev, development, test, stage, staging, prod, production, and local.
- `%SEP%`: separators `-`, `_`, `.`, and `/`.
- `%DB%` and its compatibility alias `%DB_ENGINE%`: mysql, postgres, postgresql, sqlite, mariadb, mongodb, and redis.
- `%ARCHIVE%` and its compatibility alias `%ARCHIVE_EXT%`: zip, tar, tar.gz, tgz, gz, 7z, rar, and bak.
- `%BACKUP%` and its alias `%BACKUP_EXT%`: the archive values plus bkp, bkup, old, swn, and swp.
- `%API_VERSION%`: v1, v2, v3, v4, latest, and beta.
- `%YYYY%`, `%YY%`, `%MM%`, and `%DD%`: components of the current date when the wordlist is generated.
- `%DATE%`: the current date in `YYYY-MM-DD` form.
- `%DATE_COMPACT%`: the current date in `YYYYMMDD` form.
- `%CATEGORY:name%`: entries from `db/categories/name.txt` or a mapped bundled category.

Repeated placeholders reuse the same value within a line. Distinct placeholders
expand as a Cartesian product, unknown placeholders remain unchanged, and
placeholders with no values emit no entries.

Preview resolved files and generated entry counts without scanning:

```sh
python3 dirsearch.py -u https://target --wordlist-status
```

Limit generated entries:

```sh
python3 dirsearch.py -u https://target --wordlist-max-size 500000
```

## Prefixes and Suffixes

Use `--prefixes` to add custom prefixes to all entries:

```sh
python3 dirsearch.py -e php -u https://target --prefixes .,admin,_
```

Wordlist:

```text
tools
```

Generated with prefixes:

```text
tools
.tools
admintools
_tools
```

Use `--suffixes` to add custom suffixes to all entries:

```sh
python3 dirsearch.py -e php -u https://target --suffixes ~
```

Wordlist:

```text
index.php
internal
```

Generated with suffixes:

```text
index.php
internal
index.php~
internal~
```

## Wordlist Formats

Supported transformations: lowercase, uppercase, and capitalization.

Lowercase:

```text
admin
index.html
```

Uppercase:

```text
ADMIN
INDEX.HTML
```

Capital:

```text
Admin
Index.html
```

## Exclude Extensions

Use `--exclude-extensions` with an extension list to remove all paths in the wordlist that contain the given extensions.

```sh
python3 dirsearch.py -u https://target --exclude-extensions jsp
```

Wordlist:

```text
admin.php
test.jsp
```

After:

```text
admin.php
```
