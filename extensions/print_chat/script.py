import os
import json
import glob
import gradio as gr
from functools import partial
from modules import shared, chat, utils
from modules import ui as core_ui
from modules.utils import gradio
from modules.ui_chat import inputs
from modules.ui_chat import reload_arr


def ui():
    # Add persona dropdown to sidebar
    # Add "Replace & Continue" button to chat buttons
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
