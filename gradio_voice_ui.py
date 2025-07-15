import gradio as gr
import requests

def ask_agent(audio_path):
    text = gr.Audio(transcribe=True)(audio_path)
    response = requests.post("http://localhost:8000/agent_api", json={"query": text})
    return response.json()["reply"]

gr.Interface(
    fn=ask_agent,
    inputs=gr.Audio(source="microphone", type="filepath", label="🎤 Speak your query"),
    outputs="text",
    title="🗣️ Budgeting Voice Assistant"
).launch()