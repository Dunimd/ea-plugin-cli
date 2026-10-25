#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from __future__ import annotations

"""PyInstaller entry point for the standalone ``encre-plugin`` executable.

When ``ea_plugin_cli/__main__.py`` is executed as ``__main__.py`` inside a
PyInstaller-frozen executable, its relative imports (e.g. ``from .rules import``)
break because the frozen environment flattens the package namespace.  This
file serves as a thin, top-level launcher that imports the real
``main()`` from ``ea_plugin_cli.__main__`` and delegates to it.  The build
pipeline (``python build.py cli``) points PyInstaller at this module as the
entry point so the compiled binary behaves correctly.
"""

from ea_plugin_cli.__main__ import main

if __name__ == "__main__":
    main()
