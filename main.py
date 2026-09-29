import tkinter as tk
from tkinter import messagebox
import re


# ------------------ TOKENIZER ------------------
def tokenize(input_string: str):
    token_specification = [
        ("TYPE", r"\b(int|float|char)\b"),
        ("ID", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
        ("COMMA", r","),
        ("SEMICOLON", r";"),
        # Treat newlines like normal whitespace so we can tokenize the whole editor at once.
        ("SKIP", r"[ \t\n]+"),
        ("MISMATCH", r"."),
    ]

    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specification)
    tokens = []

    def get_line_col(pos: int):
        # 1-based line, 1-based col
        lines = input_string[:pos].split("\n")
        line = len(lines)
        col = len(lines[-1]) + 1
        return line, col

    for match in re.finditer(tok_regex, input_string):
        kind = match.lastgroup
        value = match.group()
        pos = match.start()

        line_num, col_num = get_line_col(pos)

        if kind == "SKIP":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"{line_num}:{col_num}: Unexpected character '{value}'")

        tokens.append((kind, value, line_num, col_num))

    return tokens


# ------------------ PARSER ------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type):
        token = self.current_token()
        if token and token[0] == expected_type:
            self.pos += 1
            return

        if token:
            line, col = token[2], token[3]
            raise SyntaxError(f"{line}:{col}: Expected {expected_type}")
        raise SyntaxError("EOF: Unexpected end of input")

    def parseProgram(self):
        while self.current_token():
            self.parseDeclaration()

    def parseDeclaration(self):
        token = self.current_token()
        if not token:
            raise SyntaxError("EOF: Expected type")
        line, col = token[2], token[3]

        self.parseType()

        token = self.current_token()
        if not token or token[0] != "ID":
            raise SyntaxError(f"{line}:{col}: Invalid identifier")

        self.consume("ID")

        while self.current_token() and self.current_token()[0] == "COMMA":
            comma_token = self.current_token()
            self.consume("COMMA")

            token = self.current_token()
            if not token or token[0] != "ID":
                line, col = comma_token[2], comma_token[3]
                raise SyntaxError(f"{line}:{col}: Expected identifier after ','")

            self.consume("ID")

        token = self.current_token()
        if not token:
            raise SyntaxError(f"{line}:{col}: Missing ';'")
        if token[0] == "SEMICOLON":
            self.consume("SEMICOLON")
            return

        line, col = token[2], token[3]
        raise SyntaxError(f"{line}:{col}: Syntax error")

    def parseType(self):
        token = self.current_token()
        if token and token[0] == "TYPE":
            self.consume("TYPE")
            return

        if token:
            line, col = token[2], token[3]
            raise SyntaxError(f"{line}:{col}: Invalid type")
        raise SyntaxError("EOF: Expected type")


# ------------------ UI ------------------
root = tk.Tk()
root.title("Mini Parser IDE")
root.geometry("900x650")
root.configure(bg="#1e1e1e")

FONT = ("Consolas", 12)
BG = "#1e1e1e"
FG = "#ffffff"
LINE_BG = "#2b2b2b"

main_frame = tk.Frame(root, bg=BG)
main_frame.pack(fill="both", expand=True)

editor_frame = tk.Frame(main_frame, bg=BG)
editor_frame.pack(fill="both", expand=True)

line_numbers = tk.Text(
    editor_frame, width=4, bg=LINE_BG, fg="#888", state="disabled", font=FONT, bd=0
)
line_numbers.pack(side="left", fill="y")

text_area = tk.Text(
    editor_frame,
    bg=BG,
    fg=FG,
    insertbackground="white",
    font=FONT,
    bd=0,
    undo=True,
)
text_area.pack(side="left", fill="both", expand=True)

scrollbar = tk.Scrollbar(editor_frame)
scrollbar.pack(side="right", fill="y")

text_area.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_area.yview)

# Error display box (like VS Code problems panel)
error_box = tk.Text(root, height=6, bg="#111", fg="#ff5555", font=("Consolas", 10), bd=0)
error_box.pack(fill="x")

bottom_frame = tk.Frame(root, bg="#2b2b2b")
bottom_frame.pack(fill="x")


def update_line_numbers(event=None):
    lines = text_area.get("1.0", "end-1c").split("\n")
    nums = "\n".join(str(i + 1) for i in range(len(lines)))

    line_numbers.config(state="normal")
    line_numbers.delete("1.0", tk.END)
    line_numbers.insert("1.0", nums)
    line_numbers.config(state="disabled")


def highlight_current_line(event=None):
    text_area.tag_remove("current_line", "1.0", tk.END)
    text_area.tag_add("current_line", "insert linestart", "insert lineend")
    text_area.tag_config("current_line", background="#2a2d2e")


def syntax_highlight(event=None):
    text_area.tag_remove("type", "1.0", tk.END)

    content = text_area.get("1.0", "end-1c")
    for match in re.finditer(r"\b(int|float|char)\b", content):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        text_area.tag_add("type", start, end)

    text_area.tag_config("type", foreground="#569cd6")


def highlight_error(line: int, col: int):
    # Tk text columns are 0-based, our tokenizer columns are 1-based.
    start = f"{line}.{max(col - 1, 0)}"
    end = f"{line}.{max(col, 1)}"

    tag_name = f"error_{line}_{col}"
    text_area.tag_add(tag_name, start, end)
    text_area.tag_config(tag_name, background="#ff5555", foreground="white")


# ------------------ RUN PARSER ------------------
def run_parser():
    code = text_area.get("1.0", "end-1c")

    # Clear old error highlights
    for tag in list(text_area.tag_names()):
        if tag.startswith("error_"):
            text_area.tag_delete(tag)

    error_box.delete("1.0", tk.END)

    lines = code.split("\n")
    error_count = 0

    for editor_line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        try:
            tokens = tokenize(line)
            Parser(tokens).parseProgram()
        except SyntaxError as e:
            error_count += 1
            msg = str(e)

            # Our tokenizer/parser report line numbers relative to the string they saw.
            # Since we parse one editor line at a time, always map to the real editor line.
            col_no = 1
            error_msg = msg

            if msg.startswith("EOF:"):
                # Put caret at end of the line for EOF-ish errors.
                col_no = len(line) + 1
                error_msg = msg.split(":", 1)[1].strip() if ":" in msg else msg
            elif ":" in msg:
                parts = msg.split(":", 2)
                if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                    col_no = int(parts[1])
                    error_msg = parts[2].strip()

            highlight_error(editor_line_no, col_no)
            error_box.insert(
                tk.END, f"Line {editor_line_no}, Col {col_no}: {error_msg}\n"
            )

    if error_count > 0:
        status.config(text=f"{error_count} error(s)")
    else:
        status.config(text="Success")
        messagebox.showinfo("Result", "All declarations are valid")


run_button = tk.Button(
    bottom_frame,
    text="▶ Run Parser",
    command=run_parser,
    bg="#007acc",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padx=10,
    pady=4,
    cursor="hand2",
)
run_button.pack(side="left", padx=10, pady=5)

status = tk.Label(bottom_frame, text="Ready", bg="#2b2b2b", fg="white", anchor="e")
status.pack(side="right", padx=10)

# -------- Bindings --------
text_area.bind("<KeyRelease>", update_line_numbers)
text_area.bind("<KeyRelease>", highlight_current_line, add=True)
text_area.bind("<KeyRelease>", syntax_highlight, add=True)

update_line_numbers()
highlight_current_line()

root.mainloop()

