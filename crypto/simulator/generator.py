# simulator/generator.py
"""
Wallet address generator module with realistic address formats
"""

import random
import string
from typing import List, Optional
from enum import Enum


class AddressType(Enum):
    """Types of cryptocurrency addresses"""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    CARDANO = "cardano"
    RIPPLE = "ripple"


class WalletAddress:
    """Represents a cryptocurrency wallet address with realistic formats"""

    def __init__(self, address_type: AddressType):
        self.address_type = address_type
        self.address = self._generate_realistic_address()
        self.balance = 0.0
        self.transaction_count = 0
        self.is_active = False
        self.tags = []

    def _generate_realistic_address(self) -> str:
        """Generate realistic wallet addresses based on type"""
        if self.address_type == AddressType.BITCOIN:
            # Bitcoin: P2PKH (1...), P2SH (3...), or Bech32 (bc1...)
            formats = [
                lambda: "1" + ''.join(random.choices("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", k=33)),
                lambda: "3" + ''.join(random.choices("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", k=33)),
                lambda: "bc1q" + ''.join(random.choices("acdefghjklmnpqrstuvwxyz023456789", k=39))
            ]
            return random.choice(formats)()
            
        elif self.address_type == AddressType.ETHEREUM:
            # Ethereum: 0x + 40 hex characters
            return "0x" + ''.join(random.choices("0123456789abcdef", k=40))
            
        elif self.address_type == AddressType.SOLANA:
            # Solana: Base58 encoded, typically 32-44 chars
            chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            return ''.join(random.choices(chars, k=44))
            
        elif self.address_type == AddressType.CARDANO:
            # Cardano: addr1 + 103 chars or addr_test1 + 103 chars
            chars = "acdefghjklmnpqrstuvwxyz023456789"
            if random.random() < 0.5:
                return "addr1" + ''.join(random.choices(chars, k=103))
            else:
                return "addr_test1" + ''.join(random.choices(chars, k=103))
                
        elif self.address_type == AddressType.RIPPLE:
            # Ripple: r + 33 chars
            chars = "rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"
            return "r" + ''.join(random.choices(chars, k=33))
        
        # Fallback
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=34))

    def __str__(self):
        return f"{self.address_type.value}: {self.address[:20]}..." if len(self.address) > 20 else self.address

    def __repr__(self):
        return f"WalletAddress({self.address_type.value}, {self.address[:20]}...)"


class AddressGenerator:
    """Generates mock wallet addresses for simulation"""

    def __init__(self):
        self.random = random.Random()
        self.generated_count = 0

    def _get_random_address_type(self) -> AddressType:
        """Get a random address type based on distribution"""
        # Realistic distribution based on market cap
        distribution = {
            AddressType.BITCOIN: 0.45,      # 45% Bitcoin
            AddressType.ETHEREUM: 0.35,     # 35% Ethereum
            AddressType.SOLANA: 0.10,       # 10% Solana
            AddressType.CARDANO: 0.05,      # 5% Cardano
            AddressType.RIPPLE: 0.05,       # 5% Ripple
        }
        
        rand_val = self.random.random()
        cumulative = 0
        
        for addr_type, probability in distribution.items():
            cumulative += probability
            if rand_val <= cumulative:
                return addr_type
        
        return AddressType.BITCOIN  # Default fallback

    def _generate_balance(self, is_active: bool) -> float:
        """Generate a random balance for the wallet"""
        if not is_active:
            # Inactive wallets mostly have 0 or tiny balances
            if self.random.random() < 0.8:
                return 0.0
            else:
                return round(self.random.uniform(0.000001, 0.01), 8)
        
        # Active wallets have varied balances
        rand = self.random.random()
        
        if rand < 0.60:  # 60% small: 0.01 - 10
            return round(self.random.uniform(0.01, 10), 8)
        elif rand < 0.85:  # 25% medium: 10 - 100
            return round(self.random.uniform(10, 100), 8)
        elif rand < 0.95:  # 10% large: 100 - 1000
            return round(self.random.uniform(100, 1000), 8)
        elif rand < 0.99:  # 4% rich: 1000 - 10000
            return round(self.random.uniform(1000, 10000), 8)
        else:  # 1% whale: 10000 - 100000
            return round(self.random.uniform(10000, 100000), 8)

    def _generate_transaction_count(self, is_active: bool, balance: float) -> int:
        """Generate transaction count based on activity and balance"""
        if not is_active:
            return self.random.randint(0, 5)
        
        # Active wallets
        base_tx = 10
        
        if balance < 1:
            return base_tx + self.random.randint(0, 20)
        elif balance < 100:
            return base_tx + self.random.randint(20, 100)
        elif balance < 1000:
            return base_tx + self.random.randint(100, 500)
        else:
            return base_tx + self.random.randint(500, 2000)

    def _determine_activity(self) -> bool:
        """Determine if wallet is active based on probability"""
        from config.settings import settings
        return self.random.random() < settings.ACTIVE_PROBABILITY

    def _add_tags(self, balance: float, is_active: bool) -> List[str]:
        """Add descriptive tags to wallet"""
        tags = []
        
        if balance == 0:
            tags.append("empty")
        elif balance < 0.001:
            tags.append("dust")
        elif balance < 1:
            tags.append("small")
        elif balance < 100:
            tags.append("medium")
        elif balance < 1000:
            tags.append("large")
        elif balance < 10000:
            tags.append("rich")
        else:
            tags.append("whale")
            
        if is_active:
            tags.append("active")
        else:
            tags.append("inactive")
            
        # Add some random tags
        random_tags = ["exchange", "personal", "mining", "staking", "defi", "nft", "institutional"]
        if self.random.random() < 0.3:  # 30% chance of extra tag
            tags.append(self.random.choice(random_tags))
            
        return tags

    def generate(self) -> WalletAddress:
        """Generate a single wallet address with random properties"""
        # Generate address type
        addr_type = self._get_random_address_type()
        wallet = WalletAddress(addr_type)

        # Determine if active
        wallet.is_active = self._determine_activity()
        
        # Generate balance based on activity
        wallet.balance = self._generate_balance(wallet.is_active)
        
        # Generate transaction count
        wallet.transaction_count = self._generate_transaction_count(wallet.is_active, wallet.balance)
        
        # Add tags
        wallet.tags = self._add_tags(wallet.balance, wallet.is_active)

        self.generated_count += 1
        return wallet

    def generate_all(self, count: Optional[int] = None) -> List[WalletAddress]:
        """Generate multiple wallet addresses"""
        from config.settings import settings
        
        num_addresses = count or settings.NUM_ADDRESSES
        addresses = []
        
        print(f"Generating {num_addresses} addresses...")
        
        for i in range(num_addresses):
            addresses.append(self.generate())

        return addresses  # simulator/generator.py
