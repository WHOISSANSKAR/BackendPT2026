from pydantic import BaseModel, Field


class ProjectLocationCreate(BaseModel):
    country: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=255)
    pincode: str = Field(default="", max_length=255)
    address: str = Field(default="", max_length=400)
    status: str = Field(default="Not Started", max_length=20)

    pscope_startdate: str | None = None
    pscope_enddate: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    startDate: str | None = None
    endDate: str | None = None

    add_weightage: bool = False
    pscope_weightage: float | None = Field(default=None, ge=0, le=100)

    def resolved_start_date(self) -> str | None:
        return self.pscope_startdate or self.start_date or self.startDate

    def resolved_end_date(self) -> str | None:
        return self.pscope_enddate or self.end_date or self.endDate


class ProjectLocationUpdate(BaseModel):
    country: str | None = Field(default=None, min_length=1, max_length=255)
    state: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=255)
    pincode: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=400)
    status: str | None = Field(default=None, max_length=20)

    pscope_startdate: str | None = None
    pscope_enddate: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    startDate: str | None = None
    endDate: str | None = None

    add_weightage: bool | None = None
    pscope_weightage: float | None = Field(default=None, ge=0, le=100)

    def has_start_date_update(self) -> bool:
        return any(
            field in self.model_fields_set
            for field in ("pscope_startdate", "start_date", "startDate")
        )

    def has_end_date_update(self) -> bool:
        return any(
            field in self.model_fields_set
            for field in ("pscope_enddate", "end_date", "endDate")
        )

    def resolved_start_date(self) -> str | None:
        return self.pscope_startdate or self.start_date or self.startDate

    def resolved_end_date(self) -> str | None:
        return self.pscope_enddate or self.end_date or self.endDate


class ProjectLocationOut(BaseModel):
    id: str
    pscope_id: int
    pscope_project_id: int
    country: str
    state: str
    city: str
    pincode: str
    address: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    pscope_startdate: str | None = None
    pscope_enddate: str | None = None
    weightage: float | None = None
    addWeightage: bool = False
    status: str | None = None
    createdOn: str | None = None


class ProjectLocationListResponse(BaseModel):
    success: bool = True
    total: int
    locations: list[ProjectLocationOut]


class LocationWeightageSummaryResponse(BaseModel):
    success: bool = True
    total_weightage: float
    remaining_weightage: float
    entered_weightage: float | None = None
    projected_total_weightage: float | None = None
    remaining_after_add: float | None = None
    exceeds_limit: bool = False


class LocationImportResponse(BaseModel):
    success: bool = True
    message: str
    imported_count: int