from locust import HttpUser, task, between
import random

from utils.api_reader import SigmaWalletReader

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Simulated users wait 1-5 seconds between tasks

    def on_start(self):
        # Define a list of wallet addresses to choose from
        self.sigma_reader = SigmaWalletReader('../conf')
        self.wallet_addresses = self.sigma_reader.get_miner_ls()

    @task
    def load_homepage(self):
        self.client.get("/")

    @task(2)
    def load_specific_wallet_dashboard(self):
        # Randomly select a wallet address for each request
        wallet_address = random.choice(self.wallet_addresses)
        response = self.client.get(f"/{wallet_address}")

        self.sigma_reader.update_data()
        self.sigma_reader.get_miner_payment_stats(wallet_address)
        self.sigma_reader.get_latest_worker_samples(True)
        self.sigma_reader.get_total_hash_data()

        # _, performance_df = self.sigma_reader.get_mining_stats(wallet_address)
        # block_df, _, _ = self.sigma_reader.get_block_stats(wallet_address)
        # miner_performance = self.sigma_reader.get_miner_samples(wallet_address)
        # pool_df, _ = self.sigma_reader.get_pool_stats(wallet_address)

        if response.status_code != 200:
            print(f"Failed to load wallet dashboard for {wallet_address}: {response.status_code}")