"""
Wallet address generator module with seed phrase support
"""

import random
import string
from typing import List, Optional
from enum import Enum
from mnemonic import Mnemonic  # Add this import


class AddressType(Enum):
    """Types of cryptocurrency addresses"""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    CARDANO = "cardano"
    RIPPLE = "ripple"


class WalletAddress:
    """Represents a cryptocurrency wallet with seed phrase"""

    def __init__(self, address_type: AddressType):
        self.generated_count = None
        self.address_type = address_type
        self.seed_phrase = self._generate_seed_phrase()  # Generate seed phrase first
        self.address = self._generate_address_from_seed()  # Generate address from seed
        self.balance = 0.0
        self.transaction_count = 0
        self.is_active = False
        self.tags = []

    @staticmethod
    def _generate_seed_phrase() -> str:
        """Generate a 24-word BIP39 seed phrase"""
        mnemo = Mnemonic("english")

        # Generate 256 bits of entropy (32 bytes) for 24 words
        entropy = random.randbytes(32)
        seed_phrase = mnemo.to_mnemonic(entropy)

        return seed_phrase

    def _generate_address_from_seed(self) -> str:
        """Generate a deterministic address from the seed phrase"""
        # In a real implementation, you'd derive addresses from the seed phrase
        # For simulation, we'll create a hash-based deterministic address

        import hashlib

        # Create a deterministic address based on seed phrase and wallet type
        seed_hash = hashlib.sha256(self.seed_phrase.encode()).hexdigest()

        if self.address_type == AddressType.BITCOIN:
            # Bitcoin-style address from hash
            return "bc1q" + seed_hash[:40]
        elif self.address_type == AddressType.ETHEREUM:
            # Ethereum-style address from hash
            return "0x" + seed_hash[:40]
        elif self.address_type == AddressType.SOLANA:
            # Solana-style address (base58)
            chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            return ''.join(random.choices(chars, k=44))
        elif self.address_type == AddressType.CARDANO:
            # Cardano-style address
            return "addr1" + seed_hash[:103].lower()
        elif self.address_type == AddressType.RIPPLE:
            # Ripple-style address
            chars = "rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"
            return "r" + ''.join(random.choices(chars, k=33))

        return seed_hash[:34]  # Fallback

    def get_formatted_seed_phrase(self) -> str:
        """Format seed phrase for display"""
        words = self.seed_phrase.split()
        # Format in 4 columns of 6 words each
        lines = []
        for i in range(0, 24, 6):
            line_words = words[i:i+6]
            line = "  ".join(f"{i+j+1:2}. {word:<8}" for j, word in enumerate(line_words))
            lines.append(line)
        return "\n".join(lines)

    def get_short_seed_phrase(self) -> str:
        """Get a shortened version of seed phrase for compact display"""
        words = self.seed_phrase.split()
        # Show first 4 and last 4 words with ellipsis
        first_four = " ".join(words[:4])
        last_four = " ".join(words[-4:])
        return f"{first_four} ... {last_four}"

    def __str__(self):
        return f"{self.address_type.value}: {self.get_short_seed_phrase()}"

    def __repr__(self):
        return f"WalletAddress({self.address_type.value}, {self.seed_phrase[:20]}...)"


# ... [rest of the AddressGenerator class remains the same, but update the _generate_address_from_seed method]

    def reset_counter(self):
        """Reset the generation counter"""
        self.generated_count = 0