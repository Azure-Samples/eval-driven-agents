import os
import time
import random
import gc
import json
from dotenv import load_dotenv

load_dotenv()

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletionsToolCall,
    ChatCompletionsToolDefinition,
    FunctionDefinition,
    CompletionsFinishReason,
)
from azure.identity import DefaultAzureCredential
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.trace import get_tracer, get_current_span, SpanKind

# --------------------------------------------------------------------------
# Constants for easy configuration
# --------------------------------------------------------------------------

CREDENTIAL_SCOPES = ["https://cognitiveservices.azure.com/.default"]

# Number of travel scenario iterations
MIN_ITERATIONS = 5
MAX_ITERATIONS = 10
REQUESTS_PER_CLIENT = 3

# Session ID range
SESSION_ID_MIN = 1
SESSION_ID_MAX = 99999

# Sleep intervals between requests
SLEEP_MIN = 0.5
SLEEP_MAX = 2.0

# Cities and dates for variety
CITIES = ["Seattle", "New York City", "Paris", "Tokyo", "London", "San Francisco", "Toronto"]
DATES = ["tomorrow morning", "next Monday", "this weekend", "in two days", "on July 15th"]


# --------------------------------------------------------------------------
# Mock Functions (Tools)
# --------------------------------------------------------------------------

def get_weather(city: str) -> str:
    """Mock function: returns weather info for the given city."""
    weather_info = {
        "Seattle": "Rainy",
        "New York City": "Sunny",
        "Paris": "Cloudy",
        "Tokyo": "Clear",
        "London": "Foggy",
        "San Francisco": "Windy",
        "Toronto": "Snowy"
    }
    return f"The weather in {city} is {weather_info.get(city, 'Unknown')}."

def get_current_time() -> str:
    """Mock function: returns a fake current time."""
    return "The current time is 10:00 AM UTC."

def book_flight(departure_city: str, arrival_city: str, date: str) -> str:
    """Mock function: books a flight and returns a confirmation code."""
    confirmation_code = f"FLIGHT-{random.randint(10000,99999)}"
    return f"Your flight from {departure_city} to {arrival_city} on {date} is booked. Confirmation: {confirmation_code}"


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def create_client(endpoint: str, api_version: str) -> ChatCompletionsClient:
    """
    Create and return a ChatCompletionsClient instance using DefaultAzureCredential.
    """
    return ChatCompletionsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
        credential_scopes=CREDENTIAL_SCOPES,
        api_version=api_version
    )

def handle_tool_calls(messages, response):
    """
    If the model requested tool calls, execute them and update the conversation history.
    Returns True if tools were called, False otherwise.
    """
    if response.choices[0].finish_reason == CompletionsFinishReason.TOOL_CALLS:
        # Add assistant tool calls to the conversation
        messages.append(AssistantMessage(tool_calls=response.choices[0].message.tool_calls))
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                if isinstance(tool_call, ChatCompletionsToolCall):
                    args = {}
                    if tool_call.function.arguments:
                        args = json.loads(tool_call.function.arguments.replace("'", '"'))
                    func = globals().get(tool_call.function.name)
                    if func:
                        function_response = func(**args)
                        messages.append(ToolMessage(tool_call_id=tool_call.id, content=function_response))
        return True
    return False


def ask_travel_agent(client: ChatCompletionsClient, departure_city: str, arrival_city: str, date: str, tools) -> str:
    """
    Ask the model to:
    - Provide the weather in the arrival city.
    - Get current time.
    - Book a flight from departure_city to arrival_city on the given date.
    Then provide a final answer summarizing all results.
    """
    messages = [
        SystemMessage(content=(
            "You are a travel assistant with the ability to call external functions (tools) to help the user. "
            "First, call the appropriate tools to gather the requested information. "
            "After you have all the info, respond with a final answer summarizing everything. "
            "If you have all the info you need, do not call any more tools; just provide the final assistant message."
        )),
        UserMessage(content=(
            f"I want to travel from {departure_city} to {arrival_city} {date}. "
            f"Can you tell me the weather at {arrival_city}, get the current time, "
            "and then book a flight for me?"
        ))
    ]

    # We'll loop until we get a final answer that isn't TOOL_CALLS.
    # This handles multiple calls if the model decides to use tools more than once.
    for _ in range(5):  # Safety limit to avoid infinite loops
        response = client.complete(messages=messages, tools=tools)
        if handle_tool_calls(messages, response):
            # Tools were called, so we loop again
            continue
        else:
            # No more tool calls, we should have a final answer
            content = response.choices[0].message.content
            return content.strip() if content is not None else "No response content available"

    # If we reach here, it means we never got a final answer.
    return "No response content available"


def run_session(client: ChatCompletionsClient, endpoint: str, api_version: str, session_id: str, num_iterations: int) -> None:
    """
    Run a travel scenario multiple times.
    Each iteration:
    - Picks random departure and arrival cities, and a random date.
    - Asks the model to plan the trip, calling functions as needed.
    """

    # Define tools that the model can use
    weather_tool = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_weather",
            description="Get the weather information for the specified city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City for weather info"}
                },
                "required": ["city"]
            },
        )
    )

    time_tool = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_current_time",
            description="Get the current time.",
            parameters={"type": "object", "properties": {}, "required": []},
        )
    )

    flight_tool = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="book_flight",
            description="Book a flight given the departure city, arrival city, and date.",
            parameters={
                "type": "object",
                "properties": {
                    "departure_city": {"type": "string", "description": "Departure city"},
                    "arrival_city": {"type": "string", "description": "Arrival city"},
                    "date": {"type": "string", "description": "Date of the flight"}
                },
                "required": ["departure_city", "arrival_city", "date"]
            },
        )
    )

    tools = [weather_tool, time_tool, flight_tool]

    for i in range(num_iterations):
        departure_city = random.choice(CITIES)
        arrival_city = random.choice([c for c in CITIES if c != departure_city])
        date = random.choice(DATES)

        answer = ask_travel_agent(client, departure_city, arrival_city, date, tools)

        print(f"Iteration {i+1} of {num_iterations} (Session ID: {session_id})")
        print("Scenario:", f"Travel from {departure_city} to {arrival_city} {date}. Get weather, current time, and book flight.")
        print("Final Answer:", answer)
        print("---")

        # Periodically recreate the client to free resources
        if (i + 1) % REQUESTS_PER_CLIENT == 0:
            del client
            gc.collect()
            client = create_client(endpoint, api_version)

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def main():
    """
    Main entry point:
    - Sets up telemetry and tracing
    - Runs multiple travel planning iterations with function calls
    """
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
