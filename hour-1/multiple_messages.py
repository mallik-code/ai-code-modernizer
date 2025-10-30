import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "AIzaSyCsoBG_YdsfSTIGXGiYkExrZZgmi8BIb-s"
model = init_chat_model(
    "google_genai:gemini-2.5-flash-lite",
    # Kwargs passed to the model:
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
)

# Use the imported message classes
conversations = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Translate: I love programming"),
    # AIMessage(content="J'adore la programmation."),
    HumanMessage(content="Translate: I love building applications.")
]

response = model.invoke(conversations)
print(response)