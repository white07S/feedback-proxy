# feedback_router.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import db
import config
from schemas import (
    FeedbackCreate, FeedbackUpdate, FeedbackOut,
    CommentCreate, CommentOut, FeedbackListOut, ProjectOut
)

router = APIRouter(prefix="/api", tags=["feedback"])

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/projects", response_model=list[ProjectOut])
def list_projects():
    with db.get_con() as con:
        rows = list(db.query(con, "SELECT key,name,active FROM projects WHERE active=1 ORDER BY name;"))
    return [{"key": r["key"], "name": r["name"], "active": bool(r["active"])} for r in rows]

@router.post("/feedback", response_model=FeedbackOut)
def create_feedback(payload: FeedbackCreate):
    # enforce developer-controlled projects
    allowed = {p["key"] for p in config.ALLOWED_PROJECTS}
    if payload.project_key not in allowed:
        raise HTTPException(400, f"Project '{payload.project_key}' is not allowed.")

    if payload.type not in config.FEEDBACK_TYPES:
        raise HTTPException(400, "Invalid type.")
    if payload.severity and payload.severity not in config.SEVERITIES:
        raise HTTPException(400, "Invalid severity.")

    now = db.now_iso()
    with db.get_con() as con, con:
        con.execute("""
          INSERT INTO feedback (project_key,type,title,description,severity,status,created_by,created_at,updated_at)
          VALUES (?,?,?,?,?,'open',?,?,?);
        """, (payload.project_key, payload.type, payload.title, payload.description, payload.severity,
              payload.created_by, now, now))
        fid = db.scalar(con, "SELECT last_insert_rowid();")
        row = next(db.query(con, "SELECT * FROM feedback WHERE id=?;", (fid,)))
    return row  # keys match FeedbackOut

@router.get("/feedback", response_model=FeedbackListOut)
def list_feedback(
    project_key: Optional[str] = None,
    status: Optional[str] = None,
    ftype: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = config.PAGE_SIZE_DEFAULT,
    sort: str = "-created_at"  # '-created_at' or 'created_at' etc.
):
    if page_size > config.PAGE_SIZE_MAX:
        page_size = config.PAGE_SIZE_MAX

    clauses, params = [], []
    if project_key:
        clauses.append("project_key=?"); params.append(project_key)
    if status:
        clauses.append("status=?"); params.append(status)
    if ftype:
        clauses.append("type=?"); params.append(ftype)
    if search:
        clauses.append("(title LIKE ? OR description LIKE ?)"); params.extend([f"%{search}%", f"%{search}%"])

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    order = "created_at DESC" if sort.startswith("-") else "created_at ASC"

    with db.get_con() as con:
        total = db.scalar(con, f"SELECT COUNT(*) FROM feedback {where};", params) or 0
        offset = (page - 1) * page_size
        items = list(db.query(con, f"""
            SELECT * FROM feedback {where}
            ORDER BY {order}
            LIMIT ? OFFSET ?;
        """, (*params, page_size, offset)))
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/feedback/{fid}", response_model=FeedbackOut)
def get_feedback(fid: int):
    with db.get_con() as con:
        row = next(db.query(con, "SELECT * FROM feedback WHERE id=?;", (fid,)), None)
    if not row:
        raise HTTPException(404, "Not found")
    return row

@router.patch("/feedback/{fid}", response_model=FeedbackOut)
def update_feedback(fid: int, payload: FeedbackUpdate):
    fields, params = [], []
    if payload.status:
        if payload.status not in config.STATUSES:
            raise HTTPException(400, "Invalid status")
        fields.append("status=?"); params.append(payload.status)
    if payload.assignee is not None:
        fields.append("assignee=?"); params.append(payload.assignee)
    if payload.resolution is not None:
        fields.append("resolution=?"); params.append(payload.resolution)
    if payload.title is not None:
        fields.append("title=?"); params.append(payload.title)
    if payload.description is not None:
        fields.append("description=?"); params.append(payload.description)
    if payload.severity is not None:
        if payload.severity not in config.SEVERITIES:
            raise HTTPException(400, "Invalid severity")
        fields.append("severity=?"); params.append(payload.severity)

    if not fields:
        raise HTTPException(400, "Nothing to update")

    params.extend([db.now_iso(), fid])
    with db.get_con() as con, con:
        cur = con.execute(f"UPDATE feedback SET {', '.join(fields)}, updated_at=? WHERE id=?;", params)
        if cur.changes() == 0:
            raise HTTPException(404, "Not found")
        row = next(db.query(con, "SELECT * FROM feedback WHERE id=?;", (fid,)))
    return row

@router.post("/feedback/{fid}/comments", response_model=CommentOut)
def add_comment(fid: int, payload: CommentCreate):
    now = db.now_iso()
    with db.get_con() as con, con:
        # ensure feedback exists
        exists = db.scalar(con, "SELECT 1 FROM feedback WHERE id=?;", (fid,))
        if not exists:
            raise HTTPException(404, "Feedback not found")
        con.execute("""
        INSERT INTO comments (feedback_id, body, created_by, created_at)
        VALUES (?,?,?,?);
        """, (fid, payload.body, payload.created_by, now))
        cid = db.scalar(con, "SELECT last_insert_rowid();")
        row = next(db.query(con, "SELECT * FROM comments WHERE id=?;", (cid,)))
    return row

@router.get("/feedback/{fid}/comments", response_model=list[CommentOut])
def list_comments(fid: int):
    with db.get_con() as con:
        rows = list(db.query(con, "SELECT * FROM comments WHERE feedback_id=? ORDER BY created_at ASC;", (fid,)))
    return rows