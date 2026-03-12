"""Release-1 domain enums."""

from enum import Enum


class ProfileRole(str, Enum):
    LEARNER = "learner"
    MENTOR = "mentor"
    BOTH = "both"


class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    MENTOR = "mentor"
    LEARNER = "learner"


class ParticipantResponseStatus(str, Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
