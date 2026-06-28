"""
Ask user for more information using prompt_toolkit Application.
Provides an inline terminal selector for each question, with arrow key navigation,
Enter to confirm, Esc to cancel. Questions without options go directly to input mode.
Returns a JSON string with the same format as the original version.

Interface (fully compatible with original):
    ask_user_more_info(questions: List[Dict], title: str = "") -> str

Each question dict has keys:
    - id: str (required)
    - text: str (required)
    - options: List[str] (optional, default [])
    - default: str (optional, default "")
    - allow_custom: bool (optional, default False)
"""

from typing import List, Dict, Any
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
import json


def _build_style():
    """Build the prompt_toolkit Style for the selector."""
    return Style.from_dict({
        "title": "bold underline",
        "question": "bold",
        "option-selected": "bg:#005f87 fg:white",
        "option-normal": "",
        "option-custom": "italic",
        "input-prompt": "bold",
        "input-value": "fg:#00af5f",
        "help-text": "fg:#888888 italic",
        "status": "fg:#ffaf00",
    })


def _run_single_question(question: Dict[str, Any]) -> str:
    """
    Run the interactive selector for a single question.
    Returns the selected/entered value as a string, or raises KeyboardInterrupt on cancel.
    """
    q_id = question.get("id", "")
    q_text = question.get("text", "")
    options = question.get("options", [])
    default = question.get("default", "")
    allow_custom = question.get("allow_custom", False)

    # If no options, go directly to input mode
    if not options:
        return _run_input_mode(q_text, default)

    # Build the full option list: original options + "Custom input..." if allowed
    display_options = list(options)
    if allow_custom:
        display_options.append("Custom input...")

    # State
    selected_index = [0]  # mutable for closure
    result = [None]  # mutable for closure
    mode = ["select"]  # "select" or "custom_input"

    # TextArea for custom input mode (created on demand)
    custom_text_area = [None]

    # Try to set initial selection to default
    if default:
        try:
            idx = display_options.index(default)
            selected_index[0] = idx
        except ValueError:
            pass

    kb = KeyBindings()

    @kb.add("left")
    @kb.add("up")
    def _move_up(event):
        if mode[0] == "select":
            selected_index[0] = (selected_index[0] - 1) % len(display_options)

    @kb.add("right")
    @kb.add("down")
    def _move_down(event):
        if mode[0] == "select":
            selected_index[0] = (selected_index[0] + 1) % len(display_options)

    @kb.add("enter")
    def _confirm(event):
        if mode[0] == "select":
            chosen = display_options[selected_index[0]]
            if chosen == "Custom input...":
                # Switch to custom input mode
                mode[0] = "custom_input"
                init_text = default if default not in options else ""
                custom_text_area[0] = TextArea(
                    text=init_text,
                    multiline=False,
                    style="class:input-value",
                )
                _rebuild_layout(event.app)
            else:
                result[0] = chosen
                event.app.exit()
        elif mode[0] == "custom_input":
            if custom_text_area[0] is not None:
                result[0] = custom_text_area[0].text.strip()
            event.app.exit()

    @kb.add("escape")
    def _cancel(event):
        if mode[0] == "custom_input":
            # Go back to select mode
            mode[0] = "select"
            custom_text_area[0] = None
            _rebuild_layout(event.app)
        else:
            event.app.exit(exception=KeyboardInterrupt())

    @kb.add("c-c")
    def _ctrl_c(event):
        event.app.exit(exception=KeyboardInterrupt())

    def _get_select_text():
        """Build the select-mode display content."""
        lines = []
        lines.append(("class:question", f"\n  {q_text}\n"))
        lines.append(("", "\n"))
        for i, opt in enumerate(display_options):
            prefix = " ● " if i == selected_index[0] else "   "
            style_class = "class:option-selected" if i == selected_index[0] else "class:option-normal"
            if opt == "Custom input...":
                style_class = style_class + " class:option-custom"
            lines.append((style_class, f"{prefix}{opt}\n"))
        lines.append(("", "\n"))
        lines.append(("class:help-text", "  ← → / ↑ ↓ to navigate  |  Enter to confirm  |  Esc to cancel\n"))
        return FormattedText(lines)

    # ---- Layout ----
    # Select mode: simple FormattedTextControl
    select_control = FormattedTextControl(_get_select_text)
    select_window = Window(select_control)

    # Custom input mode: header + input row ("> " + TextArea) + help
    def _get_custom_header_text():
        lines = []
        lines.append(("class:question", f"\n  {q_text}\n"))
        lines.append(("", "\n"))
        lines.append(("class:input-prompt", "  Enter your custom value:\n"))
        return FormattedText(lines)

    custom_header_control = FormattedTextControl(_get_custom_header_text)
    custom_header_window = Window(custom_header_control, height=2, dont_extend_height=True)

    # Prompt prefix "> " on the same line as the custom input
    custom_prompt_control = FormattedTextControl(
        lambda: FormattedText([("class:input-prompt", "  > ")])
    )
    custom_prompt_window = Window(custom_prompt_control, width=4, dont_extend_width=True)

    custom_help_control = FormattedTextControl(
        lambda: FormattedText([("class:help-text", "  Type your value  |  Enter to confirm  |  Esc to go back")])
    )
    custom_help_window = Window(custom_help_control, height=1, dont_extend_height=True)

    def _build_custom_container():
        """Build the custom input container with the current TextArea."""
        ta = custom_text_area[0]
        if ta is None:
            # Should not happen, but guard against it
            return HSplit([custom_header_window, custom_help_window])
        input_row = VSplit([custom_prompt_window, ta])
        return HSplit([custom_header_window, input_row, custom_help_window])

    # Root layout starts in select mode
    root_container = HSplit([select_window])
    layout = Layout(root_container)

    def _rebuild_layout(app):
        """Rebuild the layout when switching modes."""
        if mode[0] == "select":
            new_root = HSplit([select_window])
        else:
            new_root = _build_custom_container()
        app.layout = Layout(new_root)
        # Focus the TextArea in custom input mode
        if mode[0] == "custom_input" and custom_text_area[0] is not None:
            try:
                app.layout.focus(custom_text_area[0])
            except Exception:
                pass
        app.invalidate()

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=_build_style(),
        full_screen=False,
        erase_when_done=False,
    )

    app.run()

    if result[0] is not None:
        return result[0]
    raise KeyboardInterrupt()


