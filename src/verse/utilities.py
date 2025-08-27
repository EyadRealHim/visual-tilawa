from .types import ReciterName, Reciter


_RECITERS = {
    "AbdulBaset AbdulSamad": 1,
    "Abdur-Rahman as-Sudais": 2,
    "Abu Bakr al-Shatri": 3,
    "Hani ar-Rifai": 4,
    "Mahmoud Khalil Al-Husary": 5,
    "Mishari Rashid al-`Afasy": 6,
    "Mohamed Siddiq al-Minshawi": 7,
    "Sa'ud ash-Shuraim": 8,
    "Khalifah Al Tunaiji": 11,
    "Sa'ad al-Ghamdi": 12,
    "Yasser Ad Dussary": 20,
    "Ahmed ibn Ali al-Ajmy": 22,
    "Abdullah Ali Jabir": 23,
    "Bandar Baleela": 24,
    "Maher al-Muaiqly": 25,
    "Abdullah Hamad Abu Sharida": 26,
}


def get_reciter_config(name: ReciterName) -> Reciter:
    try:
        return Reciter(name=name, id=_RECITERS[name], silence_threshold=8)
    except KeyError:
        raise ValueError(f"Unsupported reciter: {name}")
