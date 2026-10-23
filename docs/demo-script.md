# ReturnRight AI — 60-second concept walkthrough

Read this aloud while recording the running demo. It is about 160 words, roughly 60–70 seconds at a natural pace. Stay inside 45–75 seconds.

A longer click-by-click script is in [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Use this shorter narration for the Devpost video.

## Narration

Return policies are scattered, deadlines are easy to miss, and shoppers often cannot tell whether a purchase can still be returned.

ReturnRight AI is a resolution agent for that problem. The intended experience is a conversation that checks a policy, prepares a claim, and tracks the follow-up. What is running today is a guided demo on synthetic orders. It does not contact a merchant, submit a return, or issue a refund.

I connect to the project’s MCP server, search for kettle, and open sample order NW-1001. I mark it unwanted. The policy check cites a stored sample rule and returns return eligible. I create a case, prepare the draft, and confirm. The case stays labeled demo only, and a follow-up appears beside it.

Order search, policy checks, case tracking, and the Python MCP server are implemented. A free-form conversation, real merchant submission, and a live Alexa+ integration are still planned.

## What to show while you speak

1. Hold on the yellow **DEMO MODE** banner and the ReturnRight AI title.
2. Click **Connect MCP**. Leave the tool log visible.
3. Search `kettle`, then open **NW-1001** (Ceramic Pour-Over Kettle, Northwind Market).
4. Leave issue type on `unwanted`, type `Unused gift`, and click **evaluate_policy**.
5. Click **create_case**, then **prepare_resolution_action**, then **I confirm — confirm_resolution_action**.
6. Point to the case status, the follow-up, and the `demo_only` tool-log line.
7. Stop on that screen. Do not say the demo filed a real return.
