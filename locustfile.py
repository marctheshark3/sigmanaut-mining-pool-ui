from locust import HttpUser, task, between
import random

from utils.reader import SigmaWalletReader

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Simulated users wait 1-5 seconds between tasks

    def on_start(self):
        # Define a list of wallet addresses to choose from
        reader = SigmaWalletReader('../conf')
        self.wallet_addresses = reader.get_miner_ls()

    @task
    def load_homepage(self):
        self.client.get("/")

    @task(2)
    def load_specific_wallet_dashboard(self):
        # Randomly select a wallet address for each request
        wallet_address = random.choice(self.wallet_addresses)
        response = self.client.get(f"/{wallet_address}")
        if response.status_code != 200:
            print(f"Failed to load wallet dashboard for {wallet_address}: {response.status_code}")


