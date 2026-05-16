"""Standard capability definitions and registry for platform capabilities."""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CapabilityDefinition:
    """Definition of a standard platform capability."""
    id: str
    label: str
    description: str
    category: str  # 'state', 'auth', 'payment', 'integration', 'custom'
    icon: str = ""
    requires_params: bool = False
    param_schema: List[Dict[str, Any]] = None
    ui_hints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.param_schema is None:
            self.param_schema = []
        if self.ui_hints is None:
            self.ui_hints = {}


# Standard capability definitions
STANDARD_CAPABILITIES: Dict[str, CapabilityDefinition] = {
    "query_state": CapabilityDefinition(
        id="query_state",
        label="Query Account Status/Quota",
        description="Query account status and quota information",
        category="state",
        icon="refresh",
        ui_hints={"inline": True, "priority": 1}
    ),
    
    "refresh_token": CapabilityDefinition(
        id="refresh_token",
        label="Refresh Token",
        description="Refresh authentication token",
        category="auth", 
        icon="key",
        ui_hints={"inline": True, "priority": 2}
    ),
    
    "generate_link": CapabilityDefinition(
        id="generate_link",
        label="Generate Trial/Payment Link",
        description="Generate payment or trial link",
        category="payment",
        icon="link",
        requires_params=True,
        param_schema=[
            {"key": "plan", "label": "Plan", "type": "select", "options": ["plus", "team"]},
            {"key": "country", "label": "Country", "type": "select", "options": ["US", "SG", "TR", "HK", "JP", "GB", "AU", "CA"]},
        ],
        ui_hints={"inline": True, "priority": 3}
    ),
    
    "generate_link_browser": CapabilityDefinition(
        id="generate_link_browser",
        label="Generate Trial/Payment Link (Browser)",
        description="Generate payment or trial link using browser automation",
        category="payment",
        icon="globe",
        requires_params=True,
        param_schema=[
            {"key": "timeout", "label": "Wait Seconds (default 180)", "type": "number"},
            {"key": "headless", "label": "Headless Mode", "type": "select", "options": ["false", "true"]},
        ],
        ui_hints={"inline": False, "priority": 4}
    ),
    
    "switch_desktop": CapabilityDefinition(
        id="switch_desktop",
        label="Switch to Desktop App",
        description="Switch to desktop application",
        category="auth",
        icon="monitor",
        ui_hints={"inline": True, "priority": 5}
    ),
    
    "upload_cpa": CapabilityDefinition(
        id="upload_cpa",
        label="Upload to CPA",
        description="Upload account to CPA system",
        category="integration",
        icon="upload",
        requires_params=True,
        param_schema=[
            {"key": "api_url", "label": "CPA API URL", "type": "text"},
            {"key": "api_key", "label": "CPA API Key", "type": "text"},
        ],
        ui_hints={"inline": False, "priority": 6}
    ),
    
    "upload_tm": CapabilityDefinition(
        id="upload_tm",
        label="Upload to Team Manager",
        description="Upload account to Team Manager",
        category="integration",
        icon="users",
        requires_params=True,
        param_schema=[
            {"key": "api_url", "label": "TM API URL", "type": "text"},
            {"key": "api_key", "label": "TM API Key", "type": "text"},
        ],
        ui_hints={"inline": False, "priority": 7}
    ),
    
    "check_trial": CapabilityDefinition(
        id="check_trial",
        label="Check Trial Eligibility",
        description="Check trial eligibility",
        category="payment",
        icon="check-circle",
        ui_hints={"inline": True, "priority": 8}
    ),
    
    "create_api_key": CapabilityDefinition(
        id="create_api_key",
        label="Create API Key",
        description="Create API key",
        category="auth",
        icon="key",
        requires_params=True,
        param_schema=[
            {"key": "name", "label": "Key Name", "type": "text"},
        ],
        ui_hints={"inline": False, "priority": 9}
    ),
}


class CapabilityRegistry:
    """Registry for managing platform capabilities."""
    
    @staticmethod
    def get_definition(capability_id: str) -> CapabilityDefinition:
        """Get capability definition by ID."""
        return STANDARD_CAPABILITIES.get(capability_id)
    
    @staticmethod
    def get_all_definitions() -> Dict[str, CapabilityDefinition]:
        """Get all standard capability definitions."""
        return STANDARD_CAPABILITIES.copy()
    
    @staticmethod
    def get_inline_capabilities(capability_ids: List[str]) -> List[CapabilityDefinition]:
        """Get capabilities that should be shown as inline buttons."""
        return [
            STANDARD_CAPABILITIES[cid] 
            for cid in capability_ids 
            if cid in STANDARD_CAPABILITIES and STANDARD_CAPABILITIES[cid].ui_hints.get("inline", False)
        ]
    
    @staticmethod
    def get_menu_capabilities(capability_ids: List[str]) -> List[CapabilityDefinition]:
        """Get capabilities that should be shown in dropdown menu."""
        return [
            STANDARD_CAPABILITIES[cid]
            for cid in capability_ids
            if cid in STANDARD_CAPABILITIES and not STANDARD_CAPABILITIES[cid].ui_hints.get("inline", False)
        ]
    
    @staticmethod
    def sort_by_priority(capabilities: List[CapabilityDefinition]) -> List[CapabilityDefinition]:
        """Sort capabilities by UI priority."""
        return sorted(
            capabilities, 
            key=lambda c: c.ui_hints.get("priority", 999)
        )
