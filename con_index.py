# A fully decentralized index token
# Individual token shares of the index are rebalanced to maintain a target allocation of each token in TAU value
# TAU value of a token is coming from DEX
# The rebalance function can be called by anyone and will make it so the TAU values of the tokens in the index (closely) represent the target relative allocations
# No human error possible

I = importlib

# LST001
balances = Hash(default_value=0)

# LST002
metadata = Hash()

@construct
def seed():
    
    # LST002
    metadata['token_name'] = "Index Token"
    metadata['token_symbol'] = "INDX"
    metadata['dex_contract'] = "con_rocketswap_official_v1_1"
    metadata['operators'] = [ctx.caller] # List of operators because if there will be a DAO, it will be added to this list
    metadata['fee_receiver'] = ctx.caller
    metadata['fee'] = 0.01 # 1% fee

    # Keep in mind that this starting allocation is not the final allocation 
    # The current allocation can be read using the get_metadata_allocations function
    # The allocations are not token amounts but TAU value based
    metadata['relative_allocations'] = {"currency": 0.5, "con_rswp_lst001": 0.25, "con_yeti": 0.25}
    
def get_current_tau_absolute_allocations():
    # Get the current TAU value of each token
    relative_allocations = metadata['relative_allocations']
    current_absolute_allocations = {}
    total_tau_value = 0
    
    for token_contract, relative_allocation in relative_allocations.items():
        token_contract_balances = ForeignHash(foreign_contract=token_contract, foreign_name="balances")
        contract_balance = token_contract_balances[ctx.this]
        if token_contract != "currency":
            dex_contract_prices = ForeignHash(foreign_contract=metadata['dex_contract'], foreign_name="prices")
            current_absolute_allocations[token_contract] = dex_contract_prices[token_contract] * contract_balance
            total_tau_value += current_absolute_allocations[token_contract]
        else:
            current_absolute_allocations[token_contract] = contract_balance
            total_tau_value += contract_balance
    

    return current_absolute_allocations, total_tau_value

@export
def get_metadata_allocations():
    return metadata['relative_allocations']

@export
def get_calculated_allocations():
    dex_contract = I.import_module(metadata['dex_contract'])
    relative_allocations = metadata['relative_allocations']

    # Get the current TAU value of each token
    current_absolute_allocations = get_current_tau_absolute_allocations()[0]
    total_tau_value = get_current_tau_absolute_allocations()[1]
    

    # Calculate the new allocations
    calculated_allocations = {}
    for token_contract, relative_allocation in relative_allocations.items():
        token_tau_value = current_absolute_allocations[token_contract]
        calculated_allocations[token_contract] = token_tau_value / total_tau_value

    return calculated_allocations

@export
def rebalance():
    dex_contract = I.import_module(metadata['dex_contract'])
    relative_allocations = metadata['relative_allocations']

    # Get the current TAU value of each token
    current_absolute_allocations = get_current_tau_absolute_allocations()[0]
    total_tau_value = get_current_tau_absolute_allocations()[1]

    # Calculate the desired total value of the portfolio
    desired_portfolio_value = total_tau_value 

    # Calculate the desired target value for each token (excluding "currency")
    desired_allocations = {}
    for token_contract, relative_allocation in relative_allocations.items():
        if token_contract != "currency":
            desired_allocations[token_contract] = desired_portfolio_value * relative_allocation

    # Calculate the deviations and perform a single buy or sell transaction to adjust all tokens
    for token_contract, target_value in desired_allocations.items():
        if token_contract != "currency":
            token_tau_value = current_absolute_allocations[token_contract]
            deviation = token_tau_value - target_value

            if deviation > 0.0001:
                # Sell tokens to reduce deviation
                token_contract_for_use = I.import_module(token_contract)
                token_prices = ForeignHash(foreign_contract=metadata['dex_contract'], foreign_name="prices")
                token_price = token_prices[token_contract]
                token_amount = abs(deviation) / token_price
                token_contract_for_use.approve(amount=token_amount, to=metadata['dex_contract'])
                dex_contract.sell(contract=token_contract, token_amount=token_amount)
            elif deviation < -0.0001:
                # Buy tokens to reduce deviation
                token_contract_for_use = I.import_module("currency")
                currency_amount = abs(deviation)  # "currency" is always priced at 1 TAU
                token_contract_for_use.approve(amount=currency_amount, to=metadata['dex_contract'])
                dex_contract.buy(contract=token_contract, currency_amount=currency_amount)

    return f"Rebalanced the index"

@export
def mint_index_using_tokens(index_amount: float):
    assert index_amount > 0, 'Cannot mint negative balances!'

    rebalance()

    dex_contract = I.import_module(metadata['dex_contract'])
    relative_allocations = metadata['relative_allocations']

    # Get the current TAU value of each token
    current_absolute_allocations = get_current_tau_absolute_allocations()[0]
    total_tau_value = get_current_tau_absolute_allocations()[1]

    # Transfer the tokens
    for token_contract, relative_allocation in relative_allocations.items():
        token_tau_value = current_absolute_allocations[token_contract]
        token_amount = token_tau_value / total_tau_value * index_amount
        token_contract_for_use = I.import_module(token_contract)
        token_contract_for_use.transfer_from(
                amount=token_amount,
                to=ctx.this,
                main_account=ctx.caller)
        

    # Mint the index token
    fee = index_amount * metadata['fee']
    index_amount -= fee
    balances[ctx.caller] += index_amount
    balances[metadata['fee_receiver']] += fee

    return f"Minted {index_amount} index tokens"

@export
def burn_index_to_tokens(index_amount: float):
    assert index_amount > 0, 'Cannot mint negative balances!'

    rebalance()

    dex_contract = I.import_module(metadata['dex_contract'])
    relative_allocations = metadata['relative_allocations']

    # Get the current TAU value of each token
    current_absolute_allocations = get_current_tau_absolute_allocations()[0]
    total_tau_value = get_current_tau_absolute_allocations()[1]

    # Burn the index token
    balances[ctx.caller] -= index_amount

    # Transfer the tokens
    for token_contract, relative_allocation in relative_allocations.items():
        token_tau_value = current_absolute_allocations[token_contract]
        token_amount = token_tau_value / total_tau_value * index_amount
        token_contract_for_use = I.import_module(token_contract)
        fee = token_amount * metadata['fee']
        token_amount -= fee
        token_contract_for_use.transfer(
                amount=token_amount,
                to=ctx.caller)
        token_contract_for_use.transfer(
                amount=fee,
                to=metadata['fee_receiver'])
        
    
    return f"Burned {index_amount} index tokens"


# LST002
@export
def change_metadata(key: str, value: Any):
    assert ctx.caller in metadata['operator'], 'Only an operator can set metadata!'
    metadata[key] = value

# LST001
@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'

    balances[ctx.caller] -= amount
    balances[to] += amount

# LST001
@export
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    balances[ctx.caller, to] += amount

# LST001
@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[main_account, ctx.caller] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, ctx.caller], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, ctx.caller] -= amount
    balances[main_account] -= amount
    balances[to] += amount