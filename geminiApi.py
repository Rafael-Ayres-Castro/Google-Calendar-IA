from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Como criar um bolo de maneira reduzida"
)

print([step for step in interaction.steps])

client.interactions.create()