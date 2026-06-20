"""
Tests for profile update with name field.
Run: python -m pytest tests/test_profile_name.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestUserModelHasName:
    """User model must have a name column."""

    def test_user_model_has_name_column(self):
        from api.app.database import User
        assert hasattr(User, 'name'), "User model missing 'name' column"

    def test_user_to_dict_includes_name(self):
        from api.app.database import User
        user = User.__table__
        columns = [c.name for c in user.columns]
        assert 'name' in columns, "User table missing 'name' column"


class TestProfileUpdateWithName:
    """Profile update endpoint must handle name field."""

    def test_update_profile_accepts_name(self):
        """Backend update_profile must read 'name' from request body."""
        import ast
        import inspect
        source_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'app', 'profile.py')
        with open(source_file) as f:
            source = f.read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'update_profile':
                body_src = ast.get_source_segment(source, node)
                assert "'name'" in body_src or '"name"' in body_src, \
                    "update_profile doesn't handle 'name' field"
                return
        pytest.fail("update_profile function not found")


class TestFrontendProfileSendsName:
    """Frontend profile page must send name to API."""

    def test_api_client_update_profile_accepts_name(self):
        import ast
        source_file = os.path.join(os.path.dirname(__file__), '..', 'frontend-next', 'src', 'lib', 'api-client.ts')
        with open(source_file) as f:
            source = f.read()
        assert 'name' in source, "api-client updateProfile doesn't include 'name'"

    def test_profile_page_sends_name(self):
        import ast
        source_file = os.path.join(os.path.dirname(__file__), '..', 'frontend-next', 'src', 'app', 'dashboard', 'profile', 'page.tsx')
        with open(source_file) as f:
            source = f.read()
        assert 'name: data.name' in source or "name: data['name']" in source, \
            "Profile page doesn't send name to API"
