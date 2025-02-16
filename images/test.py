import ollama

response = ollama.chat(
    model = "llava:7b",
    messages = [
        {"role": "user", "content": "describe the image", "images": [".\\3BSfxwz.jpg"]}
    ]
)

print(response["message"]['content'])
