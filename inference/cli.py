import gradio as gr
import json

def format_output(raw_json):
    try:
        parsed = json.loads(raw_json)
        return parsed
    except json.JSONDecodeError:
        # Try to extract JSON from malformed output
        start = raw_json.find('{')
        end = raw_json.rfind('}') + 1
        if start != -1 and end != 0:
            try:
                return json.loads(raw_json[start:end])
            except:
                return {"error": "Could not parse JSON", "raw_output": raw_json}
        return {"error": "No valid JSON found", "raw_output": raw_json}

demo = gr.Interface(
    fn=lambda x: format_output(generate_shadcn_component(x)),
    inputs=gr.Textbox(lines=3, placeholder="Describe the component (e.g. 'Create an animated dropdown')"),
    outputs=gr.JSON(),
    title="ShadCN Component Generator",
    examples=[
        ["A horizontal scrolling marquee with pauseOnHover"],
        ["A 3D card component with perspective effects"],
        ["An animated toggle switch with accessibility support"]
    ]
)

demo.launch(share=True)