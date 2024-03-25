from .types import ReciterName, Reciter


def get_reciter_config(name: ReciterName) -> Reciter:
    """
    names: Sa'ud ash-Shuraim, Mahmoud Khalil Al-Husary
    """
    if name == "Sa'ud ash-Shuraim":
        return Reciter(name=name, id=4, silence_threshold=8)
    if name == "Mahmoud Khalil Al-Husary":
        return Reciter(name=name, id=5, silence_threshold=8)
