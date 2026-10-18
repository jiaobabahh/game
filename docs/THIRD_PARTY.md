# Browser runtime dependencies

This website serves its runtime dependencies from the same GitHub Pages origin.
No external model key is included.

- Pyodide 0.29.3, Mozilla Public License 2.0: https://github.com/pyodide/pyodide
- CPython standard library, Python Software Foundation License: https://docs.python.org/3/license.html
- SymPy 1.13.3, BSD: bundled wheel includes its license.
- mpmath 1.3.0, BSD: bundled wheel includes its license.
- NetworkX 3.4.2, BSD: bundled wheel includes its license.

Runtime files were downloaded from the versioned official Pyodide distribution
at https://cdn.jsdelivr.net/pyodide/v0.29.3/full/.
Wheel SHA-256 values were verified against pyodide-lock.json before publication.
