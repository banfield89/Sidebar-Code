# Nested skill — dummy fixture

This file lives inside a subfolder of `dummy_deliverable/`. It exists so
that `test_build_zip_preserves_folder_structure` can assert that nested
paths inside the source directory are preserved verbatim inside the zip.

If this file's path inside the resulting zip is anything other than
`dummy_deliverable/nested_skill/SKILL.md`, the test fails.
