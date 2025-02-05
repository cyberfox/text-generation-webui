import os
import json
import gradio as gr
from functools import partial
from modules import shared, chat
from modules import ui as core_ui
from modules.utils import gradio
from modules.ui_chat import inputs


params = {
    "display_name": "Printable",
    "is_tab": False
}

reload_arr = ('history', 'name1', 'name2', 'mode', 'chat_style', 'character_menu')


def update_user_description(description):
    # Assuming `shared` or another module holds user profiles or states
    try:
        shared.settings['user_bio'] = description
        print("User description updated successfully.")
    except Exception as e:
        print(f"Error updating user description: {e}")


def update_system_message(system_message):
    try:
        shared.settings['custom_system_message'] = system_message
        print("System message updated successfully.")
    except Exception as e:
        print(f"Error updating system message: {e}")


def load_persona_json(persona_name, user1='You', user2='AI Assistant'):
    file_path = f"personas/{persona_name}.json"  # specify your JSON file path
    try:
        with open(file_path, 'r') as json_file:
            persona_data = json.load(json_file)
            user_name = persona_data.get("user_name", user1)
            character_name = persona_data.get("character_name", user2)
            user_description = persona_data.get("user_description", "")
            system_message = persona_data.get("system_message", None)
            # Assuming you have methods or variables where you store these:
            update_user_description(user_description)
            if system_message:
                update_system_message(system_message)
    except FileNotFoundError:
        print("The persona JSON file was not found.")
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")


def create_persona_json(persona_name):
    file_path = f"personas/{persona_name}.json"
    default_persona_data = {
        "user_description": shared.settings['user_bio'],
        "system_message": shared.settings['custom_system_message']
    }
    try:
        with open(file_path, 'w') as json_file:
            json.dump(default_persona_data, json_file, indent=4)
        print(f"New persona '{persona_name}' created successfully.")
    except Exception as e:
        print(f"Error creating persona JSON file: {e}")


def prompt_for_persona_name():
    # Define Gradio text input and submit button for the new persona name input
    with gr.Blocks() as persona_prompt:
        name_input = gr.Textbox(label="Enter new persona name", placeholder="Type here...")
        submit_button = gr.Button("Submit")

        def submit_action(name):
            if name:
                create_persona_json(name)  # Assuming create_persona_json is defined elsewhere
            else:
                print("No name entered.")
            persona_prompt.close()  # Close the prompt once the name is handled

        submit_button.click(submit_action, inputs=name_input)

    persona_prompt.launch()  # Launch the Gradio interface for this prompt


def on_persona_change(selected_persona):
    print(selected_persona)
    chosen_name = selected_persona.get('persona', None)
    user1 = selected_persona.get('name1', 'You')
    user2 = selected_persona.get('name2', 'AI Assistant')
    if chosen_name == "Create New Persona":
        # Trigger the Gradio prompt for entering a new persona name
        prompt_for_persona_name()
    else:
        load_persona_json(chosen_name, user1, user2)

        chat.redraw_html(gradio(reload_arr), gradio('display'))


def ui():
#    with shared.ui_extension_point['chat_management']:
#        shared.gradio['Print chat'] = gr.Button('Print chat',
#                                                    elem_classes=['refresh-button', 'focus-on-chat-input'])

    with shared.ui_extension_point['sidebar']:
        with gr.Row():
            shared.gradio['persona'] = gr.Dropdown(choices=["Morgan", "Jenifer", "Coding", "IaC", "----",
                                                            "Create New Persona"], label='Persona',
                                                      value=shared.settings.get('persona', "Morgan"),
                                                      visible=shared.settings['mode'] != 'instruct', interactive=True)
            # shared.gradio['persona'].change(on_persona_change, gradio(reload_arr), gradio('display'),
            #                                 show_progress=False)
            print(shared.input_elements)
            shared.gradio['persona'].change(core_ui.gather_interface_values, gradio(shared.input_elements + ['persona']), gradio('interface_state')).then(
                on_persona_change, gradio('interface_state'), show_progress=False).then(
                None, None, None, js=f'() => {{{core_ui.update_big_picture_js}; updateBigPicture()}}')

    with shared.ui_extension_point['chat_buttons']:
        shared.gradio['Replace & Continue'] = gr.Button('Replace & Continue', elem_id='Replace-continue')

        shared.gradio['Replace & Continue'].click(
            core_ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
            chat.replace_last_reply, gradio('textbox', 'interface_state'), gradio('history')).then(
            lambda: '', None, gradio('textbox'), show_progress=False).then(
            chat.redraw_html, gradio(reload_arr), gradio('display')).then(
            partial(chat.generate_chat_reply_wrapper, _continue=True), gradio(inputs), gradio('display', 'history'),
            show_progress=False).then(
            core_ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
            chat.save_history, gradio('history', 'unique_id', 'character_menu', 'mode'), None).then(
            lambda: None, None, None, _js=f'() => {{{core_ui.audio_notification_js}}}')
