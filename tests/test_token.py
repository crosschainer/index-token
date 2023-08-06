import unittest
from contracting.client import ContractingClient
import os 
import random

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class DeployToken(unittest.TestCase):
    currency = None  
    rswp_token = None  
    rocketswap = None
    yeti = None
    index_token = None
    

    def deploy_all(self):
        self.c= ContractingClient()
        self.c.flush()
        self.c.signer = "ff61544ea94eaaeb5df08ed863c4a938e9129aba6ceee5f31b6681bdede11b89"

        with open("./currency.py") as f:
            code = f.read()
            self.c.submit(code, name="currency")

        with open("./con_rswp_lst001.py") as f:
            code = f.read()
            self.c.submit(code, name="con_rswp_lst001")

        with open("./con_rocketswap_official_v1_1.py") as f:
            code = f.read()
            self.c.submit(code, name="con_rocketswap_official_v1_1")

        with open("./con_yeti.py") as f:
            code = f.read()
            self.c.submit(code, name="con_yeti")

        self.currency = self.c.get_contract("currency")
        self.rswp_token = self.c.get_contract("con_rswp_lst001")
        self.rocketswap = self.c.get_contract("con_rocketswap_official_v1_1")
        self.yeti = self.c.get_contract("con_yeti")


        with open("../con_index.py") as f:
            code = f.read()
            self.c.submit(code, name="con_index")

        self.index_token = self.c.get_contract("con_index")


    def create_pair(self):
        self.currency.approve(amount=1_000_000_000, to="con_rocketswap_official_v1_1")
        self.rswp_token.approve(amount=1_000_000_000, to="con_rocketswap_official_v1_1")
        self.yeti.approve(amount=1_000_000_000, to="con_rocketswap_official_v1_1")
        self.rocketswap.create_market(
            contract="con_rswp_lst001",
            currency_amount=5_000_000,
            token_amount=75_000_000,
        )
        self.rocketswap.create_market(
            contract="con_yeti",
            currency_amount=500_000,
            token_amount=500_000_000,
        )
        
    def test_deploy(self):
        self.deploy_all()

    def test_mint_index(self):
        self.deploy_all()
        self.create_pair()
        self.currency.approve(amount=100_000_000, to="con_index")
        self.rswp_token.approve(amount=100_000_000, to="con_index")
        self.yeti.approve(amount=100_000_000, to="con_index")
        print(self.index_token.get_calculated_allocations())
        self.index_token.rebalance()
        self.rocketswap.buy(contract="con_rswp_lst001", currency_amount=10000)
        random_amount = random.randint(1, 300)
        random_amount_2 = random.randint(1,random_amount)
        for _ in range(random_amount):
            self.index_token.mint_index_using_tokens(index_amount=110)
            print(self.index_token.get_calculated_allocations())
        self.rocketswap.sell(contract="con_rswp_lst001", token_amount=2230000)
        print(self.index_token.get_calculated_allocations())
        self.rocketswap.buy(contract="con_rswp_lst001", currency_amount=10000)

        for _ in range(random_amount_2):
            self.index_token.burn_index_to_tokens(index_amount=110)
        print(self.index_token.get_calculated_allocations())
        random_amount = random.randint(1, 300)
        random_amount_2 = random.randint(1,random_amount)
        for _ in range(random_amount):
            self.index_token.mint_index_using_tokens(index_amount=110)
            print(self.index_token.get_calculated_allocations())
        self.rocketswap.sell(contract="con_rswp_lst001", token_amount=2230000)
        print(self.index_token.get_calculated_allocations())
        self.rocketswap.buy(contract="con_rswp_lst001", currency_amount=10000)
        for _ in range(random_amount_2):
            self.index_token.burn_index_to_tokens(index_amount=110)
            print(self.index_token.get_calculated_allocations())
        print(self.index_token.get_calculated_allocations())
        for _ in range(100):
            self.index_token.rebalance()
            print(self.index_token.get_calculated_allocations())
        print(self.index_token.get_calculated_allocations())
        
       


if __name__ == "__main__":
    unittest.main()