# Code of Conduct — Naming Conventions

This repository has two hard rules:

1. **All file names are lower case.**
2. **All identifiers are lower case snake_case**:
   - variables, constants, parameters
   - functions and methods
   - classes
3. **All test classes are snake_case prefixed with the first letter of test_ capital , i.e. Test_**

> Example: `data_loader.py` with `class data_loader`, `def load_data(...)`, and variable `batch_size` , and test class `Test_config`.

## Rationale

Consistent naming reduces cognitive load and merge conflicts, makes grepping easier, and avoids case-sensitive surprises across operating systems.

## Enforcement

- A **pre-commit** hook blocks commits with any uppercase characters in file names.
- **Pylint** is configured to require `snake_case` for variables, functions, methods, **and classes**.
- CI must pass before merge; PRs that violate these rules will be closed or must be fixed.

## Contributor Expectations

- Run `pre-commit install` after cloning.
- Fix any lint errors before pushing.
- Rename files to all-lowercase (e.g., `MyModule.py` → `mymodule.py`).

## Exceptions

- None. If an upstream dependency forces a different name, wrap it locally with compliant names.
