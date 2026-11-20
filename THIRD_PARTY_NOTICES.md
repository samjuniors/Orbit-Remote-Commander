# Third-party code and attribution

## DesktopCommanderMCP (MIT)

Orbit Remote Commander intentionally adapts **a narrow, audited subset** of
DesktopCommanderMCP's local-source techniques rather than embedding its entire
privileged execution server.

- Upstream: https://github.com/wonderwhy-er/DesktopCommanderMCP
- Pinned reference commit: 9a101b17e44577f0baefa4c7120f087881c5cc56
- Relevant upstream files: src/utils/lineEndingHandler.ts (line-ending
  detection and normalization), src/tools/edit.ts (exact block match/count/
  replace logic); their ideas are ported and reduced in
  src/orbit_rc_text_ops.py.
- See docs/RESEARCH-DESKTOPCOMMANDER-MCP.md for overlap, alternatives and
  deferred/unsafe features.
- No DesktopCommander branded assets, customer accounts, telemetry, remote
  gateway, device-authentication code, process execution, or full package was
  imported.
- Their license permits modification and redistribution, **provided this
  copyright and permission notice is retained**.

The following is the unmodified MIT license notice from the upstream LICENSE
at the pinned reference commit:

MIT License

Copyright (c) 2024-2025 Eduard Ruzga and Desktop Commander Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Orbit licensing

The repository owner has not selected a project-wide license for original
Orbit Remote Commander code. The upstream MIT notice above **does not** grant
a blanket license to the independently written portions of this repository.
A project-wide license and public distribution decision remain owner gates.
