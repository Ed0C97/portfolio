"""Portfolio excerpt, adapted. FastMCP server entry point.

Run: python -m mcp_server.server
"""

import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="people-os",
    description=(
        "AI-native people-operations tools for hiring, onboarding, "
        "and team management."
    ),
)


# imports sit below the FastMCP instance because each tool module imports `mcp`

from mcp_server.tools.ats import (
    get_jobs,
    get_job_details,
    get_candidates,
    get_candidate_details,
    get_scorecards,
    search_candidates,
)
from mcp_server.tools.resume_parser import parse_resume
from mcp_server.tools.interview_scorer import score_interview
from mcp_server.tools.onboarding import generate_onboarding_plan

mcp.tool()(get_jobs)
mcp.tool()(get_job_details)
mcp.tool()(get_candidates)
mcp.tool()(get_candidate_details)
mcp.tool()(get_scorecards)
mcp.tool()(search_candidates)

mcp.tool()(parse_resume)
mcp.tool()(score_interview)
mcp.tool()(generate_onboarding_plan)


# resource URIs bind path params, e.g. scorecard://eng-123 -> get_job_scorecard_resource(job_id="eng-123")

from mcp_server.resources.job_criteria import get_job_scorecard_resource
from mcp_server.resources.company_context import get_company_context

mcp.resource("scorecard://{job_id}")(get_job_scorecard_resource)
mcp.resource("context://company")(get_company_context)


def main() -> None:
    """Start the MCP server."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting People OS MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
