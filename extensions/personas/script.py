import os
import json
import glob
import time
import traceback
import gradio as gr
from functools import partial
from modules import shared, chat
from modules import ui as core_ui
from modules.utils import gradio
from modules.ui_chat import inputs
from modules.ui_chat import reload_arr
from modules.logging_colors import logger


params = {
    "display_name": "Personas",
    "is_tab": False
}

reload_arr = ('history', 'name1', 'name2', 'mode', 'chat_style', 'character_menu')


def get_default_history():
    """Creates a default empty history structure"""
    return {'internal': [], 'visible': []}


def load_character_and_start_chat(character_name):
    """Loads a character and starts a new chat with them"""
    try:
        if not character_name:
            logger.warning("[Personas] No character name provided")
            return None

        # Get current user name to pass to load_character
        name1 = shared.settings.get('name1', 'You')

        # Call load_character directly - NOTE: this modifies shared.settings
        result = chat.load_character(character_name, name1, "Assistant")

        # Unpack the results
        name1, name2, picture, greeting, context = result

        # Return all the character data for the UI update
        return {
            'name2': name2,
            'greeting': greeting,
            'context': context,
            'picture': picture,
            'character_menu': character_name,
        }
    except Exception as e:
        logger.error(f"[Personas] Error loading character: {e}")
        traceback.print_exc()
        return None


def load_persona_json(persona_name):
    """Load a persona from a JSON file and prepare updates for UI"""
    file_path = f"user_data/personas/{persona_name}.json"

    try:
        # Read the persona file
        with open(file_path, 'r') as json_file:
            persona_data = json.load(json_file)

        # Extract persona data
        user_name = persona_data.get("user_name", "You")
        character_name = persona_data.get("character_name", "")
        user_description = persona_data.get("user_description", "")
        system_prompt = persona_data.get("system_prompt", "")
        chat_instruct_command = persona_data.get("chat_instruct_command", "")

        logger.info(f"[Personas] Loaded persona data: user={user_name}, character={character_name}")

        # Prepare UI updates
        updates = {}

        # Update user name
        updates["name1"] = user_name

        # Update user description
        updates["user_bio"] = user_description

        # Update system message
        updates["custom_system_message"] = system_prompt

        # If we have a character, try to load it
        character_data = None
        if character_name:
            character_data = load_character_and_start_chat(character_name)
            if character_data:
                # Merge character updates
                updates.update(character_data)
            else:
                # If character load failed, just use the name
                updates["name2"] = character_name

        # Remember the persona name
        shared.settings['persona'] = persona_name
        if chat_instruct_command != "":
            shared.settings['chat-instruct_command'] = chat_instruct_command
            updates["chat-instruct_command"] = chat_instruct_command

        # Return the UI updates
        return updates, f"Persona '{persona_name}' loaded successfully"
    except FileNotFoundError:
        return None, f"The persona file '{file_path}' was not found"
    except json.JSONDecodeError:
        return None, f"Error decoding the persona file '{file_path}'"
    except Exception as e:
        logger.error(f"[Personas] Error loading persona: {e}")
        traceback.print_exc()
        return None, f"Error loading persona: {str(e)}"


def apply_settings_updates(updates_dict):
    """Apply updates to shared.settings"""
    if updates_dict:
        for key, value in updates_dict.items():
            if key in shared.settings:
                shared.settings[key] = value


def create_persona_json(persona_name, user_name=None, character_name=None, user_bio=None, system_message=None, chat_instruct_command=None):
    """Create a new persona JSON file with the current settings

    Args:
        persona_name: Name of the persona to create
        user_name: Optional user name from UI component
        character_name: Optional character name from UI component
        user_bio: Optional user bio from UI component
        system_message: Optional system message from UI component
        chat_instruct_command: Optional chat-instruct command block from the chat UI
    """
    # Create personas directory if it doesn't exist
    os.makedirs("user_data/personas", exist_ok=True)

    file_path = f"user_data/personas/{persona_name}.json"

    # Get values from UI components if provided, otherwise fall back to shared.settings
    if user_name is None:
        user_name = shared.settings.get('name1', 'You')

    if character_name is None:
        character_name = shared.gradio['character_menu'].value if shared.gradio.get('character_menu') is not None else ""

    if user_bio is None:
        user_bio = shared.settings.get('user_bio', '')

    if system_message is None:
        system_message = shared.settings.get('custom_system_message', '')

    if chat_instruct_command is None:
        chat_instruct_command = shared.settings.get('chat-instruct_command', '')

    # Create persona data structure
    persona_data = {
        "user_name": user_name,
        "character_name": character_name,
        "user_description": user_bio,
        "system_prompt": system_message,
        "chat_instruct_command": chat_instruct_command
    }

    try:
        with open(file_path, 'w') as json_file:
            json.dump(persona_data, json_file, indent=2)
        logger.info(f"[Personas] New persona '{persona_name}' created successfully")

        # Get updated list of personas
        personas = get_available_personas()
        return True, personas
    except Exception as e:
        logger.error(f"[Personas] Error creating persona: {e}")
        traceback.print_exc()
        return False, []


