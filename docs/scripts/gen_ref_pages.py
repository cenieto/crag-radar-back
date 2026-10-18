"""Generate one API reference page per module in ``src/`` and the navigation that lists them."""

from pathlib import Path

import mkdocs_gen_files

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
SOURCE_DIR: Path = PROJECT_ROOT / "src"
REFERENCE_DIR: Path = Path("reference")

navigation: mkdocs_gen_files.Nav = mkdocs_gen_files.Nav()

module_path: Path
for module_path in sorted(SOURCE_DIR.rglob("*.py")):
    module_relative_path: Path = module_path.relative_to(SOURCE_DIR).with_suffix("")
    module_parts: tuple[str, ...] = module_relative_path.parts
    page_path: Path = module_relative_path.with_suffix(".md")

    is_package_init: bool = module_parts[-1] == "__init__"
    if is_package_init:
        module_parts = module_parts[:-1]
        page_path = page_path.with_name("index.md")

    is_private_module: bool = module_parts[-1].startswith("_")
    if is_private_module:
        continue

    navigation[module_parts] = page_path.as_posix()
    with mkdocs_gen_files.open(REFERENCE_DIR / page_path, "w") as reference_page:
        reference_page.write(f"::: {'.'.join(module_parts)}\n")
    mkdocs_gen_files.set_edit_path(REFERENCE_DIR / page_path, module_path.relative_to(PROJECT_ROOT))

with mkdocs_gen_files.open(REFERENCE_DIR / "SUMMARY.md", "w") as navigation_file:
    navigation_file.writelines(navigation.build_literate_nav())
