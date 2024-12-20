import os
import time
import random
import gc

from dotenv import load_dotenv
load_dotenv()

from azure.ai.inference import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.trace import get_tracer, get_current_span, SpanKind

# --------------------------------------------------------------------------
# Constants for easy configuration
# --------------------------------------------------------------------------

# API and authentication related constants
CREDENTIAL_SCOPES = ["https://cognitiveservices.azure.com/.default"]

# Token limits for requests
MAX_TOKENS_QUESTION_GENERATION = 150
MAX_TOKENS_QUESTION_ANSWER = 100

# Iteration count and client recreation frequency
MIN_ITERATIONS = 5
MAX_ITERATIONS = 25
REQUESTS_PER_CLIENT = 5

# Random seed range used to generate unique questions
SEED_MIN = 1000
SEED_MAX = 9999

# Session ID range
SESSION_ID_MIN = 1
SESSION_ID_MAX = 99999

# Sleep intervals between requests
SLEEP_MIN = 0.5
SLEEP_MAX = 2.0

# --------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------

def create_client(endpoint: str, api_version: str) -> ChatCompletionsClient:
    """
    Create and return a ChatCompletionsClient instance using DefaultAzureCredential.

    Parameters
    ----------
    endpoint : str
        The Azure OpenAI endpoint.
    api_version : str
        The API version to use for the Azure OpenAI calls.

    Returns
    -------
    ChatCompletionsClient
        The inference client configured with default Azure credentials.
    """
    return ChatCompletionsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
        credential_scopes=CREDENTIAL_SCOPES,
        api_version=api_version
    )


def generate_unique_question(client: ChatCompletionsClient, seed: str) -> str:
    """
    Ask the language model to generate a unique question based on a given seed.

    Parameters
    ----------
    client : ChatCompletionsClient
        The inference client to use for completion requests.
    seed : str
        A random seed string used to prompt the LLM for a unique question.

    Returns
    -------
    str
        The generated question.
    """
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are a creative assistant. I will provide you a random seed each time. "
                "Based on that seed, produce a unique and interesting question I could ask "
                "a large language model. Respond with only the question text, nothing else."
            )
        },
        {"role": "user", "content": f"The seed is: {seed}"}
    ]

    response = client.complete(messages=prompt_messages, max_tokens=MAX_TOKENS_QUESTION_GENERATION)
    question = response.choices[0].message.content.strip()

    # Clean up and force garbage collection
    del response
    gc.collect()

    return question


def ask_question(client: ChatCompletionsClient, question: str) -> str:
    """
    Ask the given question to the language model and return the answer.

    Parameters
    ----------
    client : ChatCompletionsClient
        The inference client to use for completion requests.
    question : str
        The question to ask the LLM.

    Returns
    -------
    str
        The answer from the LLM.
    """
    prompt_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question}
    ]

    response = client.complete(messages=prompt_messages, max_tokens=MAX_TOKENS_QUESTION_ANSWER)
    answer = response.choices[0].message.content.strip()

    # Clean up and force garbage collection
    del response
    gc.collect()

    return answer


def run_session(client: ChatCompletionsClient, endpoint: str, api_version: str, session_id: str, num_iterations: int) -> None:
    """
    Run the session loop where each iteration:
    - Generates a random seed.
    - Requests a unique question from the LLM.
    - Asks the generated question and prints the answer.

    Parameters
    ----------
    client : ChatCompletionsClient
        The inference client to use for completion requests.
    endpoint : str
        The Azure OpenAI endpoint.
    api_version : str
        The API version to use for the Azure OpenAI calls.
    session_id : str
        The session ID used for telemetry grouping.
    num_iterations : int
        The number of iterations (Q&A pairs) to run.
    """
    for i in range(num_iterations):
        seed = str(random.randint(SEED_MIN, SEED_MAX))
        generated_question = generate_unique_question(client, seed)
        answer = ask_question(client, generated_question)

        print(f"Iteration {i+1} of {num_iterations}: (Session ID: {session_id})")
        print("Q:", generated_question)
        print("A:", answer)
        print("---")

        # Periodically recreate the client to free resources
        if (i + 1) % REQUESTS_PER_CLIENT == 0:
            del client
            gc.collect()
            client = create_client(endpoint, api_version)

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def main():
    """
    Main entry point of the script:
    - Reads configuration from environment variables.
    - Creates a client.
    - Creates a session span with a unique session_id.
    - Runs a random number of iterations between MIN_ITERATIONS and MAX_ITERATIONS.
    """
    # Load environment variables
    endpoint = os.getenv("ENDPOINT")
    api_version = os.getenv("API_VERSION")
    app_insights_connection_string = os.getenv("APP_INSIGHTS_CONNECTION_STRING")

    # Instrument and configure telemetry
    AIInferenceInstrumentor().instrument(enable_content_recording=False)
    configure_azure_monitor(connection_string=app_insights_connection_string)

    tracer = get_tracer(__name__)

    # Create the initial client
    client = create_client(endpoint, api_version)

    # Generate a random number of iterations
    num_iterations = random.randint(MIN_ITERATIONS, MAX_ITERATIONS)

    # Create a session ID and start a parent session span
    session_id = f"session-{random.randint(SESSION_ID_MIN, SESSION_ID_MAX)}"
    with tracer.start_as_current_span("gen-ai-session", kind=SpanKind.CLIENT) as session_span:
        session_span.set_attribute("session.id", session_id)

        current_span = get_current_span()
        if current_span.is_recording():
            current_span.set_attribute("session.id", session_id)

        # Run the main logic
        run_session(client, endpoint, api_version, session_id, num_iterations)


if __name__ == "__main__":
    main()
