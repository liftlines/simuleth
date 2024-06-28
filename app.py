from flask import Flask, render_template, request
import math
import os

app = Flask(__name__, static_folder='static', static_url_path='')

# Constants from the Ethereum specification
SLOTS_PER_EPOCH = 32
SECONDS_PER_SLOT = 12
EPOCHS_PER_SYNC_COMMITTEE_PERIOD = 256
SYNC_COMMITTEE_SIZE = 512
TIMELY_TARGET_FLAG_INDEX = 1
WEIGHT_DENOMINATOR = 64
TIMELY_TARGET_MULTIPLIER = 32
INACTIVITY_PENALTY_QUOTIENT_DENEB = 2**26
INACTIVITY_SCORE_BIAS = 4
MIN_SLASHING_PENALTY_QUOTIENT_DENEB = 32
GWEI_PER_ETH = 10**9
BASE_REWARD_FACTOR = 64
EFFECTIVE_BALANCE_INCREMENT = 10**9  # 1 GWei
MAX_EFFECTIVE_BALANCE = 32 * 10**9  # 32 ETH in Gwei
BASE_REWARDS_PER_EPOCH = 4
EPOCHS_PER_SLASHING_SPAN = 8192
PROPORTIONAL_SLASHING_MULTIPLIER = 3

# Total number of active validators in the network
TOTAL_VALIDATORS = 1027576

# Market share percentages of different client implementations
CLIENT_PERCENTAGES = {
    'execution': {
        'geth': 0.55,
        'nethermind': 0.28,
        'besu': 0.14,
        'erigon': 0.03
    },
    'consensus': {
        'nimbus': 0.11,
        'lighthouse': 0.30,
        'prysm': 0.38,
        'teku': 0.1963,
        'lodestar': 0.01
    }
}

