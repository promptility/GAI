import sys

# clear modules cache if package is reloaded (after update?)
prefix = __spec__.parent + "."  # don't clear the base 


for module_name in [
    module_name
    for module_name in sys.modules
    if module_name.startswith(prefix) and module_name != __spec__.name
]:
    del sys.modules[module_name]
globals().pop("module_name", None)
del globals()["prefix"]



from .src.commands import ( 
    gai_generate_text_command, 
    gai_replace_text_command, 
    gai_edit_plugin_settings_command 
    )


def plugin_loaded():
    print("GAI loaded!")

    # from .src.utils.logging import init_logger
    # init_logger()

    prefix = __spec__.parent + "."

    def _filter_func(name):
        return name.startswith(prefix) and name != __spec__.name

    for name in sorted(filter(_filter_func, sys.modules)):
        module = sys.modules[name]
        if hasattr(module, "gai_plugin_loaded"):
            module.gai_plugin_loaded()


def plugin_unloaded():
    print("GAI unloaded!")
    # from .src.utils.logging import shutdown_logger
    # shutdown_logger()
