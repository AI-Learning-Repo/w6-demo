"""A2A 1.0 client for the two local teaching services."""
import asyncio
import json
import urllib.request
from a2a.client import create_client, ClientConfig
from a2a.helpers import new_text_message
from a2a.types import Role, SendMessageRequest, TaskState
from google.protobuf.json_format import MessageToDict

AGENTS = {'burger': 'http://127.0.0.1:11001', 'pizza': 'http://127.0.0.1:11000'}

def discover(url):
    with urllib.request.urlopen(url.rstrip('/') + '/.well-known/agent-card.json', timeout=10) as response:
        card = json.load(response)
    if not any(i.get('protocolVersion') == '1.0' for i in card['supportedInterfaces']):
        raise RuntimeError('No A2A 1.0 interface advertised')
    return card

async def send(url, text, *, show_json=False, timeout=180):
    async def exchange():
        client = await create_client(agent=url, client_config=ClientConfig(streaming=False))
        try:
            request = SendMessageRequest(message=new_text_message(text=text, role=Role.ROLE_USER))
            if show_json:
                print('REQUEST:', json.dumps(MessageToDict(request), indent=2, ensure_ascii=False))
            final = None
            async for chunk in client.send_message(request):
                if show_json:
                    print('RESPONSE:', json.dumps(MessageToDict(chunk), indent=2, ensure_ascii=False))
                if chunk.HasField('task'):
                    final = chunk.task
            if final is None:
                raise RuntimeError('Expected a task response from seller')
            state = TaskState.Name(final.status.state)
            if final.status.state != TaskState.TASK_STATE_COMPLETED:
                raise RuntimeError(f'Task {final.id}: {state}')
            answer = '\n'.join(p.text for a in final.artifacts for p in a.parts if p.text)
            if not answer.strip():
                raise RuntimeError('Completed task has no text artifact')
            return {'task_id': final.id, 'context_id': final.context_id, 'state': state, 'text': answer}
        finally:
            await client.close()
    return await asyncio.wait_for(exchange(), timeout=timeout)