def _run_input_mode(q_text: str, default: str) -> str:
    """
    Run a simple text input mode for questions without options.
    Uses TextArea widget for native cursor and editing support.
    """
    result = [None]

    kb = KeyBindings()

    @kb.add("enter")
    def _confirm(event):
        result[0] = text_area.text.strip()
        event.app.exit()

    @kb.add("escape")
    def _cancel(event):
        event.app.exit(exception=KeyboardInterrupt())

    @kb.add("c-c")
    def _ctrl_c(event):
        event.app.exit(exception=KeyboardInterrupt())

    # Header: question text only
    def _get_header_text():
        lines = []
        lines.append(("class:question", f"\n  {q_text}\n"))
        lines.append(("", "\n"))
        return FormattedText(lines)

    header_control = FormattedTextControl(_get_header_text)
    header_window = Window(header_control, height=2, dont_extend_height=True)

    # Prompt prefix "> " on the same line as the input
    prompt_control = FormattedTextControl(
        lambda: FormattedText([("class:input-prompt", "  > ")])
    )
    prompt_window = Window(prompt_control, width=4, dont_extend_width=True)

    # TextArea for input with native cursor
    text_area = TextArea(
        text=default or "",
        multiline=False,
        style="class:input-value",
    )

    # Input row: "> " + TextArea on the same line
    input_row = VSplit([prompt_window, text_area])

    # Help text
    help_control = FormattedTextControl(
        lambda: FormattedText([("class:help-text", "  Type your answer  |  Enter to confirm  |  Esc to cancel")])
    )
    help_window = Window(help_control, height=1, dont_extend_height=True)

    root_container = HSplit([header_window, input_row, help_window])
    layout = Layout(root_container, focused_element=text_area)

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=_build_style(),
        full_screen=False,
        erase_when_done=False,
    )

    app.run()

    if result[0] is not None:
        return result[0]
    raise KeyboardInterrupt()


