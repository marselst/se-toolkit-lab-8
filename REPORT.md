# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

### Question: "What is the agentic loop?"

**Answer:**
The agentic loop is the core iterative process that AI agents use to accomplish tasks. It typically follows this cycle:

1. **Perceive/Observation** — The agent gathers information about its environment, current state, or task context (e.g., reading files, checking outputs, receiving user input)
2. **Think/Reasoning** — The agent processes the information, plans next steps, and decides what action to take (e.g., "I need to read this file first," or "I should search for more information")
3. **Act/Action** — The agent executes an action using available tools (e.g., calling APIs, running commands, writing files, sending messages)
4. **Repeat** — The agent observes the results of its action and continues the loop until the goal is achieved

This loop enables agents to work autonomously toward complex goals, adapt based on feedback from actions, break down multi-step tasks, and self-correct when things don't go as planned.

### Question: "What labs are available in our LMS?"

**Answer:**
The agent without MCP tools cannot directly query the LMS backend. It can only read from its workspace files. When asked this question, it found information about Lab 8 by reading the task files in the repository, but it doesn't have access to real-time LMS data.

## Task 1B — Agent with LMS tools

### Question: "What labs are available?"

**Answer:**
Available Labs in the LMS:

| # | Lab Title |
|---|-----------|
| Lab 01 | Products, Architecture & Roles |
| Lab 02 | Run, Fix, and Deploy a Backend Service |
| Lab 03 | Backend API: Explore, Debug, Implement, Deploy |
| Lab 04 | Testing, Front-end, and AI Agents |
| Lab 05 | Data Pipeline and Analytics Dashboard |
| Lab 06 | Build Your Own Agent |
| Lab 07 | Build a Client with an AI Coding Agent |
| Lab 08 | lab-08 (The Agent is the Interface — current lab) |

The agent is now using MCP tools to query the real LMS backend.

### Question: "Describe the architecture of the LMS system"

**Answer:**
The LMS system architecture consists of:

**High-Level Components:**
- **Caddy Reverse Proxy** (Port 42002) - Single entry point routing to all services
- **FastAPI Backend** (Port 42001) - REST API with Swagger UI
- **PostgreSQL Database** (Port 42004) - Relational database for items, learners, interactions
- **pgAdmin** (Port 42003) - Web-based database management
- **Nanobot AI Agent** (Ports 8765 WS, 18790 HTTP) - AI agent with MCP tools
- **Qwen Code API** (Port 8080) - LLM API gateway
- **VictoriaLogs** - Log storage (7-day retention)
- **VictoriaTraces** - Distributed trace storage
- **OTel Collector** - Collects and forwards logs/traces

**Data Model (OBER-Based):**
- Item hierarchy: Course → Lab → Task → Step
- Learners table with interactions tracking

**Key Design Decisions:**
- Monolithic architecture for easy deployment
- Caddy for single-origin setup (no CORS issues)
- SQLModel combining SQLAlchemy + Pydantic
- Async database operations
- Feature flags for endpoint availability

## Task 1C — Skill prompt

### Question: "Show me the scores" (without specifying a lab)

**Answer:**
The agent with the skill prompt now:
1. Automatically fetched pass rates for ALL labs
2. Presented a summary table with Lab, Avg Score, Tasks, and Total Attempts
3. Provided detailed breakdown for each lab showing individual task scores
4. Highlighted key insights:
   - Highest scoring task: Lab 01 - Lab setup (84.2%)
   - Lowest scoring task: Lab 02 - Make your VM a proxy (0.0%)
   - Most attempted task: Lab 01 - Lab setup (2,937 attempts)
   - Best performing lab: Lab 05 & Lab 07 (67.3% avg)
   - Most challenging lab: Lab 02 (48.3% avg)

The skill prompt taught the agent to:
- Format percentages nicely (e.g., "51.4%" instead of decimals)
- Format counts with commas for thousands
- Use tables for comparing multiple items
- Highlight important findings
- Keep responses concise but informative

**Skill prompt location:** `nanobot/workspace/skills/lms/SKILL.md`

## Task 2A — Deployed agent

**Nanobot startup log excerpt:**

```
nanobot-1  | Using config: /app/nanobot/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-03-27 09:56:48.892 | INFO     | nanobot.channels.manager:_init_channels:54 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | 2026-03-27 09:56:49.397 | INFO     | nanobot_webchat.channel:start:72 - WebChat starting on 0.0.0.0:8765
nanobot-1  | 2026-03-27 09:56:51.579 | INFO     | nanobot.agent.tools.mcp:connect_mcp_servers:182 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-03-27 09:56:51.579 | INFO     | nanobot.agent.loop:run:260 - Agent loop started
```

The nanobot gateway is running as a Docker service with:
- WebChat channel enabled on port 8765
- MCP server connected with 9 LMS tools registered
- Agent loop running

## Task 2B — Web client

**WebSocket endpoint test:**

The WebSocket endpoint at `ws://localhost:42002/ws/chat?access_key=nano1` is working. Agent response to "What labs are available?":

```
Here are the available labs:

| ID | Title |
|----|-------|
| 1 | Lab 01 – Products, Architecture & Roles |
| 2 | Lab 02 – Run, Fix, and Deploy a Backend Service |
| 3 | Lab 03 – Backend API: Explore, Debug, Implement, Deploy |
| 4 | Lab 04 – Testing, Front-end, and AI Agents |
| 5 | Lab 05 – Data Pipeline and Analytics Dashboard |
| 6 | Lab 06 – Build Your Own Agent |
| 7 | Lab 07 – Build a Client with an AI Coding Agent |
| 8 | Lab 08 – The Agent is the Interface (current lab) |
```

**Flutter web client:**

The Flutter web client is accessible at `http://localhost:42002/flutter/`. The login screen accepts the `NANOBOT_ACCESS_KEY` (nano1) for authentication.

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
