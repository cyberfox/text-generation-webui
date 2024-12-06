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



def ui():
    with shared.ui_extension_point['chat_management']:
        shared.gradio['Print chat'] = gr.Button('Print chat',
                                                    elem_classes=['refresh-button', 'focus-on-chat-input'])

    with shared.ui_extension_point['sidebar']:
        with gr.Row():
            shared.gradio['persona'] = gr.Dropdown(choices=["Morgan", "Jenifer", "Coding", "IaC"], label='Persona',
                                                      value=shared.settings.get('persona', "Morgan"),
                                                      visible=shared.settings['mode'] != 'instruct', interactive=True)
            shared.gradio['persona'].change(chat.redraw_html, gradio(reload_arr), gradio('display'), show_progress=False)

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
