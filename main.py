from agent import kora

print("Kora is ready. Type your message (or 'quit' to exit).\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    response = kora.invoke({"input": user_input})
    print(f"\nKora: {response['output']}\n")