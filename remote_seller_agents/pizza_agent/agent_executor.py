
import asyncio
import inspect
import logging

from agent import PizzaSellerAgent

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_part,
)

from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContext,
)

from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState


logger = logging.getLogger(__name__)


class PizzaAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = PizzaSellerAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        # 1. Extract the incoming message
        message = context.message

        if message is None:
            raise ValueError("Missing user message")

        query = get_message_text(message)

        # 2. Create or retrieve the A2A task
        task = (
            context.current_task
            or new_task_from_user_message(message)
        )

        await event_queue.enqueue_event(task)

        # 3. Create a task updater
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING
        )

        try:

            if not query.strip():
                raise ValueError("Empty text request")

            # 4. Execute the underlying agent safely
            if inspect.iscoroutinefunction(self.agent.invoke):
                result = await self.agent.invoke(
                    query,
                    task.context_id,
                )
            else:
                result = await asyncio.to_thread(
                    self.agent.invoke,
                    query,
                    task.context_id,
                )

            # 5. Publish the agent response
            await updater.add_artifact(
                parts=[
                    new_text_part(
                        text=str(result),
                        media_type="text/plain",
                    )
                ],
                name="pizza_response",
            )

            # 6. Mark task as completed
            await updater.complete()

        except Exception:

            logger.exception("Pizza agent execution failed")

            await updater.add_artifact(
                parts=[
                    new_text_part(
                        text="Seller execution failed. "
                             "Check the server logs.",
                        media_type="text/plain",
                    )
                ],
                name="error",
            )

            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        raise NotImplementedError(
            "Task cancellation is not supported."
        )
