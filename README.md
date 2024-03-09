# Telegram Event-Scheduling Bot
## How to use
Search for @steveisrich_bot on Telegram, and start messaging!

Bot link: https://t.me/steveisrich_bot

## Description
Steve is a python-programmed bot that can help you schedule your events, play games with you, and be your little robot companion. The program consists of three types of telegram message handlers: `ConversationHandlers`, `MessageHandlers` and `CommandHandlers`.

`CommandHandlers` are triggered by a /command text sent by the user. This command is associated with a function in the program, which triggers a response from the bot. The program consists of seven command handlers: `/start`, `/add`, `/delete`, `/print`, `/games`, `/mount` and `/help`. The Command Functionalities section describes their functionalities.

`MessageHandlers` are triggered by regular text messages sent by the user. The program consists of one MessageHandler called `unknown_handler`, which filters out non-existent commands sent by the user and returns an apology text.

`ConversationHandlers` are used to manage multi-step conversations with the user. The user initiates a conversation by sending a message. _For our program, the following commands can be used to initiate a conversation: `/add`, `/delete`, `/games` and `/mount`._ Depending on the user's input, different states can be called, which are associated with different functions that perform different tasks. Users can end the conversation at any point in time with the command `/cancel`.

### Files included
> main.py

The main program. It contains all the text handlers and functions required for our bot to run.

> functions.py

A list of secondary functions, not involved directly in text handling, that are called by main.py to perform various tasks. These functions include:

- `greet()`: Takes in no input, extracts the current time using the datetime module, and returns a greeting according to the current time. Called by `start()` to greet the user.
- `fun_fact()`: Takes in no input, reads from the fun_facts.csv file, and returns a list of sentences that are used as fun facts to greet the user. Called by `start()`.
- `load_user_events()`: Takes in no input, reads from the user_events.json file, and returns a dictionary containing key-value pairs of the chat_id and a list of the corresponding events scheduled by the chat. For private chats, the chat_id will be the same as the private user's user_id.
- `save_user_events()`: Takes in a dictionary input, and writes the dictionary to the user_events.json file. Works in conjunction with `load_user_events()`.
- `check_mounting()`: Takes in a datetime object, and returns a string describing which platoon is mounting on that date.
- `load_highscore()`: Takes in no input, reads from the matrix_highscore.json file, and returns a dictionary with key-value pairs of the chat_id and the corresponding high score for the matrix game.
- `save_highscore()`: Takes in a dictionary input, and writes that dictionary to the matrix_highscore.json file. Works in conjunction with load_highscore().

> fun_facts.csv

Contains a list of 10 sentences, separated by an escape sequence. These sentences are fun facts, utilised by the /start command.

> user_events.json

Contains a dictionary with key = chat_id and value = list of dictionaries containing key-value pairs of the chat's events and dates.

> matrix_highscore.json

Contains a dictionary with key = chat_id and value = integer highscore of the matrix game within the chat.

### Command functionalitites
At the start of the program, `load_user_events()` and `load_highscore()` are called and stored respectively into the variables `user_events` and `highscore_data`, which will be used by various functions later on.

#### /start
When start() is called, Steve greets the user according to their time zone, and provides a fun fact that is randomly selected from a list of fun facts. The included greetings are `morning`, `afternoon`, and `evening`. The greeting to use is decided by calling the `greet()` function. The list of fun facts is retrieved by the `fun_fact()` function.

#### /add
This command starts a conversation and allows the user schedule events and their dates/times, which will then be stored by the program in a user_events.json file. 

Once `add_event()` is called, the bot will prompt the user to input at least one event with its corresponding date and time, and provides some examples on the formatting. Once the user returns a message, the program calls the `get_event_info()` function, which rigorously error-checks the user's input, and re-prompts the user if the user inputs an invalid format or an incorrect date-time format. Once the input passes all checks, the function will convert the date-time string into a `datetime object`, and append the event-date pair into the `user_events` dictionary, which is then passed into the `save_user_events()` function to update the `user_events.json` storage file. 

Utilising the message's chat_id instead of user_id allows different events to be stored for different users and chats. This means that private chats will store events specific to the user, while members inside a group chat can schedule shared events specific to the chat.

The /add operation can be cancelled by simply calling the `/cancel` command.

#### /cancel
This command can be called to terminate an ongoing conversation.

#### /delete
This command starts a conversation and allows the user/ chat to delete scheduled events from the user_events.json file.

