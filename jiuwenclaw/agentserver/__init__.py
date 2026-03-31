# Copyright (c) Huawei Technologies Co., Ltd. 2025. All rights reserved.

"""AgentServer 模块（懒加载导出，避免导入轻量子模块时触发重依赖）."""

__all__ = ["JiuWenClaw", "SkillManager"]


def __getattr__(name: str):
    if name == "JiuWenClaw":
        from jiuwenclaw.agentserver.interface import JiuWenClaw as _JiuWenClaw
        return _JiuWenClaw
    if name == "SkillManager":
        from jiuwenclaw.agentserver.skill_manager import SkillManager as _SkillManager
        return _SkillManager
    raise AttributeError(name)
