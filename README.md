# ProgearHiking Demo

AI Agent demo showcasing hybrid Okta + Auth0 architecture for AI governance.

## Architecture

- **Okta**: Enterprise IdP with Workload Principals (WLP), ID-JAG issuance, XAA policies
- **Auth0**: Token Vault for external service access (Salesforce)
- **Azure AI Foundry**: Agent runtime
- **Vercel**: Frontend hosting
- **Render**: Backend hosting

## Structure

```
├── frontend/     # Next.js app with Okta authentication
├── backend/      # FastAPI with Token Vault integration
└── README.md
```

## Key Concept

> "Your agents can live anywhere. Okta secures them everywhere."

Okta provides governance for AI agents regardless of where they run (Azure Foundry, AWS Bedrock, Google Vertex). Auth0 Token Vault bridges access to external services that don't yet support XAA natively.
