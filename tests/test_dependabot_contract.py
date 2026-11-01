"""Offline compatibility contract, not a hosted Dependabot integration test.

Ports provider_declaration_regex and update_registry_declaration from:
https://github.com/dependabot/dependabot-core/blob/510dd5e861be74ddc533083fe8b9953a66670f2f/terraform/lib/dependabot/terraform/file_updater.rb
Copyright GitHub, Inc.; MIT license in LICENSE.dependabot beside this file.
"""
import re
from pathlib import Path

import pytest


def update_requirement(content, provider, old, replacement):
    name = re.escape(provider)
    registry = re.escape("registry.terraform.io")
    # Ruby /m is dot-all; Ruby ^/$ are always line anchors.
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    version_first = re.compile(
        rf'''(((?<!required_)version\s=\s*["'].*["'])(\s*source\s*=\s*["']({registry}/)?{name}["']|\s*{name}\s*=\s*\{{.*))''', flags
    )
    source_first = re.compile(
        rf'''((source\s*=\s*["']({registry}/)?{name}["']|\s*{name}\s*=\s*\{{.*)(?:(?!^\}}).)+)''', flags
    )
    declaration = version_first if version_first.search(content) else source_first
    version = re.compile(rf'''^\s*version\s*=\s*["'].*{re.escape(old)}.*['"]''', re.MULTILINE)
    return declaration.sub(
        lambda block: version.sub(lambda line: line[0].replace(old, replacement, 1), block[0], count=1), content
    )


def provider_requirements(content):
    # Independently discover flat source/version objects, including inline HCL.
    requirements = {}
    for block in re.finditer(r"[\w-]+\s*=\s*\{([^{}]*)\}", content):
        source = re.search(r'\bsource\s*=\s*"([^"]+)"', block[1])
        version = re.search(r'\bversion\s*=\s*"([^"]+)"', block[1])
        if source and version:
            start = block.start(1) + version.start(1)
            requirements[source[1]] = (version[1], start, start + len(version[1]))
    return requirements


@pytest.mark.parametrize("provider", ["hashicorp/azurerm", "hashicorp/random"])
def test_checked_in_provider_can_update_without_other_changes(provider):
    content = (Path(__file__).resolve().parents[1] / "terraform" / "versions.tf").read_text()
    requirements = provider_requirements(content)
    assert set(requirements) == {"hashicorp/azurerm", "hashicorp/random"}
    old, start, end = requirements[provider]
    replacement = "999.0.0"  # Synthetic requirement used only in memory.
    assert old != replacement
    # Full-file equality protects required_version and the other provider.
    assert update_requirement(content, provider, old, replacement) == content[:start] + replacement + content[end:]


def test_inline_fixture_reproduces_failed_dependabot_update():
    content = ('terraform {\n  required_providers {\n'
               '    example = { source = "hashicorp/example", version = "~> 1.0" }\n'
               '  }\n}\n')
    assert len(provider_requirements(content)) == 1
    assert update_requirement(content, "hashicorp/example", "~> 1.0", "~> 2.0") == content
