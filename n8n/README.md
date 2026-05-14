# n8n Automation Layer

Create an n8n workflow with a webhook named `aeaios`. The Django automation app can call it for email, Slack, CRM, ticketing, or approval follow-up actions.

Suggested workflow:

1. Webhook trigger receives `workflow_id`, `channel`, and `payload`.
2. Switch node routes to Email, Slack, CRM, or HTTP integration.
3. Approval node pauses high-impact actions.
4. Respond node sends execution status back to Django.
