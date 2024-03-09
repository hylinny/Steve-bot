"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

import logging
import random
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler

# additional imports for my conversation
from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler

# additional imports for my games
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler

from datetime import datetime
from functions import greet, load_user_events, save_user_events, check_mounting, load_highscore, save_highscore, fun_fact

# Sets up the logging module, so you will know when (and why) things don't work as expected:
# for more info, read https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exceptions%2C-Warnings-and-Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# assigns the variable to the state (integer states from 0, 1, 2, ...)
ADD_EVENT, DELETE_JUNCTION, DELETE_CONFIRMATION, TRIGGER_GAMES, BUTTON_STATE, CHECK_MOUNT = range(6)

# Saves loaded user events in user_events on startup
user_events = load_user_events()
highscore_data = load_highscore()
emoji_list = [
    ["🐱", "🐶", "🐰", "🐻", "🐼", "🦊", "🐯", "🦁", "🐱", "🐶", "🐰", "🐻", "🐼", "🦊", "🐯", "🦁"],
    ["🤫", "🧏‍♂️", "🗣️", "💀", "🦟", "🦗", "🔥", "🙏", "🤫", "🧏‍♂️", "🗣️", "💀", "🦟", "🦗", "🔥", "🙏"],
    ["😈", "🤡", "😩", "😍", "🥺", "🫥", "🤬", "😭", "😈", "🤡", "😩", "😍", "🥺", "🫥", "🤬", "😭"],
    ["🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕘", "🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕘"],
    ["💅", "✨", "🎀", "💝", "💕", "👁️", "👄", "🙄", "💅", "✨", "🎀", "💝", "💕", "👁️", "👄", "🙄"]
]
# get a whole bunch of lists of different emojis, and randomly select one list!!! so that emojis change each round
ROWS = 4
COLUMNS = 4

#define command handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fact = random.choice(fun_fact())
    await update.message.reply_text(
        f"Good {greet()}! My name is Steve. What can I do for you today? (Press /help for a list of commands)\n\n<i>Fun fact: {fact}</i>", parse_mode='HTML'
    )

# event handling
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Sure! What event(s) would you like to add? Please provide the description and the date/time "
        "of the event(s) in the following format:\n\n<i>&lt;Event Description 1&gt;</i>\n<i>&lt;YYYY-MM-DD HH:MM&gt;</i>\n...\n"
        "\nExample:\n-----------------------------------------\nFlight to Dubai, Gulfstream G550 @ JFK\n2024-02-08 09:00\n\nMovie date 😍 @ Beverly Hills\n2024-02-14 18:30\n-----------------------------------------"
        "\n\nPress /cancel to cancel the operation.", 
        parse_mode='HTML'
    )
    
    return ADD_EVENT # returns state of conversation

async def get_event_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = update.message.chat_id
    events = update.message.text
    list_of_events = [line.strip() for line in events.splitlines() if line] # removes all the newline characters, leaving only a list of events and times
    
    if len(list_of_events) % 2 != 0: # check that length is even i.e. proper number of event-date pairs
        await update.message.reply_text("Invalid input format. Please try again.")
        return ADD_EVENT
    
    description_list = []
    timestamp_list = []
    
    for i in range(0, len(list_of_events), 2):
        description_list.append(list_of_events[i])
        timestamp_list.append(list_of_events[i+1])
        
    timestamp_list_formatted = []
    
    for time in timestamp_list:
        try:
            timestamp = datetime.strptime(time, '%Y-%m-%d %H:%M')
            timestamp_list_formatted.append(timestamp)
        except ValueError:
            await update.message.reply_text("Invalid date/time format. Please use <i>YYYY-MM-DD HH:MM.</i>", parse_mode='HTML')
            return ADD_EVENT

    for i in range(len(description_list)): # list can be anything since all the lists are the same length
        user_events.setdefault(id, []).append({
            'description': description_list[i],
            'timestamp': timestamp_list_formatted[i].strftime('%Y-%m-%d %H:%M')
        })

    # Save user events after adding a new event
    save_user_events(user_events)
    
    # check if one event or multiple events were added
    if len(list_of_events) == 2:
        x = ''
    else:
        x = 's'
    await update.message.reply_text(
        f"Event{x} added successfully! Use /print to see all your events."
    )
    return ConversationHandler.END
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# keyboard for deleting events
async def delete_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = update.message.chat_id
    events = user_events.get(id, [])
    
    reply_keyboard = [["Delete all events"]] + [[str(i+1)] for i, _ in enumerate(events)]
    
    if events:
        message = ''
        for number, event in enumerate(events):
            formatted_timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M')
            message += f"{number+1}) {event['description']} on {formatted_timestamp.strftime('%a %d %b %Y, %I:%M %p')}\n"
        message += "\nClick on the the event number that you would like to delete.\n\nPress /cancel to cancel the operation."
        await update.message.reply_text(
            message, reply_markup=ReplyKeyboardMarkup(reply_keyboard, input_field_placeholder="Delete events")
        )
        return DELETE_JUNCTION
    else:
        await update.message.reply_text("You don't have any upcoming events.")
        return ConversationHandler.END

