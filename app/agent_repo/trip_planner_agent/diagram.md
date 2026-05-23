# Trip Planner Agent — Architecture Diagram

```mermaid
graph TD
    User([Customer]) --> triage_orchestrator

    subgraph root["trip_planner_agent — SequentialAgent (root)"]

        subgraph S1["Stage 1 — Triage"]
            triage_orchestrator["triage_orchestrator\nLlmAgent\noutput_key: trip_details"]
        end

        subgraph S2["Stage 2 — research_fan_out · ParallelAgent"]
            destination_researcher["destination_researcher\nLlmAgent + fetch_url (MCP)\noutput_key: destination_research"]
            flight_hotel_scout["flight_hotel_scout\nLlmAgent + google_search\noutput_key: flight_hotel_data"]
            budget_pre_assessor["budget_pre_assessor\nLlmAgent (no tools)\noutput_key: budget_estimate"]
        end

        subgraph S3["Stage 3 — refinement_loop · LoopAgent (max 2)"]
            itinerary_builder["itinerary_builder\nLlmAgent\noutput_key: itinerary"]
            quality_reviewer["quality_reviewer\nLlmAgent\noutput_key: review_decision"]
        end

        subgraph S4["Stage 4 — Conditional Routing"]
            response_router["response_router\nLlmAgent"]
            final_response_agent["final_response_agent\nLlmAgent"]
            human_handoff_agent["human_handoff_agent\nLlmAgent"]
        end

    end

    triage_orchestrator -->|trip_details| destination_researcher
    triage_orchestrator -->|trip_details| flight_hotel_scout
    triage_orchestrator -->|trip_details| budget_pre_assessor

    destination_researcher -->|destination_research| itinerary_builder
    flight_hotel_scout -->|flight_hotel_data| itinerary_builder
    budget_pre_assessor -->|budget_estimate| itinerary_builder

    itinerary_builder -->|itinerary| quality_reviewer
    quality_reviewer -->|NEEDS_REVISION| itinerary_builder

    quality_reviewer --> response_router

    response_router -->|APPROVED| final_response_agent
    response_router -->|NEEDS_HUMAN| human_handoff_agent

    final_response_agent --> Reply([Customer reply])
    human_handoff_agent --> Reply
```

## Session State Bus

| Key                  | Written by               | Read by                                               |
|----------------------|--------------------------|-------------------------------------------------------|
| `trip_details`       | triage_orchestrator      | destination_researcher, flight_hotel_scout, budget_pre_assessor, itinerary_builder, quality_reviewer, response_router, final_response_agent, human_handoff_agent |
| `destination_research` | destination_researcher | itinerary_builder                                    |
| `flight_hotel_data`  | flight_hotel_scout       | itinerary_builder, final_response_agent              |
| `budget_estimate`    | budget_pre_assessor      | itinerary_builder, final_response_agent              |
| `itinerary`          | itinerary_builder        | quality_reviewer, itinerary_builder (self on loop), response_router, final_response_agent |
| `review_decision`    | quality_reviewer         | itinerary_builder, response_router, final_response_agent, human_handoff_agent |
