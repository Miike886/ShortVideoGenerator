# Temporary artifact hygiene

## Status and Objective

Completed. Keep pytest/runtime scratch output out of publication workflows so branch, commit,
and pull-request preparation only stages source, tests, documentation, and intended
configuration.

## Delivered Behavior

- Added `.test-temp/` to `.gitignore`.
- Existing `.test-temp/` files remain local working artifacts and are excluded from
  `git ls-files --others --exclude-standard`.

## Important Files

- `.gitignore`
- `docs/features/README.md`
- `docs/CHANGELOG.md`

## Validation

- `git diff --check` passed after the ignore update.
- `git ls-files --others --exclude-standard` no longer reports `.test-temp/` entries.

## Known Limitations

- The directory is not removed automatically because it can contain local test output owned by
  the current workspace.
