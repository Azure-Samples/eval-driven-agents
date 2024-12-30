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

# --- Constants ---
CREDENTIAL_SCOPES = ["https://cognitiveservices.azure.com/.default"]
ITERATION_RANGE = (5, 10)
REQUESTS_PER_CLIENT = 3
SESSION_ID_RANGE = (1, 99999)
SLEEP_RANGE = (0.5, 2.0)
CITIES = ["Seattle", "New York City", "Paris"]
DATES = ["tomorrow morning", "next Monday"]

# --- Mock Functions (Tools) ---
def get_weather(city: str) -> str:
    """(Mock) Returns weather info for the given city."""
    return f"The weather in {city} is nice."

def get_current_time() -> str:
    """(Mock) Returns a fake current time."""
    return "It's 10:00 AM."

def book_flight(departure_city: str, arrival_city: str, date: str) -> str:
    """(Mock) Books a flight and returns a confirmation."""
    return f"Booked flight from {departure_city} to {arrival_city} on {date}."

# --- Helper Functions ---
def create_client(endpoint: str, api_version: str) -> ChatCompletionsClient:
    """Creates the Azure OpenAI client."""
    return ChatCompletionsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
        credential_scopes=CREDENTIAL_SCOPES,
        api_version=api_version
    )

def handle_tool_calls(messages, response):
    """Executes tool calls if requested by the model and updates history.

    When the model determines it needs to use a function (tool), the `finish_reason` in the response will be 'tool_calls'.
    This function extracts the details of the tool calls, executes them, and adds the results back to the conversation history.
    """
    if response.choices[0].finish_reason == CompletionsFinishReason.TOOL_CALLS:
        # Add the assistant's message containing the tool call information to the messages list.
        messages.append(AssistantMessage(tool_calls=response.choices[0].message.tool_calls))
        # Iterate through each tool call requested by the model.
        for tool_call in response.choices[0].message.tool_calls:
            if isinstance(tool_call, ChatCompletionsToolCall):
                func_name = tool_call.function.name
                # Get the actual Python function to call based on the function name from the model.
                func = globals().get(func_name)
                if func:
                    # Extract the arguments for the function from the model's response.
                    args = json.loads(tool_call.function.arguments.replace("'", '"')) if tool_call.function.arguments else {}
                    # Execute the function and get the response.
                    messages.append(ToolMessage(tool_call_id=tool_call.id, content=func(**args)))
        return True
    return False

def ask_travel_agent(client: ChatCompletionsClient, departure_city: str, arrival_city: str, date: str, tools):
    """Asks the model to plan a trip and use tools.

    The 'tools' parameter defines the functions the model can call. The model decides when and how to use these tools based on the user's request.
    """
    messages = [
        SystemMessage(content="You are a travel assistant."),
        UserMessage(content=f"Plan travel from {departure_city} to {arrival_city} {date}. Get weather, time, and book flight.")
    ]
    for _ in range(3): # Limit tool call iterations
        response = client.complete(messages=messages, tools=tools)
        # Check if the model requested to call a function.
        if not handle_tool_calls(messages, response):
            # If no tool calls were made, the model should have provided the final answer.
            return response.choices[0].message.content.strip() if response.choices[0].message.content else "No response"
    return "Could not get final answer."

def run_session(client: ChatCompletionsClient, endpoint: str, api_version: str, session_id: str, num_iterations: int):
    """Runs the travel planning session.

    This function defines the available tools (functions) that the language model can call.
    The model can then intelligently decide to use these tools within the `ask_travel_agent` function
    to fulfill the user's request.
    """
    # Define the tools the model can use. Each tool specifies the function name, description, and parameters.
    weather_tool = ChatCompletionsToolDefinition(function=FunctionDefinition(name="get_weather", description="Get weather", parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}))
    time_tool = ChatCompletionsToolDefinition(function=FunctionDefinition(name="get_current_time", description="Get current time", parameters={"type": "object", "properties": {}, "required": []}))
    flight_tool = ChatCompletionsToolDefinition(function=FunctionDefinition(name="book_flight", description="Book flight", parameters={"type": "object", "properties": {"departure_city": {"type": "string"}, "arrival_city": {"type": "string"}, "date": {"type": "string"}}, "required": ["departure_city", "arrival_city", "date"]}))
    tools = [weather_tool, time_tool, flight_tool]

    for i in range(num_iterations):
        departure_city = random.choice(CITIES)
        arrival_city = random.choice([c for c in CITIES if c != departure_city])
        date = random.choice(DATES)
        answer = ask_travel_agent(client, departure_city, arrival_city, date, tools)
        print(f"Iteration {i+1}/{num_iterations} (Session ID: {session_id}): {departure_city} to {arrival_city} on {date}\nAnswer: {answer}\n---")
        if (i + 1) % REQUESTS_PER_CLIENT == 0:
            del client
            gc.collect()
            client = create_client(endpoint, api_version)
        time.sleep(random.uniform(*SLEEP_RANGE))

def main():
    """Main entry point."""
    endpoint = os.getenv("ENDPOINT")
    api_version = os.getenv("API_VERSION")
    app_insights_connection_string = os.getenv("APP_INSIGHTS_CONNECTION_STRING")

    # Initialize tracing for Azure AI Inference SDK.
    # This automatically instruments the ChatCompletionsClient. Every call made by the client will be tracked.
    AIInferenceInstrumentor().instrument(enable_content_recording=False)
    # Configure Azure Monitor to receive the telemetry data (traces) generated by the instrumentation.
    # Ensure the APP_INSIGHTS_CONNECTION_STRING environment variable is set correctly.
    configure_azure_monitor(connection_string=app_insights_connection_string)
    # Get a tracer instance from OpenTelemetry, which is used to create custom telemetry data (spans).
    tracer = get_tracer(__name__)

    # Create the ChatCompletionsClient. Tracing is automatically enabled for this client due to the AIInferenceInstrumentor.
    client = create_client(endpoint, api_version)

    num_iterations = random.randint(*ITERATION_RANGE)
    session_id = f"session-{random.randint(*SESSION_ID_RANGE)}"

    # Start a parent span to represent the entire travel planning session.
    # Spans help to group related operations together in your telemetry data.
    with tracer.start_as_current_span("travel-planning-session", kind=SpanKind.CLIENT) as session_span:
        # Add a session ID attribute to this span. This allows you to easily filter and query telemetry data for specific sessions.
        session_span.set_attribute("session.id", session_id)
        current_span = get_current_span()
        # If the current span is recording (which it should be), also add the session ID to it.
        if current_span.is_recording():
            current_span.set_attribute("session.id", session_id)

        # Run the travel planning session. The calls to the language model and any tool calls will be tracked within the tracing context.
        run_session(client, endpoint, api_version, session_id, num_iterations)

if __name__ == "__main__":
    main()