#!/usr/bin/env python3

# Copyright © 2025-2026 Wenze Wei. All Rights Reserved.
#
# This file is part of Encre Agent.
# The Encre Agent project belongs to the Dunimd Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# DISCLAIMER: Users must comply with applicable AI regulations.
# Non-compliance may result in service termination or legal liability.

"""ea-plugin-cli -- the Encre Agent plugin market unified toolchain.

This package provides the ``encre-plugin`` command-line interface that
authours use to scaffold, build, verify, and publish ``ea-plugin-*``
packages into the central Encre Agent plugin registry.

The package is structured so that pure publishing rules (distribution-name
policy, manifest validation, catalog-entry construction) live in
:mod:`ea_plugin_cli.rules` and can be imported by the registry CI without
requiring ``encre-harness`` or any plugin code to be installed.  The CLI
entry-point logic that drives argparse and subprocess orchestration lives
in :mod:`ea_plugin_cli.__main__`.
"""

from __future__ import annotations

__version__ = "0.1.0"