async def deletion_junction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # retrieves which button the user clicked on
    clicked_button_text = update.message.text
    id = update.message.chat_id
        
    events = user_events.get(id, [])
    
    try:
        if clicked_button_text == "Delete all events":
            reply_keyboard = [["Yes", "No"]]
            message = ''
            message += "Are you absolutely sure that you want to delete all of the following events?\n\n"
            for number, event in enumerate(events):
                formatted_timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M')
                message += f"{number+1}) {event['description']} on {formatted_timestamp.strftime('%a %d %b %Y, %I:%M %p')}\n"
            message += "\nPress /cancel to cancel the operation."
            await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(reply_keyboard, input_field_placeholder="Confirm deletion"))
            return DELETE_CONFIRMATION
        elif int(clicked_button_text) in range(1, len(events)+1):
            index = int(clicked_button_text)
            user_events[id].pop(index-1)
            save_user_events(user_events)
            # Copied from function above
            reply_keyboard = [["Delete all events"]] + [[str(i+1)] for i, _ in enumerate(events)]
            if events:
                message = ''
                for number, event in enumerate(events):
                    message += f"{number+1}) {event['description']} on {event['timestamp']}\n"
                message += "\nClick on the the event number that you would like to delete.\n\nPress /cancel to cancel the operation."
                await update.message.reply_text(
                    message, reply_markup=ReplyKeyboardMarkup(reply_keyboard, input_field_placeholder="Delete events")
                )
                return DELETE_JUNCTION
            else:
                await update.message.reply_text("You don't have any upcoming events.", reply_markup=ReplyKeyboardRemove())
                return ConversationHandler.END
            # End of copied fuction
        else:
            raise ValueError
    except ValueError: # handles all the wrong text inputs (from the elif and else)
        await update.message.reply_text("Invalid input. Please select the event number you would like to delete from the keyboard provided.")
        return DELETE_JUNCTION
        
    
async def confirm_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = update.message.chat_id
    clicked_button_text = update.message.text
    
    if clicked_button_text == "Yes":
        # clearing all events related to the user.id
        del user_events[id]
        save_user_events(user_events)
        await update.message.reply_text("Events deleted successfully.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif clicked_button_text == "No":
        await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid answer. Please select Yes or No.")
        return DELETE_CONFIRMATION

async def print_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    id = update.message.chat_id
    events = user_events.get(id, [])
    # user_events = whole dictionary containing user id and list of dictionaries of events and times
    # events = list of dictionaries events and times specific to mentioned user id (not containing the user id itself)
    if events:
        message = "<i>Your upcoming events:</i>\n\n"
        for event in events:
            formatted_timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M') # converts the date from a string into a datetime object, so that it can be reformatted in the next line
            message += f"{event['description']}\n{formatted_timestamp.strftime('%a %d %b %Y, %I:%M %p')}\n\n"
    else:
        message = "You don't have any upcoming events."
    
    await update.message.reply_text(message, parse_mode='HTML')
# event handling

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["🎯", "🎰", "🎲"], ["🏀", "⚽️", "🎳"], ["Escape the matrix"]] # dices, basketball, football, darts, bowling, slot machine
    
    await update.message.reply_text(
        "Choose a game!\n\nPress /cancel to terminate the operation.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, input_field_placeholder="Games"
        ),
    )
    return TRIGGER_GAMES
    