def ask_user_more_info(questions: List[Dict[str, Any]], title: str = "") -> str:
    """
    Ask the user a series of questions using an inline terminal selector.

    Args:
        questions: List of question dicts, each with:
            - id (str): Question identifier
            - text (str): Question text to display
            - options (List[str], optional): List of options to choose from
            - default (str, optional): Default value
            - allow_custom (bool, optional): Whether to allow custom input
        title (str, optional): Title displayed before questions (currently unused
                               but kept for interface compatibility).

    Returns:
        str: JSON string with format:
            {"answers": {"q_id1": "answer1", "q_id2": "answer2", ...}, "cancelled": false}
            or {"answers": {}, "cancelled": true} if user cancelled.
    """
    answers = {}
    cancelled = False

    try:
        for question in questions:
            q_id = question.get("id", "")
            if not q_id:
                continue

            # Print a separator between questions
            if answers:
                print()  # blank line between questions

            value = _run_single_question(question)
            answers[q_id] = value

    except KeyboardInterrupt:
        cancelled = True
        answers = {}

    result = {
        "answers": answers,
        "cancelled": cancelled,
    }

    return json.dumps(result, ensure_ascii=False)


# ============================================================================
# 工具定义（供 choose_which_tools.py 等外部模块使用）
# ============================================================================

ASK_USER_TOOL_DEFINITION: Dict[str, Any] = {

    "type": "function",
    "function": {
        "name": "ask_user_more_info",
        "description": (
            "Ask the user multiple questions at once when more information is needed "
            "to complete a complex task. This launches an interactive questionnaire "
            "where the user can navigate between questions, select from preset options, "
            "or type custom answers. Use this when you need to gather several pieces of "
            "information from the user simultaneously rather than asking one question at a time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "description": (
                        "List of questions to ask the user. Each question is an object with: "
                        "'id' (unique identifier string), "
                        "'text' (the question text), "
                        "'options' (optional array of preset choices, max 5), "
                        "'default' (optional default text for custom input), "
                        "'allow_custom' (optional bool, default true, whether to allow free-text input)."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique identifier for this question."},
                            "text": {"type": "string", "description": "The question text to display."},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preset answer options (max 5).",
                                "maxItems": 5,
                            },
                            "default": {"type": "string", "description": "Default text for custom input."},
                            "allow_custom": {"type": "boolean", "description": "Whether to allow free-text input."},
                        },
                        "required": ["id", "text"],
                    },
                },
                "title": {
                    "type": "string",
                    "description": "Title displayed at the top of the questionnaire.",
                },
            },
            "required": ["questions"],
        },
    },
}


# ============================================================
# Standalone test
# ============================================================
if __name__ == "__main__":
    test_questions = [
        {
            "id": "q1",
            "text": "What is your favorite color?",
            "options": ["Red", "Blue", "Green", "Yellow"],
            "default": "Blue",
            "allow_custom": True,
        },
        {
            "id": "q2",
            "text": "How old are you?",
            "options": [],
            "default": "25",
            "allow_custom": False,
        },
        {
            "id": "q3",
            "text": "Choose your OS:",
            "options": ["macOS", "Linux", "Windows"],
            "default": "macOS",
            "allow_custom": False,
        },
    ]

    result_json = ask_user_more_info(test_questions, title="User Survey")
    print(f"\n\n=== Result ===\n{result_json}")
