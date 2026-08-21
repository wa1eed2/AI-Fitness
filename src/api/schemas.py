from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class UserCreateResponse(BaseModel):
    user_id: int


class UserProfileCreate(BaseModel):
    age: int = Field(gt=0)
    sex: str
    height_cm: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    fitness_level: str
    primary_goal: str
    training_days_per_week: int = Field(ge=0, le=7)
    session_duration_minutes: int = Field(gt=0)
    preferred_environment: str


class UserProfileUpdate(BaseModel):
    age: int | None = Field(default=None, gt=0)
    sex: str | None = None
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    fitness_level: str | None = None
    primary_goal: str | None = None
    training_days_per_week: int | None = Field(default=None, ge=0, le=7)
    session_duration_minutes: int | None = Field(default=None, gt=0)
    preferred_environment: str | None = None


class UserProfileResponse(BaseModel):
    profile_id: int
    user_id: int
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    fitness_level: str
    primary_goal: str
    training_days_per_week: int
    session_duration_minutes: int
    preferred_environment: str


class ExercisePreferenceCreate(BaseModel):
    exercise_id: str = Field(min_length=1)
    preference: str = Field(min_length=1)


class ExercisePreferenceResponse(BaseModel):
    user_id: int
    exercise_id: str
    preference: str


class UserLimitationCreate(BaseModel):
    body_area: str = Field(min_length=1)
    limitation_type: str = Field(min_length=1)
    notes: str | None = None


class UserLimitationResponse(BaseModel):
    limitation_id: int
    user_id: int
    body_area: str
    limitation_type: str
    notes: str | None


class EquipmentAccessCreate(BaseModel):
    equipment: str = Field(min_length=1)
    access_status: str = Field(min_length=1)


class EquipmentAccessResponse(BaseModel):
    user_id: int
    equipment: str
    access_status: str


class WorkoutExercisePlan(BaseModel):
    exercise_id: str = Field(min_length=1)
    sets: int | None = Field(default=None, gt=0)
    reps: str | int | None = None
    rest_seconds: int | None = Field(default=None, ge=0)
    duration_minutes: float | None = Field(default=None, gt=0)


class WorkoutPlanCreate(BaseModel):
    primary_goal: str | None = None
    session_duration_minutes: float | None = Field(default=None, gt=0)
    exercises: list[WorkoutExercisePlan] = Field(default_factory=list)


class WorkoutSetCreate(BaseModel):
    set_number: int = Field(gt=0)
    reps_completed: int | None = Field(default=None, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    rir_actual: int | None = Field(default=None, ge=0, le=10)
    rpe_actual: int | None = Field(default=None, ge=0, le=10)


class WorkoutSetUpdate(BaseModel):
    reps_completed: int | None = Field(default=None, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    rir_actual: int | None = Field(default=None, ge=0, le=10)
    rpe_actual: int | None = Field(default=None, ge=0, le=10)


class WorkoutFinishRequest(BaseModel):
    actual_duration_minutes: float | None = Field(default=None, ge=0)
    notes: str | None = None


class WorkoutCancelRequest(BaseModel):
    notes: str | None = None


class ProgressEntryCreate(BaseModel):
    weight_kg: float | None = Field(default=None, gt=0)
    body_fat_percentage: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class ProgressEntryUpdate(BaseModel):
    weight_kg: float | None = Field(default=None, gt=0)
    body_fat_percentage: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class BodyMeasurementCreate(BaseModel):
    body_area: str = Field(min_length=1)
    measurement_cm: float = Field(gt=0)
    notes: str | None = None


class BodyMeasurementUpdate(BaseModel):
    body_area: str | None = Field(default=None, min_length=1)
    measurement_cm: float | None = Field(default=None, gt=0)
    notes: str | None = None


class ActivityLogCreate(BaseModel):
    activity_type: str = Field(min_length=1)
    duration_minutes: float | None = Field(default=None, ge=0)
    distance_km: float | None = Field(default=None, ge=0)
    steps: int | None = Field(default=None, ge=0)
    average_speed_kmh: float | None = Field(default=None, ge=0)
    estimated_calories: float | None = Field(default=None, ge=0)
    notes: str | None = None


class ActivityLogUpdate(BaseModel):
    activity_type: str | None = Field(default=None, min_length=1)
    duration_minutes: float | None = Field(default=None, ge=0)
    distance_km: float | None = Field(default=None, ge=0)
    steps: int | None = Field(default=None, ge=0)
    average_speed_kmh: float | None = Field(default=None, ge=0)
    estimated_calories: float | None = Field(default=None, ge=0)
    notes: str | None = None


class ProgressPhotoCreate(BaseModel):
    file_path: str = Field(min_length=1)
    view_type: str = Field(min_length=1)
    is_private: bool = True
    notes: str | None = None


class ProgressPhotoUpdate(BaseModel):
    file_path: str | None = Field(default=None, min_length=1)
    view_type: str | None = Field(default=None, min_length=1)
    is_private: bool | None = None
    notes: str | None = None


class ScheduledWorkoutCreate(BaseModel):
    scheduled_for: str = Field(min_length=1)
    workout_plan: WorkoutPlanCreate
    notes: str | None = None


class ScheduledWorkoutReschedule(BaseModel):
    scheduled_for: str = Field(min_length=1)


class ScheduledWorkoutStatusUpdate(BaseModel):
    status: str = Field(min_length=1)


class ScheduledWorkoutCompleteRequest(BaseModel):
    workout_session_id: int = Field(gt=0)


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128
    )


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128
    )


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: str
    user_id: int
    email: EmailStr


class AuthUserResponse(BaseModel):
    user_id: int
    email: EmailStr
    is_active: bool
    created_at: str

class AuthSessionResponse(BaseModel):
    session_id: int
    user_id: int
    created_at: str
    expires_at: str