from typing import Dict, Any
from flask import Flask, request, jsonify
from dexteritysdk.dex.sdk_context import SDKContext
from dexteritysdk.dex.events import OrderFillEvent
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

app = Flask(__name__)

@app.route('/', methods=['GET'])
def status():
    return jsonify({'status': 'live'})

payer = Keypair()
mpg = Pubkey.from_string("BRWNCEzQTm8kvEXHsVVY9jpb1VLbpv9B8mkF43nMLCtu")
client = Client("https://devnet-rpc.shyft.to?api_key=JUvCRqsUep-u4yk0")

ctx = SDKContext.connect(
    client=client,
    market_product_group_key=mpg,
    payer=payer,
    raise_on_error=True
)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Recieves transaction data, parses it, proccess it and then sends it to the trade api to get executed
    """
    data = request.get_json()
    
    tr = data[0]
    if tr.get("meta", {}).get("err", {}) is not None:
        return jsonify({"Error": "Transaction failed"})
    
    handle_transaction(tr)
    return jsonify({"success": "parsed txn data"})


def handle_transaction(tr: Dict[str, Any]):
    """
    Checks the given transaction object for fill events and calls the Trading API if found.
    
    :param tr: A dictionary representing the transaction.
    """
    logs = tr.get("meta", {}).get("logMessages", [])
    parsed_events = ctx.parse_events_from_logs(logs)
    fill_events = [event for event in parsed_events if isinstance(event, OrderFillEvent)]
    for event in fill_events:
        event_to_trade_data(event)

def event_to_trade_data(event: OrderFillEvent) -> Dict[str, Any]:
    """
    Parses an OrderFillEvent into a Trade Object.
    
    :param event: The OrderFillEvent instance.
    :return: A Trade Object representing the fill event to send to the Trading API for execution.
    """
    trade = {
        "product": event.product,
        "taker": str(event.taker_trader_risk_group),
        "maker": str(event.maker_trader_risk_group),
        "price": event.price,
        "quote_size": event.quote_size,
        "size": event.base_size,
        "side": event.taker_side
    }
    
    print(trade)
    return trade

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port="80")