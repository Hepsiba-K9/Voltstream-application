# Week 6 - Advanced RAG + Vector Database + Agent Evaluation

## Checkpoint Summary

Task: Integrate the RAG pipeline as a tool in the ADK Advisor Agent, ask 3 questions that show document-grounded answers, and present an evaluation report with 10 Q&A pairs scored for faithfulness and relevance.

Status: Completed.

## Implementation Evidence

| Requirement | Project implementation |
| --- | --- |
| RAG pipeline | `backend/ai_services/document_loader.py`, `text_chunker.py`, `embedding_service.py`, and `document_qa_service.py` |
| Vector database | ChromaDB persistent store at `backend/databases/chroma_store` |
| Indexed documents | All supported `.txt` and `.pdf` files in `backend/data` are loaded by `existing_reference_documents()` |
| Existing PDF Q&A workflow reused | `document_qa_service.py` is shared by `/api/v1/qa` and Advisor Agent retrieval |
| Advisor Agent tool | `retrieve_advisor_rag_context(question)` in `backend/agents/advisor_agent.py` |
| ADK Advisor integration | `build_advisor_agent()` registers `retrieve_advisor_rag_context` as a tool |
| Energy workflow integration | `generate_recommendations()` calls the RAG tool before returning advice |

## Indexed Document Set

The RAG loader indexes these reference documents from `backend/data`:

1. `energy_efficiency_guide.txt`
2. `energy_efficiency_report.txt`
3. `detailed_energy_efficiency_report.txt`
4. `EEEMHandbook_finalENG-encrypted.txt`
5. `IEA_EnergyEfficiencyIndicatorsFundamentalsonStatistics.txt`

The current document status reported by the app is 825 chunks across the indexed documents.

## Demo Questions

These 3 questions can be used in the demo to prove the Advisor/RAG answers are grounded in documents:

| # | Question | Expected grounding |
| --- | --- | --- |
| 1 | What low-cost actions can reduce home energy use quickly? | Uses the guide content about cooling/heating load, LED lighting, air sealing, filters, standby loads, and scheduling. |
| 2 | What can high grid draw during bright midday hours indicate? | Uses the guide content about appliances running outside solar availability, shading, or inverter limits. |
| 3 | Why are energy efficiency indicators useful? | Uses the IEA energy efficiency indicators document about tracking sector energy use and policy questions. |

## Evaluation Method

Faithfulness score:
- 1.0 means the answer is fully supported by retrieved document content.
- 0.5 means the answer is partly supported but needs more document context.
- 0.0 means the answer is not supported by the documents.

Relevance score:
- 1.0 means the answer directly addresses the question.
- 0.5 means the answer is related but incomplete.
- 0.0 means the answer is off-topic.

Pass rule: A pair passes when faithfulness is at least 0.7 and relevance is at least 0.7.

## 10 Q&A Evaluation Report

| # | Question | Grounded answer | Main source | Faithfulness | Relevance | Result |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | What is energy efficiency? | Energy efficiency means delivering the same service or useful output while using less energy input. It focuses on reducing wasted energy without reducing the needed service. | `EEEMHandbook_finalENG-encrypted.txt`, `IEA_EnergyEfficiencyIndicatorsFundamentalsonStatistics.txt` | 1.0 | 1.0 | Pass |
| 2 | How is energy efficiency different from energy conservation? | Energy efficiency improves the way energy is used, such as using efficient equipment for the same service. Energy conservation reduces or avoids energy use, often by changing behavior or reducing demand. | `EEEMHandbook_finalENG-encrypted.txt`, `energy_efficiency_report.txt` | 0.9 | 1.0 | Pass |
| 3 | What low-cost actions can reduce home energy use quickly? | Fast low-cost savings usually come from reducing cooling and heating load, using LED lighting, sealing air leaks, cleaning air filters, and switching off standby loads with smart plugs or schedules. | `energy_efficiency_guide.txt` | 1.0 | 1.0 | Pass |
| 4 | Why should high-power appliances run during solar production hours? | Running high-power appliances when solar generation is available can reduce grid draw and use more on-site solar energy instead of imported electricity. | `energy_efficiency_guide.txt`, `detailed_energy_efficiency_report.txt` | 1.0 | 1.0 | Pass |
| 5 | What can high grid draw during bright midday hours indicate? | High grid draw during bright midday periods can mean appliances are running outside solar availability, panels are shaded, or the inverter is limiting output. | `energy_efficiency_guide.txt` | 1.0 | 1.0 | Pass |
| 6 | What can a sudden increase in night usage indicate? | A sudden increase in night usage often points to standby loads, water heating, or inefficient cooling running when solar production is unavailable. | `energy_efficiency_guide.txt` | 1.0 | 1.0 | Pass |
| 7 | What does an energy audit usually identify? | An energy audit identifies where energy is consumed, where losses occur, and which energy conservation opportunities can reduce waste or operating cost. | `EEEMHandbook_finalENG-encrypted.txt` | 0.9 | 1.0 | Pass |
| 8 | Why are energy efficiency indicators useful? | Energy efficiency indicators help compare energy use by sector, activity, and end use so changes in consumption can be tracked and explained. | `IEA_EnergyEfficiencyIndicatorsFundamentalsonStatistics.txt` | 1.0 | 1.0 | Pass |
| 9 | What barriers can limit energy efficiency improvements? | Barriers can include lack of information, limited capital, weak incentives, missing data, and difficulty identifying or implementing efficiency opportunities. | `energy_efficiency_report.txt`, `EEEMHandbook_finalENG-encrypted.txt` | 0.8 | 0.9 | Pass |
| 10 | How can batteries help reduce evening peak grid usage? | Batteries can store available solar energy and discharge later during evening peak periods, reducing grid imports when household demand is high. | `detailed_energy_efficiency_report.txt`, `energy_efficiency_guide.txt` | 0.9 | 1.0 | Pass |

Passed pairs: 10/10

Final result: Week 6 evaluation passes because at least 7/10 pairs meet the faithfulness and relevance threshold.

## Advisor Agent Workflow

1. User asks an energy question in Volt Agent.
2. Orchestrator classifies the request as an energy question.
3. Analyst Agent reads database-backed usage, billing, solar, and device data.
4. Advisor Agent calls `retrieve_advisor_rag_context()` to fetch document chunks from ChromaDB.
5. Advisor Agent combines database analysis with retrieved document context.
6. Orchestrator returns the final answer to the UI.

## Notes

- Runtime answers still come from database usage data plus retrieved document context.
- The document loader was not duplicated. The same loader used by the PDF Q&A bot now covers the additional two documents in `backend/data`.
- The Advisor tool does not hardcode final answers. It retrieves chunks through the shared RAG service.