async def matrix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    chat_id = update.message.chat_id
    # print(chat_id) #testing
    highscore_data.setdefault(chat_id, 0)
    # print(highscore_data) #testing
    
    
    emojis = random.choice(emoji_list)
    temporary_emojis = emojis.copy()
    random.shuffle(temporary_emojis)
    context.chat_data.setdefault("flipped", {}) # setdefault initializes the 'flipped' key to an empty dict if it doesn't exist
    context.chat_data["selected"] = [] # contains indices of emoji pairs later on
    context.chat_data["board"] = [[None] * COLUMNS for _ in range(ROWS)] # 2d grid of emojis
    context.chat_data["fixed"] = [[None] * COLUMNS for _ in range(ROWS)] # used for fixing of matched emojis
    context.chat_data["score_tracker"] = 0
    
    for i in range(ROWS):
        for j in range(ROWS):
            context.chat_data["board"][i][j] = temporary_emojis.pop(0)
            context.chat_data["flipped"].setdefault(i, {})[j] = False
    
    """ testing
    print(context.chat_data["board"])
    print(context.chat_data['fixed'])
    """
    inline_keyboard = [
        [
            InlineKeyboardButton(" " if not context.chat_data["flipped"][i][j] else context.chat_data["board"][i][j], callback_data=f"{i}_{j}")  # Inner list comprehension
            for j in range(COLUMNS)  # Iterate over each emoji and its index in the row
        ]
        for i in range(ROWS)  # Iterate over each row of emojis and its index
    ]
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_text("😳", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(f"Escape the matrix.\n\nHighscore: {highscore_data[chat_id]}\nMoves used: {context.chat_data['score_tracker']}", reply_markup=reply_markup)
    return BUTTON_STATE
    
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query # query = a whole bunch of random information
    chat_id = query.message.chat_id # retrieves chat_id from button press, used for updating high score later on
    button_data = query.data # gets the callback_data 
    i, j = map(int, button_data.split("_"))
    print(i, j) # Checks
    # if query.data information inside context.chat_data[fixed][i][j], return state immediately
    if context.chat_data["fixed"][i][j] == "Match":
        return BUTTON_STATE
    
    context.chat_data["flipped"][i][j] = True # flipping the card over once user presses on it
    context.chat_data["selected"].append([i, j])
    
    inline_keyboard = [
        [
            InlineKeyboardButton(" " if not context.chat_data["flipped"][i][j] else context.chat_data["board"][i][j], callback_data=f"{i}_{j}")  # Inner list comprehension
            for j in range(COLUMNS)  # Iterate over each emoji and its index in the row
        ]
        for i in range(ROWS)
    ]
    """testing
    print(f"selected: {context.chat_data['selected']}")
    print(f"board: {context.chat_data['board']}")
    print(f"fixed: {context.chat_data['fixed']}")
    print(f"flipped True or False: {context.chat_data['flipped']}")
    """
    if len(context.chat_data["selected"]) == 2:
        
        index1, index2 = context.chat_data["selected"] # the indices are a list [x, y]
        emoji1, emoji2 = context.chat_data["board"][index1[0]][index1[1]], context.chat_data["board"][index2[0]][index2[1]]
        if emoji1 == emoji2 and index1 != index2:
            # fix them to be permanently on the screen (true)
            # if user presses on them, nothing happens, moves used also does not increase
            context.chat_data["fixed"][index1[0]][index1[1]] = "Match"
            context.chat_data["fixed"][index2[0]][index2[1]] = "Match"
            context.chat_data["selected"].clear()
            context.chat_data["score_tracker"] += 1
        elif index1 == index2:
            context.chat_data["flipped"][index1[0]][index1[1]] = False
            context.chat_data["selected"].clear()
        else:
            context.chat_data["flipped"][index1[0]][index1[1]] = False
            context.chat_data["flipped"][index2[0]][index2[1]] = False
            context.chat_data["selected"].clear()
            context.chat_data["score_tracker"] += 1
            
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # check if fixed is all match, that means player wins game, return conversationhandler.end
    all_equal = all(all(element == "Match" for element in sublist) for sublist in context.chat_data["fixed"])
    if all_equal:
        if context.chat_data["score_tracker"] < highscore_data[chat_id] or highscore_data[chat_id] == 0:
            highscore_data[chat_id] = context.chat_data["score_tracker"]
        await query.edit_message_text(f"Congratulations! You won! 🎉\n\nHighscore: {highscore_data[chat_id]}\nMoves used: {context.chat_data['score_tracker']}", reply_markup=reply_markup)
        save_highscore(highscore_data)
        return ConversationHandler.END

    await query.edit_message_text(f"Escape the matrix.\n\nHighscore: {highscore_data[chat_id]}\nMoves used: {context.chat_data['score_tracker']}", reply_markup=reply_markup) # Edits the message to update moves used

async def mount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please input the date in the following format: <i>YYYY-MM-DD</i>"
        "\n\n Press /cancel to cancel the operation.",
        parse_mode='HTML'
    )
    
    return CHECK_MOUNT