def get_available_personas():
    """Get a list of available personas from the personas directory."""
    # Create personas directory if it doesn't exist
    os.makedirs("user_data/personas", exist_ok=True)

    persona_files = glob.glob('user_data/personas/*.json')
    personas = [os.path.basename(f).split('.')[0] for f in persona_files]
    personas.sort()

    # Add Create New Persona option at the end
    personas.append("Create New Persona")
    return personas


def ui():
    # Add persona dropdown to sidebar
    with shared.ui_extension_point['sidebar']:
        with gr.Row():
            with gr.Column(scale=8):
                persona_dropdown = gr.Dropdown(
                    choices=get_available_personas(),
                    label='Persona',
                    value=shared.settings.get('persona', None),
                    visible=True, 
                    interactive=True,
                    elem_id='persona-dropdown'
                )
                shared.gradio['persona'] = persona_dropdown

            # Add buttons for refresh, load, and new
            with gr.Column(scale=1):
                with gr.Row():
                    # Refresh button
                    refresh_btn = gr.Button('🔄', elem_classes=['refresh-button'])
                    # Load button
                    load_btn = gr.Button('📂', elem_classes=['refresh-button'])
                    # New button
                    new_btn = gr.Button('➕', elem_classes=['refresh-button'])

            # Create a popup for entering the new persona name and capturing current UI state
            with gr.Box(visible=False) as new_persona_box:
                new_name = gr.Textbox(label="Enter name for new persona")

                # Hidden fields to capture current UI state when the dialog is opened
                current_user_name = gr.Textbox(visible=False)
                current_char_name = gr.Textbox(visible=False)
                current_user_bio = gr.Textbox(visible=False)
                current_system_msg = gr.Textbox(visible=False)
                current_instruct_cmd = gr.Textbox(visible=False)

                with gr.Row():
                    cancel_btn = gr.Button("Cancel")
                    create_btn = gr.Button("Create", variant="primary")

            # ----- Event handlers -----

            # Function to handle selection of a persona
            def on_persona_select(persona_name):
                if not persona_name or persona_name == "Create New Persona":
                    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), None

                # Load persona data
                updates, message = load_persona_json(persona_name)

                # Apply setting updates
                apply_settings_updates(updates)

                if updates:
                    # Prepare UI updates
                    user_name = updates.get('name1', gr.update())
                    char_name = updates.get('name2', gr.update())
                    user_bio = updates.get('user_bio', gr.update())
                    system_msg = updates.get('custom_system_message', gr.update())
                    greeting = updates.get('greeting', gr.update())
                    context = updates.get('context', gr.update())
                    char_menu = updates.get('character_menu', gr.update())

                    # Prepare history
                    history = get_default_history()
                    if 'greeting' in updates and updates['greeting']:
                        greeting_text = updates['greeting']
                        char_name = updates.get('name2', 'Assistant')
                        user_name = updates.get('name1', 'You')
                        greeting_with_names = greeting_text.replace('{{user}}', user_name).replace('{{char}}', char_name)
                        history['internal'] = [['<|BEGIN-VISIBLE-CHAT|>', greeting_with_names]]
                        history['visible'] = [['', greeting_with_names]]

                    # Return all UI updates - all the character settings and history
                    return user_name, char_name, user_bio, system_msg, greeting, context, char_menu, history
                else:
                    # Something went wrong
                    gr.Warning(message)
                    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), None

            # When persona is selected, update all relevant UI elements
            load_btn.click(
                on_persona_select,
                inputs=persona_dropdown,
                outputs=[
                    shared.gradio['name1'],
                    shared.gradio['name2'],
                    shared.gradio['user_bio'],
                    shared.gradio['custom_system_message'],
                    shared.gradio['greeting'],
                    shared.gradio['context'],
                    shared.gradio['character_menu'],
                    shared.gradio['history']
                ]
            ).then(
                chat.redraw_html,
                inputs=[
                    shared.gradio['history'],
                    shared.gradio['name1'],
                    shared.gradio['name2'],
                    shared.gradio['mode'],
                    shared.gradio['chat_style'],
                    shared.gradio['character_menu']
                ],
                outputs=shared.gradio['display']
            )

            # Auto-load on dropdown change
            persona_dropdown.change(
                on_persona_select,
                inputs=persona_dropdown,
                outputs=[
                    shared.gradio['name1'],
                    shared.gradio['name2'],
                    shared.gradio['user_bio'],
                    shared.gradio['custom_system_message'],
                    shared.gradio['greeting'],
                    shared.gradio['context'],
                    shared.gradio['character_menu'],
                    shared.gradio['history']
                ]
            ).then(
                chat.redraw_html,
                inputs=[
                    shared.gradio['history'],
                    shared.gradio['name1'],
                    shared.gradio['name2'],
                    shared.gradio['mode'],
                    shared.gradio['chat_style'],
                    shared.gradio['character_menu']
                ],
                outputs=shared.gradio['display']
            )

            # Refresh button handler
            def refresh_personas():
                # Get the updated list of personas
                personas = get_available_personas()
                # Return the updated list without changing the selected persona
                return gr.update(choices=personas, value=persona_dropdown.value)

            refresh_btn.click(
                refresh_personas,
                None,
                outputs=persona_dropdown
            )

            # New persona dialog handlers
            def show_new_dialog(user_name, char_name, user_bio, system_msg, chat_instruct_cmd):
                # Capture the current UI state when dialog is opened
                return [
                    gr.update(visible=True),       # Show the box
                    gr.update(value=""),           # Clear the name field
                    gr.update(value=user_name),    # Store current user name
                    gr.update(value=char_name),    # Store current character name
                    gr.update(value=user_bio),     # Store current user bio
                    gr.update(value=system_msg),   # Store current system message
                    gr.update(value=chat_instruct_cmd), # Store current chat instruct command
                ]

            def hide_dialog():
                # Just hide the dialog box, leave the stored values intact
                return gr.update(visible=False)

            def handle_create_persona(name, user_name, char_name, user_bio, system_message, chat_instruct_command):
                if name and name.strip():
                    # Get the current UI values to use for the persona
                    success, personas = create_persona_json(
                        name.strip(),
                        user_name=user_name,
                        character_name=char_name,
                        user_bio=user_bio,
                        system_message=system_message,
                        chat_instruct_command=chat_instruct_command
                    )
                    if success:
                        gr.Info(f"New persona '{name.strip()}' created successfully")
                        return gr.update(visible=False), gr.update(choices=personas, value=name.strip())
                    else:
                        gr.Warning("Failed to create persona")
                else:
                    gr.Warning("Please enter a name for the persona")

                return gr.update(visible=True), gr.update()

            # New persona button events
            new_btn.click(
                show_new_dialog, 
                inputs=[
                    shared.gradio['name1'],           # Current user name
                    shared.gradio['name2'],           # Current character name
                    shared.gradio['user_bio'],        # Current user bio
                    shared.gradio['custom_system_message'], # Current system message
                    shared.gradio['chat-instruct_command'] # Current chat instruct message
                ],
                outputs=[
                    new_persona_box, 
                    new_name,
                    current_user_name,
                    current_char_name,
                    current_user_bio,
                    current_system_msg,
                    current_instruct_cmd,
                ]
            )

            cancel_btn.click(hide_dialog, outputs=new_persona_box)

            create_btn.click(
                handle_create_persona, 
                inputs=[
                    new_name,
                    current_user_name,       # Use captured user name
                    current_char_name,       # Use captured character name
                    current_user_bio,        # Use captured user bio
                    current_system_msg,      # Use captured system message
                    current_instruct_cmd,    # Use captured chat instruct command
                ],
                outputs=[new_persona_box, persona_dropdown]
            )
