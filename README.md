# GAI

GAI is an open‑source Sublime Text plugin that brings generative AI directly into your editor. It helps you generate boilerplate, refactor code, and explore creative solutions, letting you focus on the parts of development that matter most. Built with community contributions in mind, GAI is fully extensible, transparent, and free to use, and maintains full compatibility with the OpenAI API.

## Introduction

The plugin supports having multiple different endpoint configurations and selecting at runtime with fully asynchronous execution fully integrated in the command palette.


1. **Generates boilerplate code**: Helps generate boilerplate code.
2. **Refactors code**: Assists in refactoring code.
3. **Explores creative solutions**: Enables exploring creative solutions.
4. **Extensible**: Fully extensible with community contributions in mind.
5. **Multiple endpoint configurations**: Supports having multiple different endpoint configurations.
6. **Runtime endpoint selection**: Allows selecting endpoint configurations at runtime.
7. **Asynchronous execution**: Executes tasks fully asynchronously.
8. **Command palette integration**: Fully integrated in the Sublime Text command palette.
9. **OpenAI API compatibility**: Maintains full compatibility with the OpenAI API.
10. **Fully configurable**: Integrates naturally with Sublime Text configuration. 
11. **Free to use**: Free to use.

![Concurrent execution with multiple configurations](./media/gai_demo_multi.gif)

## Tool Liability Disclaimer

Please keep in mind that code shared with an external partner is transmitted without encryption. For this reason, it should not be used for any sensitive or regulated information, in order to stay compliant with all applicable laws, regulations, and internal policies. If you need to exchange confidential data, please consider using an encrypted channel or a secure potentially on-prem/local alternative.

By using this tool, you acknowledge that you alone are liable for any damage resulting from its use. This tool has no defined intended purpose, and you, the user, assume full responsibility for all legal, financial, social, or other obligations arising from its use. Such responsibility extends to both the use of the tool and any resulting artifacts—including code, text, or other outputs in any format, whether executable or not. The authors of this tool assume no liability.


## Installation

Currently this can only be installed via Github repository. Soon to be integrated in package control directly.

### Easy Install

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

Input your OpenAI API key in the Preferences->Package Settings->GAI. 

Prefered way use the command palette to bring up the settings (GAI: Settings). 

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

The populated list of the alternates configuration will be shown to the user when the "default" is not set.

## Usage

### Generate Text

Select the portion of text that you want to send as context to the ai , inclusive of the command. 


For example suppose the text in the editor is:

```
Writing clean and efficient code is crucial for any software development project. It not only improves readability but also reduces debugging time. Good coding practices can significantly enhance overall code quality.
```

For which we want to expand on each phrase, then command to the large language model can be placed below.

```
Writing clean and efficient code is crucial for any software development project. It not only improves readability but also reduces debugging time. Good coding practices can significantly enhance overall code quality.

Please for each phrase add more relevant information

```

Subsequently selecting the entire piece of text the Generate Text command can be called through the command palette , search for GAI: Generate Text, e.g. typing `gagi` . Subsequently, select the model from the (searchable) list, and the result can look like:

```
Writing clean and efficient code is crucial for any software development project. It not only improves readability but also reduces debugging time. Good coding practices can significantly enhance overall code quality.

Please for each phrase add more relevant information

Here's an expanded version of the given text with additional relevant information for each phrase:

1. **Writing clean and efficient code is crucial for any software development project.**
   - Clean code is easy to understand and modify, making it easier for developers to collaborate and maintain the codebase over time. Efficient code, on the other hand, ensures that the application performs well, consumes fewer resources, and provides a better user experience. Both aspects are crucial for the success and scalability of a software project.

2. **It not only improves readability but also reduces debugging time.**
   - Readability is enhanced through the use of clear variable names, concise functions, and proper documentation, making it easier for developers to understand the code's intent and functionality. Reduced debugging time is a direct result of clean code practices, as fewer bugs are introduced, and issues are easier to identify and fix when they arise.

3. **Good coding practices can significantly enhance overall code quality.**
   - Good coding practices include following established coding standards, using version control effectively, writing modular and reusable code, and continuously refactoring to improve code structure and performance. By adhering to these practices, developers can ensure that their codebase remains maintainable, efficient, and adaptable to changing requirements.

By emphasizing these aspects, developers can create software that is not only functional but also maintainable, efficient, and of high quality.

```


### Edit
You could also utilize GAI to modify your code or text. The instruct window permits you to input an instruction. The simple the better. Highlight the specific piece of text or code you want to have altered and then bring-up the command pallet (ctrl+shift+p) to select 'GAI: Edit ..." .

You have the freedom to input any text at your editing instruction. Straightforward instructions are most effective. Too complex instructions may have unwanted or unpredictable results.



