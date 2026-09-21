import gradio as gr
from carbon_agent.app import demo
from carbon_agent.ui.theme import CUSTOM_CSS

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7865,
        theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="slate"),
        css=CUSTOM_CSS,
        share=False
    )

# Run with: python app.py
