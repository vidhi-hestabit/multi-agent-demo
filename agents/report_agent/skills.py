"""Report agent skill definitions."""

from common.a2a_types import AgentSkill

SKILLS = [
    AgentSkill(
        id="generate_report",
        name="Generate Report",
        description="Compile data from multiple sources into a structured markdown report.",
        input_modes=["text", "data"],
        output_modes=["text", "data"],
        tags=["report", "document", "aggregation", "summarization"],
        examples=[
            "Generate a report about AI trends",
            "Create a weather and news summary report for London",
            "Write a comprehensive report on climate change news",
        ],
    ),
]
