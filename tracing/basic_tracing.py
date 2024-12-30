import gc
import os
import random
import time
from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from opentelemetry.trace import get_tracer, get_current_span, SpanKind

load_dotenv()

# --------------------------------------------------------------------------
# Setup Constants and Config
# --------------------------------------------------------------------------

# The model deployment name set in your Azure AI Foundry project.
# Ensure you've set this in your environment variables.
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
if not MODEL_DEPLOYMENT_NAME:
    raise ValueError("MODEL_DEPLOYMENT_NAME is not set in the environment.")

MAX_TOKENS_QUESTION = 150
MAX_TOKENS_ANSWER = 100

ITERATION_COUNT = random.randint(5, 10)  # between 5 and 10
REQUESTS_PER_CLIENT = 5

SEED_RANGE = (1000, 9999)
SESSION_ID = f"session-{random.randint(1, 99999)}"

SLEEP_RANGE = (0.5, 2.0)

# Create a tracer to produce and manage spans.
tracer = get_tracer(__name__)


def generate_unique_question(client, seed: str) -> str:
    """
    Generate a unique question based on a seed using the ChatCompletionsClient.

    Args:
        client: The ChatCompletionsClient from your AIProjectClient.
        seed: The seed string to guide the question generation.

    Returns:
        A unique question as a string.
    """
    prompt_messages = [
        {"role": "system", "content": "You are a creative assistant. Given a seed, produce a unique question."},
        {"role": "user", "content": f"The seed is: {seed}"}
    ]
    response = client.complete(model=MODEL_DEPLOYMENT_NAME, messages=prompt_messages, max_tokens=MAX_TOKENS_QUESTION)
    question = response.choices[0].message.content.strip()
    del response
    gc.collect()
    return question


def ask_question(client, question: str) -> str:
    """
    Ask the given question using the ChatCompletionsClient and return the answer.

    Args:
        client: The ChatCompletionsClient from your AIProjectClient.
        question: The user question string.

    Returns:
        The model's answer as a string.
    """
    prompt_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question}
    ]
    response = client.complete(model=MODEL_DEPLOYMENT_NAME, messages=prompt_messages, max_tokens=MAX_TOKENS_ANSWER)
    answer = response.choices[0].message.content.strip()
    del response
    gc.collect()
    return answer


def run_session(project_client: AIProjectClient, client, session_id: str, num_iterations: int):
    """
    Run a session of Q&A. After a certain number of requests, the ChatCompletionsClient is recreated
    to demonstrate lifecycle changes.

    Args:
        project_client: The AIProjectClient connected to your Azure AI Foundry project.
        client: The current ChatCompletionsClient.
        session_id: A unique session ID for logging and tracing.
        num_iterations: Number of Q&A rounds.
    """
    for i in range(num_iterations):
        seed = str(random.randint(*SEED_RANGE))
        question = generate_unique_question(client, seed)
        answer = ask_question(client, question)
        print(f"Iteration {i+1}/{num_iterations} [Session: {session_id}]")
        print("Q:", question)
        print("A:", answer)
        print("---")

        # Every few requests, recreate the client to simulate lifecycle changes.
        if (i + 1) % REQUESTS_PER_CLIENT == 0:
            del client
            gc.collect()
            client = project_client.inference.get_chat_completions_client()

        time.sleep(random.uniform(*SLEEP_RANGE))


def main():
    """
    Main entry point.

    This example shows how to:
    1. Connect to an Azure AI Foundry project using AIProjectClient.
    2. Enable telemetry/tracing automatically with project_client.telemetry.enable().
    3. Retrieve a traced ChatCompletionsClient for Q&A.
    """

    project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
    if not project_connection_string:
        raise ValueError("PROJECT_CONNECTION_STRING is not set in the environment.")

    # Create and authenticate AIProjectClient.
    # DefaultAzureCredential will automatically find your credentials (e.g., from 'az login').
    with AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=project_connection_string
    ) as project_client:

        # Enable telemetry to automatically configure Application Insights and tracing.
        project_client.telemetry.enable()

        # Obtain a ChatCompletionsClient that's already instrumented for tracing.
        with project_client.inference.get_chat_completions_client() as client:
            # Start a parent span representing this entire session.
            with tracer.start_as_current_span("gen-ai-session", kind=SpanKind.CLIENT) as session_span:
                session_span.set_attribute("session.id", SESSION_ID)
                current_span = get_current_span()
                if current_span.is_recording():
                    current_span.set_attribute("session.id", SESSION_ID)

                # Run the main logic of generating and asking questions.
                run_session(project_client, client, SESSION_ID, ITERATION_COUNT)


if __name__ == "__main__":
    main()
