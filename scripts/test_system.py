# scripts/test_system.py
import requests
import json
import time
from datetime import datetime, timedelta, timezone
import logging
import sys
from tabulate import tabulate
from typing import Dict, Any, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('system_tests.log', encoding='utf-8')
    ]
)

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.tokens = {}
        self.test_results = []
        self.session = requests.Session()

    def make_request(self, test_name: str, method: str, endpoint: str, 
                    token_type: str = None, data: dict = None) -> tuple[bool, Any]:
        """Make HTTP request and return (success, response_data)"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token_type and token_type in self.tokens:
            headers["Authorization"] = f"Bearer {self.tokens[token_type]}"

        try:
            logging.info(f"\nMaking {method} request to {url}")
            logging.info(f"Headers: {headers}")
            logging.info(f"Data: {data}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            logging.info(f"Response Status: {response.status_code}")
            try:
                response_data = response.json()
                logging.info(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                logging.info(f"Response Text: {response.text}")
            
            success = 200 <= response.status_code < 300
            self.log_test(test_name, success, response)
            
            return success, response.json() if success else None
            
        except Exception as e:
            logging.error(f"Request error in {test_name}: {str(e)}")
            self.log_test(test_name, False, error=str(e))
            return False, None

    def log_test(self, name: str, success: bool, response: requests.Response = None, error: str = None):
        result = {
            'test': name,
            'status': 'PASS' if success else 'FAIL',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'details': error if error else (
                f"Status: {response.status_code}" if response else "No response"
            )
        }
        self.test_results.append(result)
        logging.info(f"{'✓' if success else '×'} {name}")

    def verify_server(self) -> bool:
        """Verify server is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return True
        except:
            logging.error("Server is not accessible")
            return False

    def authenticate(self) -> bool:
        """Handle admin and test user authentication"""
        # Login as admin
        success, response = self.make_request(
            "Admin Login",
            "POST",
            "/api/users/login",
            None,
            {"username": "admin", "password": "Admin123!@#"}
        )
        if not success:
            return False
        self.tokens['admin'] = response['token']

        # Create test user
        success, _ = self.make_request(
            "Create Test User",
            "POST",
            "/api/users/register",
            None,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "Test123!@#",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        if not success:
            return False

        # Login test user
        success, response = self.make_request(
            "Test User Login",
            "POST",
            "/api/users/login",
            None,
            {"username": "testuser", "password": "Test123!@#"}
        )
        if not success:
            return False
        self.tokens['user'] = response['token']

        return True

    def run_tests(self):
        """Execute all system tests in order"""
        if not self.verify_server():
            logging.error("Server verification failed")
            return

        if not self.authenticate():
            logging.error("Authentication failed")
            return

        # Create test raffle
        success, response = self.make_request(
            "Create Raffle",
            "POST",
            "/api/admin/raffles",
            "admin",
            {
                "title": "Test Raffle",
                "description": "Test Description",
                "total_tickets": 100,
                "ticket_price": 10.0,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "total_prize_count": 2,
                "instant_win_count": 0
            }
        )
        if not success:
            return
        raffle_id = response['id']

        test_sequence = [
            # User operations
            ("Add Credits", "POST", "/api/users/credits/2", "admin", 
             {"amount": 1000.0, "transaction_type": "add"}),
            ("View Profile", "GET", "/api/users/me", "user", None),
            ("Update Profile", "PUT", "/api/users/profile/2", "user",
             {"first_name": "Updated", "last_name": "Name"}),

            # Raffle lifecycle operations
            ("View Raffle", "GET", f"/api/raffles/{raffle_id}", None, None),
            ("Update Raffle", "PUT", f"/api/admin/raffles/{raffle_id}", "admin",
             {"title": "Updated Raffle"}),
            ("Set Coming Soon", "PUT", f"/api/admin/raffles/{raffle_id}/status", "admin",
             {"status": "coming_soon"}),
            ("Activate Raffle", "PUT", f"/api/admin/raffles/{raffle_id}/status", "admin",
             {"status": "active"}),

            # Ticket operations
            ("Purchase Tickets", "POST", f"/api/raffles/{raffle_id}/tickets", "user",
             {"quantity": 5}),
            ("View Purchased Tickets", "GET", "/api/raffles/tickets", "user", None),
            
            # End raffle and draw winners
            ("End Raffle", "PUT", f"/api/admin/raffles/{raffle_id}/status", "admin",
             {"status": "ended"}),
            ("Execute Draw", "POST", f"/api/admin/raffles/{raffle_id}/draw", "admin",
             {"draw_count": 2}),
            ("View Draw Results", "GET", f"/api/raffles/{raffle_id}/winners", "admin", None)
        ]

        for test_name, method, endpoint, token_type, data in test_sequence:
            success, response = self.make_request(test_name, method, endpoint, token_type, data)
            if not success:
                logging.error(f"Test sequence failed at: {test_name}")
                if test_name in ["Set Coming Soon", "Activate Raffle", "End Raffle"]:
                    # Get current raffle status for debugging
                    self.make_request(
                        f"Check Status after {test_name}",
                        "GET",
                        f"/api/raffles/{raffle_id}",
                        "admin",
                        None
                    )
            time.sleep(1)

        self.display_results()

    def display_results(self):
        """Display test results in a formatted table"""
        print("\n=== Test Results ===")
        headers = ['Test', 'Status', 'Time', 'Details']
        rows = [[r['test'], r['status'], r['timestamp'], r['details']] 
               for r in self.test_results]
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        print(f"\nSummary: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")

if __name__ == "__main__":
    print("\nStarting WildRandom System Tests...")
    tester = SystemTester()
    tester.run_tests()