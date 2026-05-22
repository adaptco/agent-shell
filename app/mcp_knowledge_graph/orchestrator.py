"""
Orchestrator for Knowledge Graph-based Sub-Agent Task Assignment
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import uuid


@dataclass
class SubTaskAssignment:
    """Assignment of a sub-task to a specific sub-agent"""

    task_id: str
    task_description: str
    assigned_subagent: str
    expertise_cluster_id: str
    priority: float
    dependencies: List[str]
    estimated_steps: int
    context_tokens: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SubAgentOrchestrator:
    """Orchestrates sub-agent task assignment based on knowledge graph"""

    # Map expertise clusters to sub-agent roles
    CLUSTER_TO_SUBAGENT = {
        "backend": "BackendAgent",
        "frontend": "FrontendAgent",
        "devops": "DevOpsAgent",
        "data": "DataAgent",
        "ml": "MLAgent",
        "security": "SecurityAgent",
        "testing": "TestingAgent",
        "documentation": "DocumentationAgent",
    }

    # Sub-agent capabilities and estimated effort
    SUBAGENT_EFFORT_MAP = {
        "BackendAgent": {"complexity": 1.5, "parallelize": True},
        "FrontendAgent": {"complexity": 1.2, "parallelize": True},
        "DevOpsAgent": {"complexity": 1.8, "parallelize": False},
        "DataAgent": {"complexity": 2.0, "parallelize": False},
        "MLAgent": {"complexity": 2.5, "parallelize": False},
        "SecurityAgent": {"complexity": 2.2, "parallelize": False},
        "TestingAgent": {"complexity": 1.0, "parallelize": True},
        "DocumentationAgent": {"complexity": 0.8, "parallelize": True},
    }

    def __init__(self):
        self.task_queue: List[SubTaskAssignment] = []
        self.completed_tasks: List[SubTaskAssignment] = []

    def generate_subtasks(self, graph: Dict[str, Any], parent_task: str) -> List[SubTaskAssignment]:
        """
        Generate sub-tasks from knowledge graph clusters.
        Each cluster becomes a focused task for a specialized sub-agent.
        """
        tasks = []
        cluster_priority_map = {}

        # Calculate priority based on cluster size and confidence
        for node in graph.get("nodes", []):
            cluster_id = node["id"]
            # Priority = confidence * log(token_count + 1)
            import math

            priority = node.get("confidence", 0.5) * math.log(node.get("token_count", 1) + 1)
            cluster_priority_map[cluster_id] = priority

        # Generate task for each cluster
        for node in graph.get("nodes", []):
            cluster_id = node["id"]
            cluster_label = node["label"]
            priority = cluster_priority_map[cluster_id]

            # Determine sub-agent from cluster domain
            domain = self._extract_domain_from_cluster(cluster_id, cluster_label)
            subagent = self.CLUSTER_TO_SUBAGENT.get(domain, "GeneralAgent")

            # Get tokens from cluster
            cluster_data = graph["clusters"].get(cluster_id, {})
            tokens = [t["text"] for t in cluster_data.get("tokens", [])[:5]]

            # Generate task description
            task_description = self._generate_task_description(parent_task, cluster_label, domain, tokens)

            # Find dependencies (related clusters)
            dependencies = []
            for edge in graph.get("edges", []):
                if edge["source"] == cluster_id:
                    dependencies.append(edge["target"])

            # Estimate steps
            effort_factor = self.SUBAGENT_EFFORT_MAP.get(subagent, {}).get("complexity", 1.0)
            estimated_steps = max(2, int(len(tokens) * effort_factor))

            task = SubTaskAssignment(
                task_id=f"subtask_{uuid.uuid4().hex[:8]}",
                task_description=task_description,
                assigned_subagent=subagent,
                expertise_cluster_id=cluster_id,
                priority=priority,
                dependencies=dependencies,
                estimated_steps=estimated_steps,
                context_tokens=tokens,
            )

            tasks.append(task)

        # Sort by priority
        tasks.sort(key=lambda t: t.priority, reverse=True)

        return tasks

    def _extract_domain_from_cluster(self, cluster_id: str, cluster_label: str) -> str:
        """Extract domain expertise from cluster ID or label"""
        for domain in self.CLUSTER_TO_SUBAGENT.keys():
            if domain in cluster_id.lower() or domain in cluster_label.lower():
                return domain
        return "backend"  # Default

    def _generate_task_description(self, parent_task: str, cluster_label: str, domain: str, tokens: List[str]) -> str:
        """Generate human-readable task description"""
        token_str = ", ".join(tokens[:3])

        task_templates = {
            "backend": f"Implement {cluster_label} in backend. Key areas: {token_str}. Parent task: {parent_task}",
            "frontend": f"Build UI for {cluster_label}. Key components: {token_str}. Parent task: {parent_task}",
            "devops": f"Configure {cluster_label} infrastructure. Components: {token_str}. Parent task: {parent_task}",
            "data": f"Create {cluster_label} data pipeline. Entities: {token_str}. Parent task: {parent_task}",
            "ml": f"Develop {cluster_label} ML model. Features: {token_str}. Parent task: {parent_task}",
            "security": f"Implement {cluster_label} security. Controls: {token_str}. Parent task: {parent_task}",
            "testing": f"Develop tests for {cluster_label}. Coverage: {token_str}. Parent task: {parent_task}",
            "documentation": f"Document {cluster_label}. Topics: {token_str}. Parent task: {parent_task}",
        }

        return task_templates.get(domain, f"Implement {cluster_label}. Context: {token_str}")

    def assign_task_order(self, tasks: List[SubTaskAssignment]) -> List[SubTaskAssignment]:
        """
        Determine execution order based on dependencies and parallelization capability.
        Returns ordered task list.
        """
        ordered = []
        assigned = set()

        while len(ordered) < len(tasks):
            # Find tasks with no unmet dependencies
            ready_tasks = [
                t
                for t in tasks
                if t.task_id not in assigned
                and all(dep in assigned or dep not in [x.task_id for x in tasks] for dep in t.dependencies)
            ]

            if not ready_tasks:
                # Circular dependency or all remaining - just add next
                ready_tasks = [t for t in tasks if t.task_id not in assigned][:1]

            if ready_tasks:
                task = max(ready_tasks, key=lambda t: t.priority)  # Pick highest priority
                ordered.append(task)
                assigned.add(task.task_id)

        return ordered

    def create_delegation_contract(self, task: SubTaskAssignment, parent_task_id: str) -> Dict[str, Any]:
        """Create a delegation contract for sub-agent handoff"""
        return {
            "handoff_id": f"hoff_{uuid.uuid4().hex[:8]}",
            "parent_task_id": parent_task_id,
            "subagent_name": task.assigned_subagent,
            "subtask": task.task_description,
            "expertise_cluster": task.expertise_cluster_id,
            "priority": task.priority,
            "estimated_steps": task.estimated_steps,
            "context_tokens": task.context_tokens,
            "dependencies": task.dependencies,
            "return_contract": {"expects": "delegate_result", "max_steps": task.estimated_steps + 2},
        }
