# Add-on translations

Each `<locale>.json` file maps the **English** text used in the code to its translation. The file name is Blender's locale code (`pt_BR`, `es`, `fr_FR`, `de_DE`, …); see Blender → Preferences → Interface → Language.

To add a language:

1. Copy `pt_BR.json` to `<locale>.json` and translate the values. Keep `{placeholders}` exactly as they are.
2. List the strings that are still missing: `python3 blender_addon/tests/test_i18n.py <locale>`
3. Run the tests: `uvx pytest blender_addon/tests`. They fail when a string is missing or a placeholder does not match.

Blender switches language from its own setting. Turn on Preferences → Interface → Translation → "Interface" and "Tooltips".
