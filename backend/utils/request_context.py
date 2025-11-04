import contextvars
from typing import Optional, Dict, Any
from pydantic import BaseModel


class RewriteContext(BaseModel):
    rewrite_intent: str = ""
    current_workflow: str = ""
    node_infos: Optional[Dict[str, Any]] = None
    rewrite_expert: Optional[str] = ""


# Define context variables
_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('session_id', default=None)
_workflow_checkpoint_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar('workflow_checkpoint_id',
                                                                                        default=None)
_config: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar('config', default=None)
_rewrite_context: contextvars.ContextVar[Optional[RewriteContext]] = contextvars.ContextVar('rewrite_context',
                                                                                            default=None)


def set_session_id(session_id: str) -> None:
    _session_id.set(session_id)


def get_session_id() -> Optional[str]:
    return _session_id.get()


def set_workflow_checkpoint_id(checkpoint_id: Optional[int]) -> None:
    _workflow_checkpoint_id.set(checkpoint_id)


def get_workflow_checkpoint_id() -> Optional[int]:
    return _workflow_checkpoint_id.get()


def set_config(config: Dict[str, Any]) -> None:
    _config.set(config)


def get_config() -> Optional[Dict[str, Any]]:
    return _config.get()


def set_request_context(session_id: str, workflow_checkpoint_id: Optional[int] = None,
                        config: Optional[Dict[str, Any]] = None) -> None:
    set_session_id(session_id)
    if workflow_checkpoint_id is not None:
        set_workflow_checkpoint_id(workflow_checkpoint_id)
    if config is not None:
        set_config(config)


def clear_request_context() -> None:
    _session_id.set(None)
    _workflow_checkpoint_id.set(None)
    _config.set(None)


def set_rewrite_context(rewrite_context: RewriteContext) -> None:
    _rewrite_context.set(rewrite_context)


def get_rewrite_context() -> RewriteContext:
    context = _rewrite_context.get()
    if context is None:
        # 初始化一个新的 RewriteContext
        context = RewriteContext()
        _rewrite_context.set(context)
    return context
