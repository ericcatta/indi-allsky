from dataclasses import dataclass
import subprocess
from typing import Any


@dataclass(frozen=True)
class ModernAdminTaskEnqueueResult:
    task: Any
    task_id: Any
    queue: Any
    state: Any
    priority: Any
    jobdata: dict[str, Any]


class ModernAdminTaskEnqueueEffectAdapter:
    """Hybrid compatibility adapter for existing task queue effects.

    The adapter owns the boundary from a Hybrid command plan to the existing
    task queue row. The injected model/session/enums remain the low-level
    Flask/Classic persistence adapter.
    """

    def __init__(self, task_model, db_session, queue_enum, state_enum):
        self.task_model = task_model
        self.db_session = db_session
        self.queue_enum = queue_enum
        self.state_enum = state_enum


    def enqueue_from_plan(self, plan_details):
        return self.enqueue(
            queue=plan_details['queue'],
            state=plan_details['state'],
            priority=plan_details['priority'],
            jobdata=plan_details['jobdata'],
        )


    def enqueue(self, queue, state, priority, jobdata):
        queue_value = self.resolve_enum_value(self.queue_enum, queue)
        state_value = self.resolve_enum_value(self.state_enum, state)

        task = self.task_model(
            queue=queue_value,
            state=state_value,
            priority=priority,
            data=jobdata,
        )

        self.db_session.add(task)
        self.db_session.commit()

        return ModernAdminTaskEnqueueResult(
            task=task,
            task_id=getattr(task, 'id', None),
            queue=queue_value,
            state=state_value,
            priority=priority,
            jobdata=jobdata,
        )


    def resolve_enum_value(self, enum_cls, value):
        if isinstance(value, str):
            return enum_cls[value]

        return value


class ModernAdminServiceControlEffectAdapter:
    """Hybrid compatibility adapter for existing user service controls."""

    def __init__(self, service_name, subprocess_run=None, timeout=20):
        self.service_name = service_name
        self.subprocess_run = subprocess_run or subprocess.run
        self.timeout = timeout


    def execute(self, command):
        try:
            result = self.subprocess_run(
                ['systemctl', '--user', command, self.service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError()

        return {
            'returncode' : result.returncode,
            'output'     : (result.stdout or '').strip(),
        }


class ModernAdminSystemPowerEffectAdapter:
    """Hybrid compatibility adapter for existing system power effects."""

    def __init__(self, reboot_effect):
        self.reboot_effect = reboot_effect


    def execute(self, command):
        if command == 'reboot':
            return self.reboot_effect()

        raise ValueError('Unhandled system power command')
