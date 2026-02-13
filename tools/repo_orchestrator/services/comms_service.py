import uuid
from datetime import datetime
from typing import List, Dict
from tools.repo_orchestrator.models import AgentMessage

class CommsService:
    _messages: Dict[str, List[AgentMessage]] = {}

    @classmethod
    def send_message(cls, agent_id: str, from_role: str, msg_type: str, content: str) -> AgentMessage:
        if agent_id not in cls._messages:
            cls._messages[agent_id] = []
        
        message = AgentMessage(
            id=str(uuid.uuid4()),
            from_role=from_role,
            agentId=agent_id,
            type=msg_type,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        
        cls._messages[agent_id].append(message)
        return message

    @classmethod
    def get_messages(cls, agent_id: str) -> List[AgentMessage]:
        return cls._messages.get(agent_id, [])

    @classmethod
    def clear_messages(cls, agent_id: str):
        if agent_id in cls._messages:
            cls._messages[agent_id] = []
