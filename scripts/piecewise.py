from ape import networks, Contract
from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
from ape.utils import ZERO_ADDRESS
from eth_utils import event_abi_to_log_topic

def fetch_events(vault_address):
    vault = Contract(vault_address)
    provider = networks.provider

    # Get the ABI for the events (used to get topics)
    deposit_event_abi = next(event for event in vault.contract_type.abi if event.type == 'event' and event.name == 'Deposit')
    withdraw_event_abi = next(event for event in vault.contract_type.abi if event.type == 'event' and event.name == 'Withdraw')

    # Get event topics
    deposit_event_topic = event_abi_to_log_topic(deposit_event_abi)
    withdraw_event_topic = event_abi_to_log_topic(withdraw_event_abi)

    # Fetch deposit events
    deposit_logs = provider.get_logs(
        addresses=[vault_address],
        topics=[deposit_event_topic],
        start_block=0,
        stop_block='latest'
    )

    # Fetch withdrawal events
    withdraw_logs = provider.get_logs(
        addresses=[vault_address],
        topics=[withdraw_event_topic],
        start_block=0,
        stop_block='latest'
    )

    return deposit_logs, withdraw_logs

def decode_event_logs(vault, logs):
    decoded_events = []
    for log in logs:
        event = vault.decode_log(log)
        decoded_events.append(event)
    return decoded_events

def process_events(vault_address):
    deposit_logs, withdraw_logs = fetch_events(vault_address)
    vault = Contract(vault_address)

    # Decode logs
    deposit_events = decode_event_logs(vault, deposit_logs)
    withdraw_events = decode_event_logs(vault, withdraw_logs)

    # Add event type
    for event in deposit_events:
        event.event_type = 'deposit'
    for event in withdraw_events:
        event.event_type = 'withdraw'

    # Combine and sort events by block number
    all_events = deposit_events + withdraw_events
    all_events.sort(key=lambda x: x.block_number)

    return all_events

def get_aps(vault, block_number, decimals):
    # For Idle Finance, use tokenPrice
    token_price = vault.tokenPrice(block_identifier=block_number)
    aps = token_price / (10 ** decimals)
    return aps

def calculate_piecewise_yield(vault_address):
    all_events = process_events(vault_address)
    provider = networks.provider
    vault = Contract(vault_address)
    decimals = vault.decimals()

    yield_accumulated = Decimal(0)
    previous_event = None

    for i, event in enumerate(all_events):
        block_number = event.block_number
        timestamp = provider.get_block(block_number).timestamp

        aps = get_aps(vault, block_number, decimals)

        if previous_event is not None:
            # Time difference
            time_diff = timestamp - previous_event.timestamp

            # Yield for the interval
            interval_yield = ((aps - previous_event.aps) / previous_event.aps) * 100

            # Accumulate yield
            yield_accumulated += interval_yield

        # Update previous_event data
        previous_event = SimpleNamespace(
            timestamp=timestamp,
            aps=aps,
            event=event
        )

    # Calculate yield from the last event to the current block
    current_block_number = provider.get_block('latest').number
    current_timestamp = provider.get_block('latest').timestamp
    current_aps = get_aps(vault, current_block_number, decimals)

    if previous_event:
        interval_yield = ((current_aps - previous_event.aps) / previous_event.aps) * 100
        yield_accumulated += interval_yield

    print(f"Total Yield: {yield_accumulated:.2f}%")

# Example usage
def main():
    vault_address = "0x5274891bEC421B39D23760c04A6755eCB444797C"  # IdleUSDC Yield
    calculate_piecewise_yield(vault_address)
