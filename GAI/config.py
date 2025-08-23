import importlib
# NOTE: Import the *top‑level* ``sublime`` module (the tests replace it with a Mock).
# Using ``importlib.import_module`` guarantees we get the patched object,
# not the ``GAI.sublime`` file that also exists in the package.
sublime = importlib.import_module('sublime')

from time import sleep  # Added import for sleep function used in ready_wait


class configurator():

    def __init__(self, configurations, section_name, base_obj):
        self.base_obj = base_obj
        self.__section_cursor__ = section_name

        self.cancelled = False  

        self.source_config__meta__ = configurations.get("__meta__", {})

        # Read Sublime Text configuration object
        self.source_config = {}
        self.source_config["oai"] = configurations.get("oai", {})
        self.source_config[section_name] = configurations.get(section_name, {})

        # Read the section configuration
        self.__running_config__ = {}
        self.__running_config__["alternates"] = configurations.get(
            "alternates", {})
        self.__configuration__completed__ = False
        self.__construct__running__config__()

    def __construct__running__configself):

        def populate_dict(input_dict, target_dict):

            def merge_value(input_val, target_val, key):
                # Determine which priority lists apply for the current key
                target_prio_str_keys = self.source_config__meta__.get(
                    "target_prio_str_keys", [])
                input_prio_str_keys = self.source_config__meta__.get(
                    "input_prio_str_keys", [])
                input_prio_keys = self.source_config__meta__.get(
                    "input_prio_keys", [])

                if key in target_prio_str_keys:
                    # Target (global) value first, then input (more specific)
                    return target_val + "\n\n" + input_val
                elif key in input_prio_str_keys:
                    # Input (more specific) value first, then target
                    return input_val + "\n\n" + target_val
                elif key in input_prio_keys:
                    # Input overrides target completely
                    return input_val
                else:
                    # Default: keep target value
                    return target_val

            def merge_dict_value(lhs, rhs, k):
                # Merge a dict with a scalar value (or vice‑versa)
                if isinstance(lhs, dict):
                    dict lhs
                    val = rhs
                else:
                    dict_val = rhs
                    val = lhs

                merged = dict(dict_val)  # copy to avoid mutating original
                merged[k] = val
                return merged

            def merge_dict(k):
                """
                Merge the value for a single key ``k`` from ``input_dict`` into
                ``target_dict``.

                The original implementation missed the case where the key
                exists **only** in ``target_dict`` (e.g. the ``alternates`` key
                when merging the global ``oai`` section).  In that situation the
                function incorrectly fell through to the ``None`` fallback,
                wiping out the existing value and breaking the configurator.

                The corrected logic now:
                1. If the key exists only in ``input_dict`` → return that value.
                2. If the key exists only in ``target_dict`` → keep the target
                   value.
                3. If the key exists in both:
                   * non‑dict values → apply the priority‑merge rules.
                   * both dicts → recurse.
                   * one dict / one scalar → merge appropriately.
                """
                # Key only in the input → take it.
                if k in input_dict and k not in target_dict:
                    return input_dict[k]

                # Key only in the target → keep it.
                if k in target_dict and k not in input_dict:
                    return target_dict[k]

                # Key present in both dictionaries.
                if k in input_dict and k in target_dict:
                    # Both values are non‑dicts → apply string/priority merge.
                    if not isinstance(input_dict[k], dict) and not isinstance(target_dict[k], dict):
                        return merge_value(input_dict[k], target_dict[k], k)

                    # Both values are dicts → recurse.
                    if isinstance(input_dict[k], dict) and isinstance(target_dict[k], dict):
                        return populate_dict(input_dict[k], target_dict[k])

                    # One dict, one scalar → merge appropriately.
                    return merge_dict_value(input_dict[k], target_dict[k], k)

                # Fallback (should not happen).
                return None

            keys = set(list(target_dict.keys()) + list(input_dict.keys()))
            return {k: merge_dict(k) for k in keys}

        # Construct oai configuration from global and section
        default_oai = self.source_config["oai"]
        self.__running_config populate_dict(
            default_oai, self.__running_config__)

        # Merge the specific command section
        section_config = self.source_config[self.__section_cursor__]
        self.__running_config__ = populate_dict(
            section_config, self.__running_config__)

        def replace_config(config_name):
            if config_name:
                alternates = self.__running_config__["alternates"]
                config_override = alternates[config_name]
                self.__running_config__ = populate_dict(
                    self.__running_config__, config_override)

        def on_done(index):
            if index == -1:
                self.cancelled = True  
            else:
                configs_list = ["__default__"]
                configs_list += list(alternates.keys())
                selected_config = configs_list[index]
                if selected_config != "__default__":
                    replace_config(selected_config)
            self.__configuration__completed__ = True

        default_alternate = self.__running_config__[
            "alternates"].get("default", None)
        if default_alternate is not None:
            replace_config(default_alternate)
            self.__configuration__completed__ = True
        else:
            alternates = self.__running_config__["alternates"]
            # ``self.base_obj`` is a command object that already has a ``view``.
            # The ``view`` provides ``window()`` – this works both in Sublime
            # and in the mocked test environment.
            self.base_obj.view.window().show_quick_panel(
                ["default"] + list(alternates.keys()), on_select=on_done)

    def ready_wait(self, sleep_duration=0.2):
        while not self.__configuration__completed__:
            sleep(sleep_duration)

    def is_cancelled(self):
        self.ready_wait()
        return self.cancelled

    def get_prompt(self, default=""):
        self.ready_wait()
        return self.__running_config__.get("prompt", default)

    def get_persona(self, default="You are a helpful AI Assistant"):
        self.ready_wait()
        return self.__running_config__.get("persona", default)

    def get_model(self, default="gpt-4"):
        self.ready_wait()
        return self.__running_config__.get("model", default)

    def get(self, key, default=None):
        self.ready_wait()
        return self.__running_config__.get(key, default)
