import typer
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory

# Load environment variables
load_dotenv()

# Initialize the Groq model
llm = ChatGroq(model="llama-3.3-70b-versatile")

# Create a prompt template with history support
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert software engineering assistant. Provide clear, concise, and accurate code and explanations."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# Create the conversation chain using the new approach
chain_with_history = prompt_template | llm

# Create a store for chat histories
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Create the chain with message history
chain = RunnableWithMessageHistory(
    chain_with_history,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

app = typer.Typer()


@app.command()
def chat(
    prompt: str = typer.Argument(
        None,
        help="A single prompt to process. If not provided, starts interactive mode.",
    ),
):
    """
    Chat with the LLM. If no prompt is provided, enters interactive mode.
    """
    import uuid
    session_id = str(uuid.uuid4())

    if prompt:
        # Run once with the provided prompt
        response = chain.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": session_id}}
        )
        print(response.content)
    else:
        # Interactive mode
        print("Starting interactive chat. Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            response = chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            print(response.content)


if __name__ == "__main__":
    app()
