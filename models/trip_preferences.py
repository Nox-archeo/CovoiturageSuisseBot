from enum import Enum

class Smoking(Enum):
    NO = "no_smoking"
    YES = "smoking_allowed"
    OUTSIDE = "smoking_outside"

class Music(Enum):
    NO = "no_music"
    YES = "music_ok"
    QUIET = "quiet_music"

class TalkPreference(Enum):
    QUIET = "quiet"
    CHATTY = "chatty"
    DEPENDS = "depends"

class PetsAllowed(Enum):
    NO = "no_pets"
    YES = "pets_ok"
    SMALL = "small_pets"

class LuggageSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
