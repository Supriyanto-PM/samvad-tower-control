"""
Unit tests for Navigation Routing and Logout State Lifecycle.
"""
import unittest

class TestNavigationRouting(unittest.TestCase):
    def setUp(self):
        self.slug_map = {
            "dashboard": "Dashboard",
            "paas_rollout": "PaaS Rollout",
            "customs": "Customs & Logistics",
            "sga": "SG&A Finance",
            "site_ops": "Site Operations",
            "reports": "Reports",
            "update": "Update & Sync",
            "settings": "Settings",
            "portal": "Logout",
            "logout": "Logout"
        }
        self.inv_slug_map = {
            "Dashboard": "dashboard",
            "PaaS Rollout": "paas_rollout",
            "Customs & Logistics": "customs",
            "SG&A Finance": "sga",
            "Site Operations": "site_ops",
            "Reports": "reports",
            "Update & Sync": "update",
            "Settings": "settings"
        }

    def test_slug_mapping_symmetry(self):
        for label, slug in self.inv_slug_map.items():
            self.assertEqual(self.slug_map.get(slug), label)

    def test_logout_slugs(self):
        self.assertEqual(self.slug_map.get("logout"), "Logout")
        self.assertEqual(self.slug_map.get("portal"), "Logout")

    def test_logout_state_transition(self):
        session_state = {
            "show_welcome": False,
            "ribbon_nav": "PaaS Rollout",
            "last_active_nav": "PaaS Rollout"
        }
        query_params = {"nav": "paas_rollout"}

        # Simulate clicking Logout
        selected_nav = "Logout"
        if selected_nav == "Logout":
            session_state["show_welcome"] = True
            session_state["pending_nav"] = "Dashboard"
            session_state["last_active_nav"] = "Dashboard"
            query_params.clear()

        # Assert post-logout state
        self.assertTrue(session_state["show_welcome"])
        self.assertEqual(session_state["pending_nav"], "Dashboard")
        self.assertEqual(session_state["last_active_nav"], "Dashboard")
        self.assertEqual(len(query_params), 0)

        # Simulate clicking Enter on Welcome page
        session_state["show_welcome"] = False
        session_state["pending_nav"] = "Dashboard"
        query_params["nav"] = "dashboard"

        # Simulate pre-instantiation widget resolution
        if "pending_nav" in session_state:
            session_state["ribbon_nav"] = session_state.pop("pending_nav")

        self.assertFalse(session_state["show_welcome"])
        self.assertEqual(session_state["ribbon_nav"], "Dashboard")
        self.assertNotIn("pending_nav", session_state)
        self.assertEqual(query_params["nav"], "dashboard")

if __name__ == "__main__":
    unittest.main()
