import asyncio
import time
from datetime import datetime, timedelta
from cdp import CdpClient
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, Response
from queue import Queue
import threading

load_dotenv()

app = Flask(__name__)
active_tasks = {}

class FaucetClaimer:
    def __init__(self, wallet_address, target_eth_amount):
        self.wallet_address = wallet_address
        self.target_eth_amount = float(target_eth_amount)
        self.claim_amount = 0.0001  # Amount received per successful claim
        self.retry_delay = 5  # Delay between attempts in seconds
        self.daily_wait_period = 24 * 60 * 60  # 24 hours in seconds
        self.message_queue = Queue()
        self.is_running = True

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.message_queue.put(f"[{timestamp}] {message}")

    async def claim_coinbase_faucet(self):
        while self.is_running:
            start_time = datetime.now()
            self.log(f"Starting new claiming session")
            
            api_key_id = os.getenv("CDP_API_KEY_ID")
            api_key_secret = os.getenv("CDP_API_KEY_SECRET")

            if not api_key_id or not api_key_secret:
                self.log("Error: CDP_API_KEY_ID and CDP_API_KEY_SECRET not set in .env file.")
                self.log("Please create a .env file in the same directory as your script with:")
                self.log("CDP_API_KEY_ID=\"your_api_key_id\"")
                self.log("CDP_API_KEY_SECRET=\"your_api_key_secret\"")
                break

            total_claimed = 0
            attempt = 1
            claims_needed = self.target_eth_amount / self.claim_amount
            
            self.log(f"Starting faucet claims:")
            self.log(f"Target: {self.target_eth_amount} ETH")
            self.log(f"Amount per claim: {self.claim_amount} ETH")
            self.log(f"Estimated claims needed: {claims_needed:.0f}")

            while total_claimed < self.target_eth_amount and self.is_running:
                self.log(f"Attempt #{attempt} - Current total: {total_claimed:.6f} ETH / Target: {self.target_eth_amount} ETH ({(total_claimed/self.target_eth_amount*100):.1f}%)")
                
                try:
                    async with CdpClient(api_key_id=api_key_id, api_key_secret=api_key_secret) as cdp:
                        self.log(f"Attempting to claim faucet funds for wallet address: {self.wallet_address}")

                        self.log(f"Requesting funds from Base Sepolia faucet...")
                        faucet_hash = await cdp.evm.request_faucet(
                            address=self.wallet_address,
                            network="base-sepolia",
                            token="eth"
                        )
                        self.log(f"Faucet transaction initiated. Check status at:")
                        self.log(f"https://sepolia.basescan.org/tx/{faucet_hash}")

                        total_claimed += self.claim_amount
                        self.log(f"Successfully claimed {self.claim_amount} ETH! New total: {total_claimed:.6f} ETH")
                        remaining = self.target_eth_amount - total_claimed
                        if remaining > 0:
                            self.log(f"Remaining to claim: {remaining:.6f} ETH")

                except Exception as e:
                    self.log(f"An error occurred: {e}")
                    error_message = str(e).lower()
                    if "rate limit" in error_message or "too many requests" in error_message:
                        self.log("Possible rate limit hit.")
                        self.log(f"Waiting {self.retry_delay} seconds before trying again...")
                    elif "insufficient funds" in error_message or "limit reached" in error_message:
                        self.log("Faucet daily limit reached.")
                        self.log("Waiting 24 hours before continuing...")
                        if self.is_running:
                            await asyncio.sleep(self.daily_wait_period)
                    else:
                        self.log(f"Unforeseen error: {e}")
                
                attempt += 1
                if total_claimed < self.target_eth_amount and self.is_running:
                    self.log(f"Waiting {self.retry_delay} seconds before next attempt...")
                    await asyncio.sleep(self.retry_delay)

            if self.is_running:
                completion_time = datetime.now()
                next_run_time = completion_time + timedelta(days=1)
                self.log(f"Target amount reached! Total claimed: {total_claimed:.6f} ETH")
                self.log(f"Total attempts made: {attempt-1}")
                self.log(f"Session completed at: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.log(f"Next run scheduled for: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.log("Waiting 24 hours before starting next session...")
                
                await asyncio.sleep(self.daily_wait_period)
            else:
                self.log("Faucet claimer stopped by user.")
                break

    def stop(self):
        self.is_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_claiming():
    wallet = request.args.get('wallet')
    amount = request.args.get('amount')
    
    if not wallet or not amount:
        return "Missing parameters", 400

    # Stop any existing task for this wallet
    if wallet in active_tasks:
        active_tasks[wallet]['claimer'].stop()
        active_tasks[wallet]['thread'].join()
        del active_tasks[wallet]

    def send_events():
        claimer = FaucetClaimer(wallet, amount)
        
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(claimer.claim_coinbase_faucet())
            loop.close()

        thread = threading.Thread(target=run_async_loop)
        thread.start()
        
        active_tasks[wallet] = {
            'claimer': claimer,
            'thread': thread
        }

        while True:
            try:
                message = claimer.message_queue.get()
                yield f"data: {message}\n\n"
            except:
                break

    return Response(send_events(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True, threaded=True)