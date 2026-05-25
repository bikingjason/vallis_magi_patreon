# Python style

When writing Python code:

- Use modern Python type hints.
- Prefer built-in generic types: `list[str]`, `dict[str, int]`, `tuple[int, ...]`, `set[str]`.
- Do not use bare container types such as `list`, `dict`, `tuple`, or `set` in function signatures.
- Use `| None` instead of `Optional[...]`.
- Use clear return types on functions.
- Target Python 3.14+ unless told otherwise.
