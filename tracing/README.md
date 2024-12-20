# Observability & Tracing with Azure AI Inference SDK 🚀

**Get visibility into your model's behavior and performance.** This sub-folder demos how to trace and analyze tool calls, requests, and responses using the Azure AI Inference SDK with OpenTelemetry and Application Insights.

## Prerequisites 📋

1. **Azure AI Foundry Setup**
   - Go to [Azure AI Foundry](https://ai.azure.com)
   - Create a Hub (or use an existing one)
   - Create a Project within your Hub
   - Deploy a model (preferably Azure OpenAI)
     - Navigate to Models > Deploy
     - Select Azure OpenAI from the model catalog
     - Complete the deployment configuration

2. **Configure Tracing**
   - In your AI Foundry Project:
     - Go to Settings > Tracing
     - Enable tracing
     - Configure Application Insights connection
     - Save your settings

3. **Gather Required Information**
   - From your deployed model's endpoint page, note down:
     - Endpoint URL
     - API Version
   - From Application Insights:
     - Connection String

## Quick Start ✅

1. **Install Dependencies**  
   Choose one of these methods:

   **Using uv (Recommended - Fastest)**
   ```bash
   # Install uv if you haven't already
   pip install uv
   
   # Create and activate virtual environment
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   .venv\Scripts\activate     # On Windows
   
   # Install dependencies
   uv pip install .
   ```

   **Using conda**
   ```bash
   # Create and activate conda environment
   conda create -n tracing-demo python=3.10
   conda activate tracing-demo
   
   # Install dependencies
   pip install .
   ```
   *(Uses [pyproject.toml](./pyproject.toml) for a modern setup.)*

2. **Create `.env` from Example**  
   ```bash
   cp .env.example .env
   ```
   Update values for:
   - `ENDPOINT` (from AI Foundry model endpoint page)
   - `API_VERSION` (from AI Foundry model endpoint page)
   - `APP_INSIGHTS_CONNECTION_STRING` (from Application Insights)

3. **Run a Sample**  
   ```bash
   python basic_function_calling.py
   ```
   or  
   ```bash
   python basic_tracing.py
   ```

4. **Check Telemetry & Traces**  
   - Go to your AI Foundry Project
   - Navigate to the Tracing blade
   - View request traces, spans, and tool call logs
   
   **Tip:** Adjust environment variables in `.env` for different levels of instrumentation.

## What's Here? 🎯

- **`basic_function_calling.py`**: Demonstrates function (tool) calls with full traceability.
- **`basic_tracing.py`**: Showcases request/response tracing for Q&A scenarios.
- **`.env.example`**: Template for your environment variables—just `cp` & edit.
- **`pyproject.toml`**: Modern Python packaging for clean dependency management.

Happy Tracing! ✨