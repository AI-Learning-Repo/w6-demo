
import argparse
import os
import logging

import uvicorn

from starlette.applications import Starlette

from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentInterface,
    AgentSkill,
)

from a2a.server.request_handlers import (
    DefaultRequestHandler,
)

from a2a.server.tasks import InMemoryTaskStore

from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)

from agent_executor import PizzaAgentExecutor


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--host",
        default="127.0.0.1"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=11000
    )

    args = parser.parse_args()

    public_url = os.getenv(
        "HOST_OVERRIDE",
        f"http://{args.host}:{args.port}/"
    )

    # 1. Advertise the agent's skill
    skill = AgentSkill(
        id="create_pizza_order",
        name="Pizza Order Creation Tool",
        description=(
            "Provides pizza menu information, "
            "prices and simulated pizza orders."
        ),
        tags=["pizza", "food", "ordering"],
        examples=[
            "What is the price of a Margherita Pizza?",
            "I want to order two Margherita Pizzas.",
        ],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    )

    # 2. Define the A2A v1 Agent Card
    agent_card = AgentCard(
        name="pizza_seller_agent",
        description=(
            "Helps with pizza menu information "
            "and simulated orders."
        ),
        version="2.0.0",

        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=public_url,
            )
        ],

        capabilities=AgentCapabilities(
            streaming=False
        ),

        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],

        skills=[skill],
    )

    # 3. Connect the executor to A2A
    request_handler = DefaultRequestHandler(
        agent_executor=PizzaAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    # 4. Create HTTP routes
    routes = []

    routes.extend(
        create_agent_card_routes(agent_card)
    )

    routes.extend(
        create_jsonrpc_routes(
            request_handler,
            "/"
        )
    )

    # 5. Create the ASGI application
    app = Starlette(routes=routes)

    # 6. Start the HTTP server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port
    )


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    main()
