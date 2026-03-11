"""
Gradio UI for the Multi-Agent AI System.
"""

from __future__ import annotations
import asyncio
import traceback
import gradio as gr

from common.config import get_settings
from common.logging import setup_logging, get_logger
from ui.api_client import OrchestratorClient
from ui.components.news_card import format_news_section
from ui.components.weather_card import format_weather_card
from ui.components.report_viewer import format_report

setup_logging()
logger = get_logger("ui")
settings = get_settings()
client = OrchestratorClient()

EXAMPLE_QUERIES = [
    "What is the weather in London?",
    "Latest news about artificial intelligence",
    "Weather in Tokyo and related news",
    "Generate a report about climate change news",
    "What is the current weather in Paris and any news about it?",
    "News about SpaceX",
]

CSS = """
.main-header { text-align: center; padding: 20px 0; }
.result-box { min-height: 200px; }
.status-ok { color: #4caf50; font-weight: bold; }
.status-err { color: #f44336; font-weight: bold; }
"""


def run_async(coro):
    """Run async coroutine synchronously for Gradio."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def process_query(query: str) -> tuple[str, str, str, str]:
    """
    Process a user query through the orchestrator.
    Returns: (summary, news_html, weather_html, report_html)
    """
    if not query.strip():
        return "Please enter a query.", "", "", ""

    try:
        response = run_async(client.query(query))
    except Exception as e:
        error_msg = f"Error connecting to orchestrator: {e}\n\nMake sure all services are running (see README)."
        logger.error("ui_query_failed", error=str(e))
        return error_msg, "", "", ""

    summary = response.get("summary", "No summary available.")
    results = response.get("results", [])

    news_html = ""
    weather_html = ""
    report_html = ""

    for result in results:
        if not result.get("success"):
            continue

        agent = result.get("agent", "")
        data = result.get("data", {}) or {}
        structured = data.get("structured") or {}

        if agent == "news_agent" and structured:
            articles = structured.get("articles", [])
            if articles:
                news_html = format_news_section(articles)

        elif agent == "weather_agent" and structured:
            weather = structured.get("weather", {})
            if weather:
                weather_html = format_weather_card(weather)
            elif structured:
                weather_html = format_weather_card(structured)

        elif agent == "report_agent" and structured:
            markdown = structured.get("markdown", "")
            if markdown:
                report_html = format_report(markdown)

    return summary, news_html, weather_html, report_html


def check_health() -> str:
    try:
        health = run_async(client.health())
        agents = health.get("agents", {})
        lines = [f"Orchestrator: OK"]
        for agent, status in agents.items():
            icon = "OK" if status else "UNREACHABLE"
            lines.append(f"{agent}: {icon}")
        return "\n".join(lines)
    except Exception as e:
        return f"Orchestrator unreachable: {e}"


with gr.Blocks(css=CSS, title="Multi-Agent AI System") as demo:
    gr.Markdown(
        """
        # Multi-Agent AI System
        Powered by Groq LLM, MCP Tools, and A2A Protocol
        """,
        elem_classes=["main-header"],
    )

    with gr.Row():
        with gr.Column(scale=4):
            query_input = gr.Textbox(
                label="Your Query",
                placeholder="e.g. What is the weather in Tokyo? or Latest AI news",
                lines=2,
            )
        with gr.Column(scale=1):
            submit_btn = gr.Button("Ask", variant="primary", size="lg")
            clear_btn = gr.Button("Clear", size="lg")

    gr.Examples(
        examples=EXAMPLE_QUERIES,
        inputs=query_input,
        label="Example Queries",
    )

    with gr.Tabs():
        with gr.Tab("Summary"):
            summary_output = gr.Textbox(
                label="AI Summary",
                lines=10,
                interactive=False,
                elem_classes=["result-box"],
            )

        with gr.Tab("News"):
            news_output = gr.HTML(label="News Articles")

        with gr.Tab("Weather"):
            weather_output = gr.HTML(label="Weather Conditions")

        with gr.Tab("Report"):
            report_output = gr.HTML(label="Generated Report")

    with gr.Accordion("System Health", open=False):
        health_output = gr.Textbox(label="Service Status", lines=6, interactive=False)
        health_btn = gr.Button("Check Health")
        health_btn.click(fn=check_health, outputs=health_output)

    submit_btn.click(
        fn=process_query,
        inputs=query_input,
        outputs=[summary_output, news_output, weather_output, report_output],
    )
    query_input.submit(
        fn=process_query,
        inputs=query_input,
        outputs=[summary_output, news_output, weather_output, report_output],
    )
    clear_btn.click(
        fn=lambda: ("", "", "", "", ""),
        outputs=[query_input, summary_output, news_output, weather_output, report_output],
    )


def main():
    logger.info("ui_starting", port=settings.ui_port)
    demo.launch(
        server_name="0.0.0.0",
        server_port=settings.ui_port,
        show_error=True,
        share=False,
    )


if __name__ == "__main__":
    main()
