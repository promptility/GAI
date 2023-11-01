# GAI

GAI is a Generative AI sublime text plugin. You can work alongside cutting edge AI to write code - automate the boilerplate, and
focus on the creative side of coding. 

You must have an account, and API key, and be authorized, to use[OpenAI's API](https://openai.com/blog/openai-api/). 

## Disclaimer

You are trusting an outside organization with the code you send them, and it is
not encrypted - this cannot and should not be used for any kind of sensitive or
otherwise regulated data according to local rules, directives, regulations, and
any kind of other legally defining documents.

By using this tool you understand that you and you alone is liable for any damage resulting by that use. This tool has not any defined intended use whatsoever and you the user use it at your own sole responsibility and bear any legal, financial, social, or any other possible responsibility.

This responsibility extends to both its use and artifacts, such as code, text, artifacts generated via those artifacts, in any format, be-it so executable or not, and the authors of this code have no responsibility whatsoever.

## Installation

### Easy Install
Currently this can only be installed via Github repository. 

First you need to add this repository to package control.

1. Bring-up the command palette.
2. Select 'Package Control: Add repository'.
3. Copy paste this repository's URL. 

Subsequently to install GAI:

1. From Sublime
2. Access 'Package Control' (via 'Preferences' or ctrl+shift+p)
3. Select 'Install Package'
4. Wait for packages to load
5. Search and download 'GAI'

## Configuration
First: input your OpenAI API key in the Preferences->Package Settings->GAI. 
Alternatively, use the command palette to bring up the settings (GAI: Settings). Do not edit the left side of , but place your settings on the right side.

The configuration is structured in a format that allows to customize easily both per command but also globally with multiple endpoints.

```json
{
    "oai" : {
        // put your openai connection information here ( consult the configuration for details)
    }, 
    "alternates" : {
        // Allows to provide multiple top-level different configurations, e.g. 
        "my_gpt_4": {
            // ...
        }, 
        "my_gpt_3": {
            // ...
        }
    },
    "commands" : {
        "completions" : {
            // Put the configuration options here such as connection information
            // and other customizations , such as prompt, personas etc.
            "alternates" : {
                // configurations in here will replace top-level alternates 
                // with the same key. New keys will be appended.
                "default": "", // if set to an alternate configuration name it will default to this and user selection is supressed.
            }
        }
    }
}
```

The populated list of the alternates configuration will be shows to the user when the "default" is not set.

### Completion

Write your function definition with a docstring possibly. Then highlight, and bring-up the command palette to selection 'GAI: Python code generation'.



### Edit
You could also utilize GAI to modify your code or text. The instruct window permits you to input an instruction. The simple the better. Highlight the specific piece of text or code you want to have altered and then bring-up the command pallet (ctrl+shift+p) to select 'GAI: Edit ..." .

You have the freedom to input any text at your editing instruction. Straightforward instructions are most effective. Too complex instructions may have unwanted or unpredictable results.
