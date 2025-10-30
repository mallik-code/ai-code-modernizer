import os
from langchain.chat_models import init_chat_model

#mallikarao589@gmail.com - code-catalyst
os.environ["GOOGLE_API_KEY"] = "AIzaSyCsoBG_YdsfSTIGXGiYkExrZZgmi8BIb-s"

#chat_model = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=1)
chat_model = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=0.7, timeout=30, max_tokens=1000)
response = chat_model.invoke("Why do parrots talk?")
print(response)
# Expected output: A detailed explanation of why parrots mimic human speech, including their social nature and vocal learning abilities.