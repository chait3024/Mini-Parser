# Mini-Parser
A lightweight Python IDE with a custom regex tokenizer, recursive descent parser, and visual syntax error diagnostics for C-style variable declarations.
## Overview

**Mini Parser IDE** is a minimalist, dark-themed code editor and syntax analyzer built in Python using Tkinter. It implements a custom lexical tokenizer and recursive descent parser in [`main.py`](main.py) to validate C-style variable declarations.

### Key Features
- **Custom Lexer & Parser:** Built-in regex tokenizer and recursive descent parser validating multi-variable declarations (e.g., `int a;`, `float x, y, z;`).
- **Real-Time Editor:** VS Code-inspired dark UI with line numbers, active line indicators, and live syntax highlighting.
- **Visual Diagnostics:** In-editor inline error highlights and a bottom "Problems" panel displaying exact line and column numbers for syntax errors.
