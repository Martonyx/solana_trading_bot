import os
from typing import Dict, Any
from flask import Flask, request, jsonify
from dexteritysdk.dex.sdk_context import SDKContext
from dexteritysdk.dex.events import OrderFillEvent
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import requests
import json
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

app = Flask(__name__)

rpc = "https://devnet-rpc.shyft.to?api_key=gFiieg8pfYoK0jQ2" # Devnet RPC
client = Client(rpc)
payer = Keypair()
mpg = "BRWNCEzQTm8kvEXHsVVY9jpb1VLbpv9B8mkF43nMLCtu" # Stakechip Devnet MPG Key
market_product_group_key = Pubkey.from_string(mpg)

ctx = SDKContext.connect(
  client=client,
  market_product_group_key=market_product_group_key,
  payer=payer,
  raise_on_error=True
)


@app.route('/', methods=['GET'])
def status():
    return jsonify({'status': 'live'})

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Recieves transaction data, parses it, proccess it and then sends it to the trade api to get executed
    """
    data = request.get_json()
    data = data[0]
    if data.get("meta", {}).get("err") is not None:
        return jsonify({'error': "Transaction failed"}), 400

    try:   
        handle_transaction(data)
        return jsonify({"message": "Transaction processed"}), 200
    except Exception as e:
        print(f"Exception during transaction processing: {e}")
        return jsonify({'error': "Transaction failed to process"}), 500


def handle_transaction(tr: Dict[str, Any]):
    """
    Checks the given transaction object for fill events and calls the Trading API if found.
    
    :param tr: A dictionary representing the transaction.
    """
    events = ctx.parse_events_from_logs(tr.get("meta", {}).get("logMessages", []))
    fill_events = [event for event in events if isinstance(event, OrderFillEvent)]

    if fill_events:
        parsed_trades = [event_to_trade_data(tr, event) for event in fill_events]

        try:
            for trade in parsed_trades:
                print(trade)
            print(f"Sent {len(parsed_trades)} trade events.")
        except Exception as e:
            print(f"Failed to send fill events due to error: {e}")
    else:
        print("No fill events found in transaction.")

def event_to_trade_data(event: OrderFillEvent) -> Dict[str, Any]:
    """
    Parses an OrderFillEvent into a Trade Object.
    
    :param event: The OrderFillEvent instance.
    :return: A Trade Object representing the fill event to send to the Trading API for execution.
    """

def proccess_trade(trade):
   url = os.environ.get('TRADING_API_URL', 'http://localhost:3000') + '/process-trade'
  
   headers = {'Content-Type': 'application/json'}
  
   data = json.dumps(trade)
  
   try:
       response = requests.post(url, headers=headers, data=data)
      
       print("Status Code:", response.status_code)
       print("Response:", response.json())
   except Exception as e:
       print(f"An error occurred: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port="3001")