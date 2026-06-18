from functions.auto_configuration import get_config

from tools.ask_user_more_info import ASK_USER_TOOL_DEFINITION, ask_user_more_info
from tools.search_web import SEARCH_WEB_TOOL_DEFINITION, search_web
from tools.get_current_time import TIME_TOOL_DEFINITION, get_current_time
from tools.terminal_command import EXECUTE_COMMAND_DEFINITION, execute_terminal_command
from tools.rag_history_search import RAG_HISTORY_SEARCH_TOOL_DEFINITION, rag_history_search
from tools.read_file import READ_FILE_TOOL_DEFINITION, read_file
from tools.write_file import write_file, WRITE_FILE_TOOL_DEFINITION
from tools.edit_file import EDIT_FILE_TOOL_DEFINITION, edit_file

def get_tool_result(function_name:str, args:dict) -> str:
    if function_name == "ask_user_more_info":
        return ask_user_more_info(args['question'])
    elif function_name == "search_web":
        print(f"[Processing] Searching the info of \"{args['query']}\"")
        return search_web(args['query'])
    elif function_name == "get_current_time":
        return get_current_time()
    elif function_name == "execute_terminal_command":
        execute_mode = get_config("AUTO_EXECUTE_MODE")
        print(f"[Processing] Opening a terminal to execute command...")
        return execute_terminal_command(args["command"], args.get("background", False), mode=execute_mode)
    elif function_name == "rag_history_search":
        print(f"[Processing] Try to search info of \"{args['query']}\" in past chat history...")
        return rag_history_search(args['query'])
    elif function_name == "read_file":
        read_file_mode = get_config("AUTO_READ_MODE")
        print(f"[Processing] Reading file {args['file_path']}")
        return read_file(args['file_path'], mode=read_file_mode)
    elif function_name == "write_file":
        # write_file in normal mode triggers CodeAct: the actual writing is done
        # by run_codeact_task in use_tools_to_analyze.py, not here.
        # This branch should not be reached directly; kept for safety.
        print(f"[Processing] write_file triggered — should be handled by CodeAct in use_tools_to_analyze.py")
        return "[CodeAct] write_file must be handled by CodeAct mode."
    elif function_name == "edit_file":
        edit_file_mode = get_config("AUTO_EDIT_MODE")
        print(f"[Processing] Editing file {args['file_path']}...")
        return edit_file(args['file_path'], args['old_str'], args['new_str'], mode=edit_file_mode)
    else:
        return None

def choose_which_tools(user_prompt:str, system_prompt:str) -> list:
    print(f"[Analysing] Viewing available tools...")
    return [ASK_USER_TOOL_DEFINITION, 
            SEARCH_WEB_TOOL_DEFINITION,
            TIME_TOOL_DEFINITION,
            EXECUTE_COMMAND_DEFINITION,
            RAG_HISTORY_SEARCH_TOOL_DEFINITION,
            READ_FILE_TOOL_DEFINITION,
            WRITE_FILE_TOOL_DEFINITION,
            EDIT_FILE_TOOL_DEFINITION]
