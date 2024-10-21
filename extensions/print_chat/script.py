from modules import shared, chat
import gradio as gr
from modules.utils import gradio


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
