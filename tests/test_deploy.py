import unittest
from contracting.client import ContractingClient

class MyTestCase(unittest.TestCase):
    currency = None  
    rswp_token = None  
    rocketswap = None
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

        with open("./con_index.py") as f:
            code = f.read()
            self.c.submit(code, name="con_index")

        self.currency = self.c.get_contract("currency")
        self.rswp_token = self.c.get_contract("con_rswp_lst001")
        self.rocketswap = self.c.get_contract("con_rocketswap_official_v1_1")
        self.index_token = self.c.get_contract("con_index")
        
    def test_deploy(self):
        self.deploy_all()
        


if __name__ == "__main__":
    log = logging.getLogger("Tests")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    unittest.main()