def calculate_base_reward(balance_gwei):
    """
    Calculate the base reward for a validator based on its balance.

    Args:
    balance_gwei (int): The validator's balance in Gwei.

    Returns:
    int: The base reward in Gwei.
    """
    return (balance_gwei // EFFECTIVE_BALANCE_INCREMENT) * BASE_REWARD_FACTOR

def calculate_inactivity_penalty(balance_gwei, offline_epochs, epochs_since_finality):
    """
    Calculate the inactivity penalty for a validator that has been offline.

    Args:
    balance_gwei (int): The validator's balance in Gwei.
    offline_epochs (int): The number of epochs the validator has been offline.
    epochs_since_finality (int): The number of epochs since the last finality checkpoint.

    Returns:
    int: The inactivity penalty in Gwei.
    """
    inactivity_score = min(offline_epochs, epochs_since_finality) * INACTIVITY_SCORE_BIAS
    penalty_numerator = balance_gwei * inactivity_score
    penalty_denominator = INACTIVITY_PENALTY_QUOTIENT_DENEB
    return penalty_numerator // penalty_denominator

def estimate_missed_attestation_rewards(balance_gwei, offline_epochs):
    """
    Estimate the rewards missed due to missed attestations while offline.

    Args:
    balance_gwei (int): The validator's balance in Gwei.
    offline_epochs (int): The number of epochs the validator has been offline.

    Returns:
    int: The estimated missed rewards in Gwei.
    """
    base_reward = calculate_base_reward(balance_gwei)
    return base_reward * BASE_REWARDS_PER_EPOCH * offline_epochs

def calculate_slashing_penalty(balance_gwei):
    """
    Calculate the base slashing penalty for a validator.

    Args:
    balance_gwei (int): The validator's balance in Gwei.

    Returns:
    int: The base slashing penalty in Gwei.
    """
    return balance_gwei // MIN_SLASHING_PENALTY_QUOTIENT_DENEB

def calculate_correlated_slashing_penalty(balance_gwei, client_type, client_name):
    """
    Calculate the correlated slashing penalty based on the client used.

    Args:
    balance_gwei (int): The validator's balance in Gwei.
    client_type (str): The type of client ('execution' or 'consensus').
    client_name (str): The name of the client.

    Returns:
    tuple: (total_penalty, base_penalty, additional_penalty) all in Gwei.
    """
    effective_balance = min(balance_gwei, MAX_EFFECTIVE_BALANCE)

    # Calculate the base slashing penalty
    base_penalty = calculate_slashing_penalty(effective_balance)

    # Calculate the percentage of affected validators based on client market share
    affected_percentage = CLIENT_PERCENTAGES[client_type][client_name]

    # Calculate the correlation factor (capped at 1/3)
    correlation_factor = min(affected_percentage, 1/3)

    # Calculate the additional penalty due to correlation
    additional_penalty = effective_balance * correlation_factor * PROPORTIONAL_SLASHING_MULTIPLIER

    # The total penalty is the base penalty plus the additional penalty
    total_penalty = base_penalty + additional_penalty

    return total_penalty, base_penalty, additional_penalty

def estimate_long_term_penalty(balance_gwei):
    """
    Estimate the long-term penalty a slashed validator might face.

    Args:
    balance_gwei (int): The validator's balance in Gwei.

    Returns:
    int: The estimated long-term penalty in Gwei.
    """
    effective_balance = min(balance_gwei, MAX_EFFECTIVE_BALANCE)
    base_reward = calculate_base_reward(effective_balance)

    # Estimate penalties for missed attestations over EPOCHS_PER_SLASHING_SPAN
    return base_reward * BASE_REWARDS_PER_EPOCH * EPOCHS_PER_SLASHING_SPAN

def hours_to_epochs(hours):
    """
    Convert hours to the equivalent number of epochs.

    Args:
    hours (float): Number of hours.

    Returns:
    int: Equivalent number of epochs, rounded up.
    """
    return math.ceil(hours * 3600 / (SLOTS_PER_EPOCH * SECONDS_PER_SLOT))

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main route handler for the validator penalty calculator.
    Processes form submissions and calculates penalties based on the selected scenario.
    """
    if request.method == 'POST':
        try:
            # Extract common form data
            penalty_type = request.form['penalty_type']
            balance_str = request.form.get('balance', '').strip()
            if not balance_str:
                raise ValueError("Validator Balance is required")
            balance_eth = float(balance_str)
            balance_gwei = int(balance_eth * GWEI_PER_ETH)
            execution_client = request.form.get('execution_client')
            consensus_client = request.form.get('consensus_client')

            if penalty_type == 'Node goes offline':
                # Handle offline node scenario
                offline_hours_str = request.form.get('offline_hours', '').strip()
                if not offline_hours_str:
                    raise ValueError("Offline Duration is required")
                offline_hours = float(offline_hours_str)
                offline_epochs = hours_to_epochs(offline_hours)
                epochs_since_finality = offline_epochs  # Assuming offline duration equals epochs since finality

                inactivity_penalty_gwei = calculate_inactivity_penalty(balance_gwei, offline_epochs, epochs_since_finality)
                inactivity_penalty_eth = inactivity_penalty_gwei / GWEI_PER_ETH
                missed_rewards_gwei = estimate_missed_attestation_rewards(balance_gwei, offline_epochs)
                missed_rewards_eth = missed_rewards_gwei / GWEI_PER_ETH

                return render_template('result_offline.html',
                                       inactivity_penalty_eth=inactivity_penalty_eth,
                                       missed_rewards_eth=missed_rewards_eth)

            elif penalty_type == 'Double Signing - by redundant validator':
                # Handle double signing scenario
                base_penalty_gwei = calculate_slashing_penalty(balance_gwei)
                base_penalty_eth = base_penalty_gwei / GWEI_PER_ETH

                include_correlated_penalty = request.form.get('include_correlated_penalty') == 'true'
                if include_correlated_penalty:
                    correlation_cause = request.form.get('correlation_cause')
                    if not correlation_cause:
                        raise ValueError("Correlation cause is required when including correlated penalty")
                    client = execution_client if correlation_cause == 'execution' else consensus_client
                    total_penalty_gwei, _, additional_penalty_gwei = calculate_correlated_slashing_penalty(balance_gwei, correlation_cause, client)
                    additional_correlated_penalty_eth = additional_penalty_gwei / GWEI_PER_ETH
                else:
                    total_penalty_gwei = base_penalty_gwei
                    additional_correlated_penalty_eth = 0

                # Estimate long-term penalty
                long_term_penalty_gwei = estimate_long_term_penalty(balance_gwei)
                long_term_penalty_eth = long_term_penalty_gwei / GWEI_PER_ETH

                # Calculate total penalty
                total_penalty_eth = (total_penalty_gwei + long_term_penalty_gwei) / GWEI_PER_ETH

                return render_template('result_double_signing.html',
                                       base_slashing_penalty_eth=base_penalty_eth,
                                       include_correlated_penalty=include_correlated_penalty,
                                       additional_correlated_penalty_eth=additional_correlated_penalty_eth,
                                       long_term_penalty_eth=long_term_penalty_eth,
                                       total_penalty_eth=total_penalty_eth)
            else:
                return "Error: Unsupported penalty type."
        except ValueError as e:
            return render_template('error.html', error=str(e))

    # If it's a GET request, just render the initial form
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
