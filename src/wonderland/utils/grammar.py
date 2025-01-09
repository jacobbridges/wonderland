def aan(word: str) -> str:
    """
    Pick the appropriate article ('a' or 'an') for the given word.

    :param word: The word to pick an article for.
    :return: The article for the given word.
    """
    for vowel in "aeiou":
        if word.startswith(vowel):
            return "an"
    return "a"
