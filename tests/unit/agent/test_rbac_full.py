"""
Tests for Phase 3: Full RBAC (ObjectType-level permissions)

Coverage:
- ObjectTypePermission model
- Team model and hierarchy
- InstancePermission model
- PermissionResolver (unified resolution)
- RBAC Actions

Schema Version: 4.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import directly from modules to avoid agent/__init__.py import issues
from lib.oda.agent.object_permissions import (
    ObjectTypePermission,
    FieldPermission,
    PermissionGrant,
    PermissionType,
    FieldAccessLevel,
    ObjectTypePermissionRegistry,
)
from lib.oda.agent.teams import (
    Team,
    TeamMembership,
    TeamMembershipType,
    TeamStatus,
    TeamRegistry,
)
from lib.oda.agent.instance_permissions import (
    InstancePermission,
    InstancePermissionRegistry,
)
from lib.oda.agent.permission_resolver import (
    PermissionResolver,
    ResolvedPermission,
    PermissionSource,
    PermissionContext,
)
from lib.oda.agent.permissions import (
    PermissionManager,
    AgentIdentity,
    PermissionLevel,
    RoleType,
)
from lib.oda.ontology.ontology_types import utc_now


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def object_permission_registry():
    """Fresh ObjectTypePermissionRegistry for each test."""
    registry = ObjectTypePermissionRegistry()
    return registry


@pytest.fixture
def team_registry():
    """Fresh TeamRegistry for each test."""
    registry = TeamRegistry()
    return registry


@pytest.fixture
def instance_permission_registry():
    """Fresh InstancePermissionRegistry for each test."""
    registry = InstancePermissionRegistry()
    return registry


@pytest.fixture
def permission_manager():
    """Fresh PermissionManager for each test."""
    return PermissionManager(load_defaults=True)


@pytest.fixture
def resolver(permission_manager, object_permission_registry, instance_permission_registry, team_registry):
    """PermissionResolver with all registries."""
    return PermissionResolver(
        permission_manager=permission_manager,
        object_permission_registry=object_permission_registry,
        instance_permission_registry=instance_permission_registry,
        team_registry=team_registry,
    )


# =============================================================================
# OBJECT TYPE PERMISSION TESTS
# =============================================================================


class TestObjectTypePermission:
    """Tests for ObjectTypePermission model."""

    def test_create_basic_permission(self):
        """Test creating a basic ObjectTypePermission."""
        perm = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            can_read=True,
            can_create=True,
            can_update=True,
            can_delete=False,
        )

        assert perm.object_type == "Task"
        assert perm.role_id == "developer"
        assert perm.can_read is True
        assert perm.can_create is True
        assert perm.can_update is True
        assert perm.can_delete is False
        assert perm.can_link is False
        assert perm.id is not None

    def test_permission_with_field_restrictions(self):
        """Test ObjectTypePermission with field-level restrictions."""
        perm = ObjectTypePermission(
            object_type="Document",
            role_id="viewer",
            can_read=True,
            field_restrictions={
                "secret_content": FieldPermission(
                    readable=False,
                    access_level=FieldAccessLevel.HIDDEN,
                ),
                "budget": FieldPermission(
                    readable=True,
                    access_level=FieldAccessLevel.MASKED,
                    mask_pattern="$****",
                ),
            },
        )

        assert perm.can_access_field("title", "read") is True
        assert perm.can_access_field("secret_content", "read") is False
        assert perm.get_field_access_level("budget") == FieldAccessLevel.MASKED
        assert perm.get_field_access_level("title") == FieldAccessLevel.FULL

    def test_permission_expiration(self):
        """Test permission expiration check."""
        # Non-expiring permission
        perm1 = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
        )
        assert perm1.is_expired() is False

        # Expired permission
        perm2 = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            expires_at=utc_now() - timedelta(hours=1),
        )
        assert perm2.is_expired() is True

        # Future expiration
        perm3 = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            expires_at=utc_now() + timedelta(hours=1),
        )
        assert perm3.is_expired() is False

    def test_mask_object_fields(self):
        """Test field masking on objects."""
        perm = ObjectTypePermission(
            object_type="User",
            role_id="viewer",
            can_read=True,
            field_restrictions={
                "ssn": FieldPermission(
                    access_level=FieldAccessLevel.HIDDEN,
                ),
                "email": FieldPermission(
                    access_level=FieldAccessLevel.MASKED,
                    mask_pattern="***@***",
                ),
            },
        )

        obj = {
            "id": "user-1",
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com",
        }

        masked = perm.mask_object_fields(obj)

        assert "id" in masked
        assert "name" in masked
        assert "ssn" not in masked  # Hidden
        assert masked["email"] == "***@***"  # Masked

    def test_to_dict(self):
        """Test serialization to dict."""
        perm = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            can_read=True,
            can_create=True,
        )

        data = perm.to_dict()

        assert data["object_type"] == "Task"
        assert data["role_id"] == "developer"
        assert data["can_read"] is True
        assert data["can_create"] is True
        assert "created_at" in data


class TestObjectTypePermissionRegistry:
    """Tests for ObjectTypePermissionRegistry."""

    def test_register_and_get(self, object_permission_registry):
        """Test registering and retrieving permissions."""
        perm = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
        )

        object_permission_registry.register(perm)

        retrieved = object_permission_registry.get("Task", "developer")
        assert retrieved is not None
        assert retrieved.id == perm.id

    def test_get_for_object_type(self, object_permission_registry):
        """Test getting all permissions for an ObjectType."""
        perm1 = ObjectTypePermission(object_type="Task", role_id="developer")
        perm2 = ObjectTypePermission(object_type="Task", role_id="admin")
        perm3 = ObjectTypePermission(object_type="Project", role_id="developer")

        object_permission_registry.register(perm1)
        object_permission_registry.register(perm2)
        object_permission_registry.register(perm3)

        task_perms = object_permission_registry.get_for_object_type("Task")
        assert len(task_perms) == 2

    def test_remove_permission(self, object_permission_registry):
        """Test removing a permission."""
        perm = ObjectTypePermission(object_type="Task", role_id="developer")
        object_permission_registry.register(perm)

        removed = object_permission_registry.remove("Task", "developer")
        assert removed is True
        assert object_permission_registry.get("Task", "developer") is None


# =============================================================================
# TEAM TESTS
# =============================================================================


class TestTeam:
    """Tests for Team model."""

    def test_create_team(self):
        """Test creating a basic team."""
        team = Team(
            name="Engineering",
            description="Engineering team",
            members=["agent-001", "agent-002"],
        )

        assert team.name == "Engineering"
        assert len(team.members) == 2
        assert team.status == TeamStatus.ACTIVE
        assert team.id is not None

    def test_add_member(self):
        """Test adding members to a team."""
        team = Team(name="Backend")

        membership = team.add_member(
            agent_id="agent-001",
            membership_type=TeamMembershipType.MEMBER,
            added_by="admin-001",
        )

        assert "agent-001" in team.members
        assert membership.agent_id == "agent-001"
        assert membership.membership_type == TeamMembershipType.MEMBER

    def test_remove_member(self):
        """Test removing members from a team."""
        team = Team(name="Backend", members=["agent-001", "agent-002"])

        removed = team.remove_member("agent-001")

        assert removed is True
        assert "agent-001" not in team.members
        assert "agent-002" in team.members

    def test_team_hierarchy(self, team_registry):
        """Test team hierarchy with parent teams."""
        parent_team = Team(name="Engineering")
        child_team = Team(name="Backend", parent_team_id=parent_team.id)

        team_registry.register(parent_team)
        team_registry.register(child_team)

        # Check hierarchy
        children = team_registry.get_children(parent_team.id)
        assert len(children) == 1
        assert children[0].id == child_team.id

        ancestors = team_registry.get_ancestors(child_team.id)
        assert len(ancestors) == 1
        assert ancestors[0].id == parent_team.id

    def test_team_permissions(self):
        """Test team permissions for ObjectTypes."""
        team = Team(name="Backend")

        perm = ObjectTypePermission(
            object_type="Database",
            role_id="backend",
            can_read=True,
            can_update=True,
        )
        team.add_permission(perm)

        retrieved = team.get_permission_for_object_type("Database")
        assert retrieved is not None
        assert retrieved.can_update is True

    def test_membership_expiration(self):
        """Test membership expiration."""
        team = Team(name="Backend")

        # Add member with expiration
        team.add_member(
            agent_id="agent-001",
            expires_at=utc_now() - timedelta(hours=1),
        )

        active = team.get_active_members()
        assert "agent-001" not in active


class TestTeamRegistry:
    """Tests for TeamRegistry."""

    def test_get_teams_for_agent(self, team_registry):
        """Test finding all teams an agent belongs to."""
        team1 = Team(name="Team A", members=["agent-001"])
        team2 = Team(name="Team B", members=["agent-001", "agent-002"])
        team3 = Team(name="Team C", members=["agent-002"])

        team_registry.register(team1)
        team_registry.register(team2)
        team_registry.register(team3)

        teams = team_registry.get_teams_for_agent("agent-001")
        assert len(teams) == 2

    def test_get_all_descendants(self, team_registry):
        """Test getting all descendant teams."""
        root = Team(name="Company")
        eng = Team(name="Engineering", parent_team_id=root.id)
        backend = Team(name="Backend", parent_team_id=eng.id)
        frontend = Team(name="Frontend", parent_team_id=eng.id)

        team_registry.register(root)
        team_registry.register(eng)
        team_registry.register(backend)
        team_registry.register(frontend)

        descendants = team_registry.get_all_descendants(root.id)
        assert len(descendants) == 3


# =============================================================================
# INSTANCE PERMISSION TESTS
# =============================================================================


class TestInstancePermission:
    """Tests for InstancePermission model."""

    def test_create_instance_permission(self):
        """Test creating instance-level permission."""
        perm = InstancePermission(
            instance_id="task-123",
            object_type="Task",
            owner_id="agent-001",
        )

        assert perm.instance_id == "task-123"
        assert perm.object_type == "Task"
        assert perm.is_owner("agent-001") is True
        assert perm.is_owner("agent-002") is False

    def test_permission_grants(self):
        """Test adding and checking permission grants."""
        perm = InstancePermission(
            instance_id="doc-123",
            object_type="Document",
        )

        # Add grant
        grant = PermissionGrant(
            principal_type="agent",
            principal_id="agent-002",
            permission_type=PermissionType.GRANT,
            operations={"read", "update"},
        )
        perm.add_grant(grant)

        # Check operations
        assert perm.check_operation("agent", "agent-002", "read") is True
        assert perm.check_operation("agent", "agent-002", "delete") is None
        assert perm.check_operation("agent", "agent-003", "read") is None

    def test_deny_overrides_grant(self):
        """Test that DENY takes precedence over GRANT."""
        perm = InstancePermission(
            instance_id="secret-doc",
            object_type="Document",
        )

        # Add grant
        perm.add_grant(PermissionGrant(
            principal_type="team",
            principal_id="team-1",
            permission_type=PermissionType.GRANT,
            operations={"read"},
        ))

        # Add deny
        perm.add_grant(PermissionGrant(
            principal_type="team",
            principal_id="team-1",
            permission_type=PermissionType.DENY,
            operations={"read"},
        ))

        # DENY should win
        assert perm.check_operation("team", "team-1", "read") is False

    def test_owner_full_access(self):
        """Test that owner has full access."""
        perm = InstancePermission(
            instance_id="task-123",
            object_type="Task",
            owner_id="agent-001",
        )

        # Owner should have access even with no explicit grants
        assert perm.check_operation("agent", "agent-001", "delete") is True


class TestInstancePermissionRegistry:
    """Tests for InstancePermissionRegistry."""

    def test_get_or_create(self, instance_permission_registry):
        """Test get_or_create functionality."""
        # First call creates
        perm1 = instance_permission_registry.get_or_create(
            instance_id="task-123",
            object_type="Task",
            owner_id="agent-001",
        )
        assert perm1 is not None

        # Second call returns existing
        perm2 = instance_permission_registry.get_or_create(
            instance_id="task-123",
            object_type="Task",
        )
        assert perm2.id == perm1.id


# =============================================================================
# PERMISSION RESOLVER TESTS
# =============================================================================


class TestPermissionResolver:
    """Tests for unified PermissionResolver."""

    def test_unknown_agent_denied(self, resolver):
        """Test that unknown agents are denied."""
        result = resolver.resolve(
            agent_id="unknown-agent",
            object_type="Task",
            operation="read",
        )

        assert result.allowed is False
        assert result.source == PermissionSource.DEFAULT
        assert "Unknown agent" in result.reason

    def test_instance_owner_allowed(self, resolver, permission_manager, instance_permission_registry):
        """Test that instance owner is allowed."""
        # Register agent
        agent = permission_manager.register_agent("agent-001")

        # Create instance permission with owner
        instance_perm = InstancePermission(
            instance_id="task-123",
            object_type="Task",
            owner_id="agent-001",
        )
        instance_permission_registry.register(instance_perm)

        result = resolver.resolve(
            agent_id="agent-001",
            object_type="Task",
            operation="delete",
            instance_id="task-123",
        )

        assert result.allowed is True
        assert result.source == PermissionSource.OWNER

    def test_object_type_permission(self, resolver, permission_manager, object_permission_registry):
        """Test ObjectType-level permission resolution."""
        # Register agent with role
        agent = permission_manager.register_agent("agent-001", roles=["developer"])

        # Create ObjectType permission for role
        perm = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            can_read=True,
            can_update=True,
            can_delete=False,
        )
        object_permission_registry.register(perm)

        # Check allowed operation
        result = resolver.resolve(
            agent_id="agent-001",
            object_type="Task",
            operation="update",
        )
        assert result.allowed is True
        assert result.source == PermissionSource.OBJECT_TYPE

        # Check denied operation
        result = resolver.resolve(
            agent_id="agent-001",
            object_type="Task",
            operation="delete",
        )
        assert result.allowed is False

    def test_team_permission_inheritance(self, resolver, permission_manager, team_registry):
        """Test team permission inheritance."""
        # Create team with permission
        team = Team(
            name="Engineering",
            members=["agent-001"],
            permissions=[
                ObjectTypePermission(
                    object_type="Project",
                    role_id="engineering",
                    can_read=True,
                    can_update=True,
                )
            ],
        )
        team_registry.register(team)

        # Register agent with team
        agent = permission_manager.register_agent("agent-001")
        agent.add_team(team.id)

        result = resolver.resolve(
            agent_id="agent-001",
            object_type="Project",
            operation="update",
        )

        assert result.allowed is True
        assert result.source == PermissionSource.TEAM

    def test_resolution_chain_audit(self, resolver, permission_manager):
        """Test that resolution chain is properly recorded."""
        permission_manager.register_agent("agent-001")

        result = resolver.resolve(
            agent_id="agent-001",
            object_type="Unknown",
            operation="read",
        )

        assert len(result.resolution_chain) > 0
        assert "instance_check:start" not in result.resolution_chain  # No instance_id

    def test_field_access_check(self, resolver, permission_manager, object_permission_registry):
        """Test field-level access checking."""
        agent = permission_manager.register_agent("agent-001", roles=["viewer"])

        perm = ObjectTypePermission(
            object_type="Document",
            role_id="viewer",
            can_read=True,
            field_restrictions={
                "secret": FieldPermission(access_level=FieldAccessLevel.HIDDEN),
                "budget": FieldPermission(access_level=FieldAccessLevel.MASKED),
            },
        )
        object_permission_registry.register(perm)

        # Check regular field
        allowed, level = resolver.can_access_field(
            agent_id="agent-001",
            object_type="Document",
            field_name="title",
        )
        assert allowed is True
        assert level == FieldAccessLevel.FULL

        # Check hidden field
        allowed, level = resolver.can_access_field(
            agent_id="agent-001",
            object_type="Document",
            field_name="secret",
        )
        assert allowed is False
        assert level == FieldAccessLevel.HIDDEN


# =============================================================================
# AGENT IDENTITY TEAM TESTS
# =============================================================================


class TestAgentIdentityTeams:
    """Tests for AgentIdentity team membership."""

    def test_add_team(self):
        """Test adding team to agent."""
        agent = AgentIdentity(id="agent-001", name="Test Agent")

        added = agent.add_team("team-001")
        assert added is True
        assert "team-001" in agent.team_ids

        # Adding same team again should return False
        added = agent.add_team("team-001")
        assert added is False

    def test_remove_team(self):
        """Test removing team from agent."""
        agent = AgentIdentity(
            id="agent-001",
            name="Test Agent",
            team_ids=["team-001", "team-002"],
        )

        removed = agent.remove_team("team-001")
        assert removed is True
        assert "team-001" not in agent.team_ids
        assert "team-002" in agent.team_ids

    def test_has_team(self):
        """Test checking team membership."""
        agent = AgentIdentity(
            id="agent-001",
            team_ids=["team-001"],
        )

        assert agent.has_team("team-001") is True
        assert agent.has_team("team-002") is False


# =============================================================================
# RUN TESTS
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
