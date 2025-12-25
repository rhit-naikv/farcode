# Import community file tools
from langchain_community.tools import (
    CopyFileTool,
    DeleteFileTool,
    DuckDuckGoSearchRun,
    FileSearchTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadFileTool,
    WriteFileTool,
)

from .secure_shell_tool import create_secure_shell_tool


def getTools():
    # Initialize the community file tools
    list_directory_tool = ListDirectoryTool()
    read_file_tool = ReadFileTool()
    write_file_tool = WriteFileTool()
    copy_file_tool = CopyFileTool()
    move_file_tool = MoveFileTool()
    delete_file_tool = DeleteFileTool()
    file_search_tool = FileSearchTool()
    search_tool = DuckDuckGoSearchRun()
    # Using secure shell tool with safeguards instead of the default ShellTool
    shell_tool = create_secure_shell_tool()

    return [
        list_directory_tool,
        read_file_tool,
        write_file_tool,
        copy_file_tool,
        move_file_tool,
        delete_file_tool,
        file_search_tool,
        shell_tool,
        search_tool,
    ]
