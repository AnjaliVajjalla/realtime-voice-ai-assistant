import random

# DO NOT MEMORIZE: just word lists, expand them anytime.
ADJECTIVES = [
    "Silly", "Goofy", "Sneaky", "Fuzzy", "Bouncy", "Clever", "Sleepy",
    "Wild", "Curious", "Brave", "Grumpy", "Chatty", "Dizzy", "Cheerful",
    "Mighty", "Speedy", "Cozy", "Sassy", "Jolly", "Quirky",
]

ANIMALS = [
    "Raccoon", "Hamster", "Otter", "Penguin", "Fox", "Panda", "Koala",
    "Llama", "Hedgehog", "Platypus", "Squirrel", "Walrus", "Ferret",
    "Armadillo", "Narwhal", "Wombat", "Toucan", "Gecko", "Badger", "Moose",
]


def generate_chat_name() -> str:
    """A random, memorable name for a chat, e.g. 'Silly Raccoon',
    instead of a boring timestamp. Purely cosmetic, has no effect on
    the actual saved data."""
    return f"{random.choice(ADJECTIVES)} {random.choice(ANIMALS)}"
