import sublime_plugin

from GAI.src.commands import ( 
    gai_generate_text_command, 
    gai_replace_text_command, 
    gai_edit_plugin_settings_command 
    )


def plugin_loaded():
    print("GAI loaded!")

    # from .src.utils.logging import init_logger
    # init_logger()


def plugin_unloaded():
    print("GAI unloaded!")
    # from .src.utils.logging import shutdown_logger
    # shutdown_logger()
