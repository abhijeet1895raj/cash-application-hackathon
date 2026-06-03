"""
register_agents.py - Create all 5 Cash Application agents in Azure AI Foundry.

Run once to make agents visible in ai.azure.com → your project → Agents.
Agent IDs are saved to agents_registry.json and reused on subsequent runs.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/register_agents.py

Options:
    --delete    Delete all registered agents and exit
    --refresh   Delete existing agents and recreate from current prompts
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Make sure backend/ is on the path so we can import agents/
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from agents.cash_app import (
    AGENT_ORDER,
    AGENT_META,
    AGENT_PROMPTS,
    AGENT_TOOLS,
)

REGISTRY_FILE = Path(__file__).parent.parent / "agents_registry.json"

# Per-agent model assignments
AGENT_MODELS = {
    "BankStatementIntelligenceAgent": os.getenv("MODEL_BANK_AGENT",     "gpt-5.4-mini"),
    "ARLedgerAgent":                  os.getenv("MODEL_AR_AGENT",        "gpt-5.4-mini"),
    "ReconciliationAgent":            os.getenv("MODEL_RECON_AGENT",     "gpt-4o"),
    "MismatchReasoningAgent":         os.getenv("MODEL_REASONING_AGENT", "gpt-5"),
    "CashPostingAgent":               os.getenv("MODEL_POSTING_AGENT",   "gpt-4o"),
}


def build_client() -> AIProjectClient:
    endpoint       = os.getenv("AZURE_AI_ENDPOINT", "")
    subscription   = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "")
    project_name   = os.getenv("AZURE_PROJECT_NAME", "")
    api_key        = os.getenv("AZURE_API_KEY", "")

    if not all([endpoint, subscription, resource_group, project_name]):
        print("ERROR: Missing Azure credentials in .env")
        print("  Required: AZURE_AI_ENDPOINT, AZURE_SUBSCRIPTION_ID,")
        print("            AZURE_RESOURCE_GROUP, AZURE_PROJECT_NAME")
        sys.exit(1)

    credential = AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()
    return AIProjectClient(
        endpoint=endpoint,
        subscription_id=subscription,
        resource_group_name=resource_group,
        project_name=project_name,
        credential=credential,
    )


def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def save_registry(registry: dict):
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


def delete_agents(client: AIProjectClient, registry: dict):
    if not registry:
        print("No registered agents found.")
        return
    for name, agent_id in registry.items():
        try:
            client.agents.delete_agent(agent_id)
            print(f"  Deleted {name} ({agent_id})")
        except Exception as e:
            print(f"  Could not delete {name}: {e}")
    REGISTRY_FILE.unlink(missing_ok=True)
    print("Registry cleared.")


def register_agents(client: AIProjectClient, registry: dict) -> dict:
    # Check which agents already exist in the project by listing
    existing = {}
    try:
        for agent in client.agents.list_agents():
            existing[agent.name] = agent.id
    except Exception as e:
        print(f"Warning: could not list existing agents: {e}")

    updated_registry = {}

    for i, name in enumerate(AGENT_ORDER, 1):
        meta  = AGENT_META[name]
        model = AGENT_MODELS[name]
        tools_obj = AGENT_TOOLS.get(name)

        print(f"\n[{i}/5] {meta['icon']} {meta['label']}")
        print(f"       Model : {model}")
        print(f"       Tools : {tools_obj[0]['type'] if tools_obj else 'none'}")

        # Skip if already registered and not refreshing
        if name in registry and name in existing:
            print(f"       Status: ✓ Already registered (ID: {registry[name]})")
            updated_registry[name] = registry[name]
            continue

        # Delete stale registry entry if agent was removed from project
        if name in registry and name not in existing:
            print(f"       Note  : Previous registration gone from project, recreating...")

        kwargs = dict(
            model=model,
            name=name,
            instructions=AGENT_PROMPTS[name],
            description=f"Cash Application Foundry - {meta['label']}. {meta['desc']}",
        )
        if tools_obj:
            kwargs["tools"] = tools_obj  # plain list of dicts e.g. [{"type":"code_interpreter"}]

        try:
            agent = client.agents.create_agent(**kwargs)
            updated_registry[name] = agent.id
            print(f"       Status: ✓ Created (ID: {agent.id})")
        except Exception as e:
            print(f"       Status: ✗ FAILED - {e}")
            sys.exit(1)

    return updated_registry


def print_summary(registry: dict):
    print("\n" + "─" * 60)
    print("  CASH APPLICATION FOUNDRY - Agents Registered")
    print("─" * 60)
    for i, name in enumerate(AGENT_ORDER, 1):
        meta  = AGENT_META[name]
        model = AGENT_MODELS[name]
        aid   = registry.get(name, "NOT REGISTERED")
        print(f"  {i}. {meta['icon']}  {meta['label']:<28} {model:<14} {aid}")
    print("─" * 60)
    print(f"\n  Registry saved → {REGISTRY_FILE}")
    print("\n  View in portal:")
    project = os.getenv("AZURE_PROJECT_NAME", "your-project")
    print(f"  https://ai.azure.com → {project} → Agents\n")


def main():
    parser = argparse.ArgumentParser(description="Register Cash Application agents in Azure AI Foundry")
    parser.add_argument("--delete",  action="store_true", help="Delete all registered agents")
    parser.add_argument("--refresh", action="store_true", help="Delete and recreate all agents")
    args = parser.parse_args()

    print("\nConnecting to Azure AI Foundry...")
    client = build_client()
    print(f"  Project : {os.getenv('AZURE_PROJECT_NAME')}")
    print(f"  Endpoint: {os.getenv('AZURE_AI_ENDPOINT')}")

    registry = load_registry()

    if args.delete or args.refresh:
        print("\nDeleting existing agents...")
        delete_agents(client, registry)
        registry = {}
        if args.delete:
            return

    print("\nRegistering agents...")
    registry = register_agents(client, registry)
    save_registry(registry)
    print_summary(registry)


if __name__ == "__main__":
    main()
