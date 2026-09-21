"""
Tab 3: AI Carbon Advisor Tab.
Conversational agent interface equipped with deterministic tool calling and transparent trace logs.
"""
import gradio as gr
from typing import List, Tuple
from carbon_agent.agents.advisor_agent import CarbonAdvisorAgent

advisor_agent = CarbonAdvisorAgent()


def render_advisor_tab(state: gr.State):
    """Render components for the AI Carbon Advisor chat tab."""
    gr.Markdown("### 🤖 AI Carbon Advisor (Tool-Augmented Agent)")
    gr.Markdown(
        "Ask questions regarding your footprint, hotspots, simulations, or predictions. "
        "The agent queries deterministic calculation tools before answering—**never hallucinating numbers**."
    )

    # Preset quick-prompt buttons
    with gr.Row():
        btn_q1 = gr.Button("🔍 Why is my carbon footprint high?", size="sm")
        btn_q2 = gr.Button("⚡ What if I cut electricity by 20%?", size="sm")
        btn_q3 = gr.Button("📈 What is my predicted emission next month?", size="sm")
        btn_q4 = gr.Button("🚗 How can I reduce transport emissions?", size="sm")

    chatbot = gr.Chatbot(label="Agent Conversation", height=420)
    
    with gr.Row():
        msg_input = gr.Textbox(
            label="Your Message",
            placeholder="Type your question here (e.g., 'What happens if I reduce car usage by 30%?')...",
            lines=1,
            scale=5
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    with gr.Accordion("🛠️ Tool-Calling & Agent Reasoning Traces", open=True):
        tool_trace_display = gr.Markdown("*No tool calls executed yet in this session.*")

    def handle_user_query(user_msg, chat_history, current_state):
        if not user_msg or not user_msg.strip():
            return "", chat_history, "*No tool calls executed.*", current_state

        chat_history = chat_history or []
        current_state = current_state or {}

        # Call Advisor Agent
        response_text, tool_calls = advisor_agent.respond(user_msg, current_state, chat_history)

        chat_history.append((user_msg, response_text))

        # Format tool trace markdown
        if tool_calls:
            trace_md = "#### ⚙️ Executed Deterministic Tool Traces:\n"
            for tc in tool_calls:
                trace_md += f"- **Tool Called:** `{tc['tool']}`\n"
                trace_md += f"  - **Purpose:** {tc['reason']}\n"
                trace_md += f"  - **Arguments:** `{tc['input']}`\n"
        else:
            trace_md = "*No tool calls required for this general query.*"

        return "", chat_history, trace_md, current_state

    # Event handlers
    send_btn.click(
        fn=handle_user_query,
        inputs=[msg_input, chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )
    msg_input.submit(
        fn=handle_user_query,
        inputs=[msg_input, chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )

    # Preset button click handlers
    btn_q1.click(
        fn=lambda ch, st: handle_user_query("Why is my carbon footprint high?", ch, st),
        inputs=[chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )
    btn_q2.click(
        fn=lambda ch, st: handle_user_query("What happens if I reduce electricity consumption by 20%?", ch, st),
        inputs=[chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )
    btn_q3.click(
        fn=lambda ch, st: handle_user_query("What is my predicted emission next month?", ch, st),
        inputs=[chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )
    btn_q4.click(
        fn=lambda ch, st: handle_user_query("How can I reduce transportation emissions?", ch, st),
        inputs=[chatbot, state],
        outputs=[msg_input, chatbot, tool_trace_display, state]
    )

    return chatbot
