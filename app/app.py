"""Startup uvicorn config"""
import json
import uuid
from typing import Annotated

from fastapi import FastAPI, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import FileResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CourseRef(BaseModel):
    """Course create and update entity"""
    title: str | None
    description: str | None
    teacher_id: int | None
    age_from: int | None
    age_to: int | None
    requirements: str | None
    price: float | None
    image_id: str | None
    docs_ids: str | None
    is_submitted: bool = False
    times: list[str] | None
    specialization: str | None


class Course(CourseRef):
    """Course entity"""
    id: int


storage: list[CourseRef | None] = []

try:
    with open("data.json", "r") as f:
        for i in json.load(f):
            if i is not None:
                storage.append(CourseRef(**i))
            else:
                storage.append(None)
except FileNotFoundError:
    pass


@app.on_event("shutdown")
def save_storage():
    json.dump(
        list(map(lambda x: x is not None and x.dict() or x, storage)),
        open("data.json", "w"),
    )


@app.get("/courses/", response_model=list[Course])
async def get_courses() -> list[Course]:
    return [
        Course(id=index, **course.dict())
        for index, course in enumerate(storage)
        if course is not None
    ]


@app.post("/courses/", response_model=Course)
async def create_course(ref: CourseRef):
    storage.append(ref)

    return Course(
        id=len(storage) - 1,
        **ref.dict(),
    )


@app.get("/courses/{course_id}/", response_model=Course)
async def get_course_by_id(course_id: int) -> Course:
    if len(storage) > course_id and storage[course_id] is not None:
        return Course(id=course_id, **storage[course_id].dict())
    else:
        raise HTTPException(status_code=404, detail="Course not found")


@app.patch("/courses/{course_id}/", status_code=204)
async def update_course_by_id(course_id: int, upd_ref: CourseRef):
    for key in upd_ref.dict(exclude_none=True, exclude_unset=True).keys():
        if getattr(upd_ref, key, None) is not None:
            setattr(storage[course_id], key, getattr(upd_ref, key))


@app.delete("/courses/{course_id}/", status_code=204)
async def delete_course_by_id(course_id: int):
    storage[course_id] = None


@app.post("/files/")
async def upload_file(file: Annotated[bytes, File()]):
    id_ = uuid.uuid4()

    with open(f"{id_}", "wb") as f:
        f.write(file)

    return id_


@app.get("/files/{file_id}")
async def upload_file(file_id: uuid.UUID):
    return FileResponse(f"{file_id}")