async def check_mount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_provided = update.message.text.strip()
        
    try:
        date_object = datetime.strptime(date_provided, '%Y-%m-%d')
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use <i>YYYY-MM-DD</i>", parse_mode='HTML')
        return CHECK_MOUNT
    
    # checks if date is mounting day
    situation = check_mounting(date_object)
    date_alphabetical = date_object.strftime('%a %d %b %Y')
    await update.message.reply_text(f"On {date_alphabetical}, Platoon {situation}.\n\nPress /cancel to quit.")
    return CHECK_MOUNT

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    expressions = [
        "I don't even know what the f*** half of them are used for. 🙄",
        "Use them if you want. Zzz... 😴",
        "Yeehaw! 🤠",
        "Please, do whatever you want with them, but leave my family alone. 😣",
        "Steve, at your service. 🫡"
    ]
    
    expression = random.choice(expressions)
    
    await update.message.reply_text(
        f"A list of commands. {expression}\n\n"
        "/start: Start a conversation.\n"
        "/add: Schedule an event.\n"
        "/delete: Delete an event.\n"
        "/print: Display your upcoming events.\n"
        "/games: Games!\n"
        "/mount: Check if you are mounting on a certain date.\n"
        "/help: Displays a list of commands."
    )
    
# if bot is in group chat, bot will only handle commands. if bot is private chat, bot will interpret any user message and print /help
""" taken out
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type = update.message.chat.type
    text: str = update.message.text
    
    # good for debugging, prints out what is happening in terminal
    print(f"User ({update.message.chat.id}) in {message_type}: '{text}'")
    
    return
"""

# filters out commands not recognised by the previous handlers, must be added last
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text
    
    if command == "/cancel":
        await update.message.reply_text("No active command to cancel. I wasn't doing anything anyway. Ugh. 🙄")
    else:
        await update.message.reply_text("Sorry, I didn't understand that command.")
    

def main():
    # Create an instance of ApplicationBuilder and set the bot token
    application = ApplicationBuilder().token('6396472947:AAGsIjLjdv0vQcpvMecMtxBpY40mHYD07MI').build()
    
    # Create command and message handlers (when the user sends the command /'...', the corresponding function is triggered)
    start_handler = CommandHandler('start', start)
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_event)], #add_event_handler
        states={
            ADD_EVENT: [MessageHandler(filters.TEXT & (~ filters.Regex(r"^/cancel$")), get_event_info)],
            # The states parameter is a dictionary that defines the different states of the conversation along with the associated handlers.
            # ADD_EVENT is a state where the conversation expects the user to provide information about the event (description and date/time).
                # The associated handler is [MessageHandler(filters.TEXT, get_event_info)], 
                # meaning that when a text message is received, the get_event_info handler is triggered.
        },
        fallbacks=[CommandHandler("cancel", cancel)], # always active, regardless of the current state
    )
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete_events)],
        states={
            DELETE_JUNCTION: [MessageHandler(filters.TEXT & (~ filters.Regex(r"^/cancel$")), deletion_junction)],
            DELETE_CONFIRMATION: [MessageHandler(filters.TEXT & (~ filters.Regex(r"^/cancel$")), confirm_deletion)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    print_handler = CommandHandler('print', print_events)
    games_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('games', games)],
        states={
            TRIGGER_GAMES: [
                MessageHandler(filters.Regex(r"^Escape the matrix$") & (~ filters.Regex(r"^/cancel$")), matrix)
            ],
            BUTTON_STATE: [CallbackQueryHandler(button)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    mount_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('mount', mount)],
        states={
            CHECK_MOUNT: [MessageHandler(filters.TEXT & (~ filters.Regex(r"^/cancel$")), check_mount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    help_handler = CommandHandler("help", help)
    """ taken out
    group_vs_private_handler = MessageHandler(filters.TEXT & (~ filters.COMMAND), handle_message)
    """
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    
    # Add handlers to the application
    application.add_handler(start_handler)
    application.add_handler(add_conv_handler)
    application.add_handler(delete_conv_handler)
    application.add_handler(print_handler)
    application.add_handler(games_conv_handler)
    application.add_handler(mount_conv_handler)
    application.add_handler(help_handler)
    """ taken out
    application.add_handler(group_vs_private_handler)
    """
    application.add_handler(unknown_handler)
    """ Issue at hand: program runs top to bottom. So if i call /delete for instance, 
    the command above the delete_conv_handler can be called by the user since they are detected
    by the program first. However, the commands after the delete handler can't be called since 
    their input is already addressed by the delete function. Is this fixable? """
    
    # Start the application (bot) polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    # Keep the program running until Ctrl+C is pressed
    # application.idle()
    
if __name__ == '__main__':
    main()
    
    
    # FALLBACK CAN BE MULTIPLE COMMANDS, SO THAT THEY DON'T GET CALLED IN THE MIDDLE OF THE COMMAND