Once `delete_events()` is called, the bot will send a text message that numerically lists all of the user's scheduled events, and provide a `reply_keyboard` containing buttons for the events' indices. The user can select which events to delete, along with an option to delete all scheduled events. Once a selection is made, the conversation transits into another state where the function `deletion_junction()` is called. This function checks which button the user clicked on by Regex matching with the string printed on the buttons. 

If the user chooses a numbered button referring to any one of the events, then that particular event will be popped from `user_events` and saved with `save_user_events()`. The same state will be returned, calling `deletion_junction()` again, and printing a list of events minus the already deleted ones. This means that the user can continuously delete events until he ends the conversation with the `cancel` command.

 If the user chooses the `Delete all events` button, the conversation will transit into another state, which calls the function `confirm_deletion`. This function asks the user to confirm his or her action, providing a `reply_keyboard` with the options "Yes" or "No". Choosing "Yes" will delete the key-value pair within `user_events` containing the chat_id and the scheduled events, while choosing "No" will simply end the conversation. 
 
 Finally, if the user decides to send a text message instead of choosing a button, the program will detect an invalid input and re-prompt the user. If the user has no upcoming events, the bot will simply return a message indicating so.

The /delete operation can be cancelled by calling `/cancel`.

#### /print
This command calls the `print_events()` function, which programs the bot to print a list of user events and dates scheduled by the chat or user. If the user has no upcoming events, the bot will return a message indicating so.

#### /games
This command starts a conversation and provides the user with a `reply_keyboard` containing six mini-game emojis built into Telegram, as well as a custom matrix game. The emojis, once pressed, will trigger the mini-games, and the keyboard stays in place to allow for repeated user actions. Once the matrix game button is pressed, the conversation transitions into another state and the `matrix()` function is called. This function is essentially a memory game, where the user flips `inline_keyboard` buttons on a 4*4 grid provided by the bot, and tries to match icons until all grid icons are revealed.

`context.chat_data` will be used to store information regarding the memory game. It is a dictionary associated with a specific user's session, and typically refers to the `CallBackContext` object. This object provides a way to store and retrieve data between different callback functions, and can be used to store information that needs to persist across different states or steps of a conversation. `context.chat_data["board"]` stores the 4*4 grid in a 2D list. `context.chat_data["fixed"]` is a 4*4 grid that contains `None` or `"Match"` values, which is updated when a pair is found to ensure that paired icons remain revealed. `context.chat_data["score_tracker"]` contains an `int` that increments with every two button clicks. `context.chat_data["selected"]` stores the indices of two clicked icons and checks for a match, concealing them if there is no match, and updating `context.chat_data["fixed"]` when a match is found. `context.chat_data["selected"]` is cleared after every two button clicks.

Highscores for this game are updated with every win. Highscore data is loaded by calling `load_highscore()` and saved in the variable `highscore_data`. Once the game ends, if the highscore is surpassed for the current chat, `highscore_data` is updated and saved to `matrix_highscore.json` by calling `save_highscore()`.

The /games operation can be cancelled by calling `/cancel`.

#### /mount
This command starts a conversation and allows the user to check which platoon is mounting on a specified date. The `mount()` function is called, which prompts the user to input a date. Upon receiving the user's message, the conversation transitions into another state and the `check_mount()` function is called. This function error-checks the user input and re-prompts the user if an incorrect date format is detected. Once these checks are passed, `check_mounting()` is called, and the bot responds with the answer returned.

The /mount operation can be cancelled by calling `/cancel`.

#### /help
This command prints out a list of available commands for the user to execute, along with a quirky message randomly chosen from a list of expressions.

### Future Updates
- Set reminder for events, with options to update a day before, hour before, or custom update.
- Integrate OpenAI's various models.
- Introduce the demo trading account from Finance.


### Resources used:
https://core.telegram.org/bots/features#commands

https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API

https://docs.python-telegram-bot.org/en/stable/telegram.callbackquery.html

Examples: 
https://docs.python-telegram-bot.org/en/stable/examples.html

Examples github version: 
https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples

Bot hosting: 
https://www.youtube.com/watch?v=2TI-tCVhe9k

Introductory video: 
https://www.youtube.com/watch?v=vZtm1wuA2yc

Profile pic:
https://www.craiyon.com/image/SZE9tExFSbqb4cKUBd6FEA

Exceptions handling:
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exceptions%2C-Warnings-and-Logging