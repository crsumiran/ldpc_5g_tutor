import json
import queue
import threading
import shutil
from datetime import timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.db import SessionLocal
from app.config import settings
from app.jobs import create_job, run_job
from app.llm import complete, list_available_free_models, openrouter_error_status
from app.opencode import complete as opencode_complete, OpenCodeError, OpenCodeCancelled
from app.models import Job, LabMessage, LabRun, LabSession
from app.verilog.manifest import get_checkpoint, load_course, validate_manifest
from app.verilog.runner import run_checkpoint, source_hash
from app.verilog.schemas import (
    CheckpointProgress,
    CourseManifest,
    CourseResponse,
    FileUpdate,
    LabMessageResponse,
    LabRunRequest,
    LabRunResult,
    LabSessionResponse,
    TutorRequest,
)
from app.verilog.tutor import get_tutor_reply
from app.verilog.waveform import response_pulses
from app.verilog.workspace import (
    allowed_editable_files,
    ensure_lab_workspace_assets,
    lab_artifact_dir,
    lab_workspace_dir,
    materialize_lab_workspace,
    progress_ids,
    progress_json,
    read_workspace_file,
    write_workspace_file,
)


router = APIRouter(prefix="/api", tags=["labs"])


@router.get("/openrouter/models")
def available_guide_models(
    openrouter_api_key: str | None = Header(default=None, alias="X-OpenRouter-Api-Key", max_length=512),
):
    key = openrouter_api_key.strip() if openrouter_api_key else settings.openrouter_api_key
    if not key:
        raise HTTPException(status_code=400, detail="Enter an OpenRouter key in AI settings first.")
    try:
        return {"models": list_available_free_models(key), "key_source": "entered" if openrouter_api_key else "server"}
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=openrouter_error_status(exc)) from None


class SessionRequest(BaseModel):
    learner_key: str = Field(default="local", min_length=1, max_length=128)


class OpenRouterTestRequest(BaseModel):
    model: str | None = Field(default=None, min_length=1, max_length=160, pattern=r"^[A-Za-z0-9._:/-]+$")
    allow_model_fallbacks: bool = True


@router.post("/openrouter/test")
def test_openrouter_connection(
    body: OpenRouterTestRequest,
    openrouter_api_key: str | None = Header(default=None, alias="X-OpenRouter-Api-Key", max_length=512),
):
    key = openrouter_api_key.strip() if openrouter_api_key else settings.openrouter_api_key
    if not key:
        raise HTTPException(status_code=400, detail="Enter an OpenRouter key in AI settings first.")
    requested_model = body.model or settings.tutor_model
    configured = [item.strip() for item in settings.tutor_fallback_models.split(",") if item.strip()]
    fallbacks = [item for item in configured if item != requested_model] if body.allow_model_fallbacks else []
    try:
        if settings.tutor_engine == "opencode":
            response = opencode_complete(
                messages=[{"role": "user", "content": "Reply with exactly OK."}],
                model=requested_model, fallback_models=fallbacks, api_key=key,
            )
        else:
            response = complete(
                messages=[{"role": "user", "content": "Reply with exactly OK."}],
                model=requested_model, fallback_models=fallbacks,
                include_model=True, temperature=0, api_key=key, max_tokens=256,
            )
    except Exception as exc:
        detail = str(exc) if isinstance(exc, OpenCodeError) else openrouter_error_status(exc, requested_model)
        raise HTTPException(status_code=502, detail=detail) from None

    served_model = str(response.get("_served_model") or requested_model)
    content = response.get("content")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter returned no answer text from {served_model}; try another model or check its provider availability.",
        )
    return {
        "ok": True,
        "requested_model": requested_model,
        "served_model": served_model,
        "fallback_used": served_model != requested_model,
        "key_source": "entered" if openrouter_api_key else "server",
        "engine": settings.tutor_engine,
    }


def _checkpoint_progress(manifest, passed: set[str]) -> list[CheckpointProgress]:
    result = []
    for checkpoint in manifest.checkpoints:
        if checkpoint.id in passed:
            status = "passed"
        elif all(prerequisite in passed for prerequisite in checkpoint.prerequisites):
            status = "available"
        else:
            status = "locked"
        result.append(
            CheckpointProgress(
                id=checkpoint.id,
                title=checkpoint.title,
                goal=checkpoint.goal,
                status=status,
                estimated_minutes=checkpoint.estimated_minutes,
                difficulty=checkpoint.difficulty,
                concepts=checkpoint.concepts,
            )
        )
    return result


def _session_response(session: LabSession, manifest) -> LabSessionResponse:
    passed = progress_ids(session.progress_json)
    return LabSessionResponse(
        id=session.id,
        course_id=session.course_id,
        learner_key=session.learner_key,
        passed_checkpoint_ids=sorted(passed),
        checkpoints=_checkpoint_progress(manifest, passed),
        created_at=str(session.created_at),
        updated_at=str(session.updated_at),
    )


def _course_response(manifest, root: Path, session_id: str | None = None) -> CourseResponse:
    from app.ldpc.theory import load_theory
    return CourseResponse(
        manifest=manifest,
        overview=(root / manifest.overview_file).read_text(encoding="utf-8"),
        architecture=(root / manifest.architecture_file).read_text(encoding="utf-8"),
        theory_pages=load_theory(root) if (root / "theory.json").is_file() else [],
        session_id=session_id,
        progress=_checkpoint_progress(manifest, set()),
    )


@router.get("/courses")
def list_courses():
    curriculum_root = Path(settings.curriculum_dir)
    if not curriculum_root.is_dir():
        return []
    courses = []
    for child in sorted(curriculum_root.iterdir()):
        if child.is_dir() and (child / "manifest.json").is_file():
            try:
                manifest = CourseManifest.model_validate(json.loads((child / "manifest.json").read_text(encoding="utf-8")))
                validate_manifest(manifest, child)
                courses.append({"id": manifest.id, "title": manifest.title, "subtitle": manifest.subtitle, "checkpoint_count": len(manifest.checkpoints)})
            except (OSError, ValueError):
                continue
    return courses


@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: str):
    try:
        manifest, root = load_course(course_id)
        return _course_response(manifest, root)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/courses/{course_id}/sessions", response_model=LabSessionResponse)
def create_lab_session(course_id: str, body: SessionRequest):
    try:
        manifest, root = load_course(course_id)
        session_id, workspace = materialize_lab_workspace(root, manifest)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    db = SessionLocal()
    try:
        session = LabSession(id=session_id, course_id=course_id, learner_key=body.learner_key, workspace_path=str(workspace), progress_json=progress_json(set()))
        db.add(session)
        db.commit()
        db.refresh(session)
        return _session_response(session, manifest)
    finally:
        db.close()


def _get_session(db, session_id: str) -> LabSession:
    session = db.query(LabSession).filter(LabSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Lab session not found")
    return session


def _get_manifest_for_session(session: LabSession):
    try:
        manifest, root = load_course(session.course_id)
        ensure_lab_workspace_assets(root, manifest, Path(session.workspace_path))
        return manifest, root
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/lab-sessions/{session_id}", response_model=LabSessionResponse)
def get_lab_session(session_id: str):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, _ = _get_manifest_for_session(session)
        return _session_response(session, manifest)
    finally:
        db.close()


def _viewable_paths(manifest) -> list[str]:
    paths = set(manifest.provided_files)
    for checkpoint in manifest.checkpoints:
        paths.update(checkpoint.source_files)
    return sorted(paths)


@router.get("/lab-sessions/{session_id}/files")
def list_lab_files(session_id: str):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, _ = _get_manifest_for_session(session)
        passed = progress_ids(session.progress_json)
        current = next((c for c in manifest.checkpoints if all(p in passed for p in c.prerequisites) and c.id not in passed), manifest.checkpoints[-1])
        editable = allowed_editable_files(manifest, passed, current.id)
        return [{"path": path, "content": read_workspace_file(Path(session.workspace_path), path), "editable": path in editable} for path in _viewable_paths(manifest)]
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


@router.get("/lab-sessions/{session_id}/files/{file_path:path}")
def get_lab_file(session_id: str, file_path: str):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, _ = _get_manifest_for_session(session)
        if file_path not in _viewable_paths(manifest):
            raise HTTPException(status_code=404, detail="File is not learner-visible")
        return {"path": file_path, "content": read_workspace_file(Path(session.workspace_path), file_path)}
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


@router.put("/lab-sessions/{session_id}/files/{file_path:path}")
def update_lab_file(session_id: str, file_path: str, body: FileUpdate):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, _ = _get_manifest_for_session(session)
        passed = progress_ids(session.progress_json)
        checkpoint_id = next((c.id for c in manifest.checkpoints if c.id not in passed and all(p in passed for p in c.prerequisites)), manifest.checkpoints[-1].id)
        if file_path not in allowed_editable_files(manifest, passed, checkpoint_id):
            raise HTTPException(status_code=403, detail="File is read-only until its checkpoint is unlocked")
        write_workspace_file(Path(session.workspace_path), file_path, body.content)
        return {"path": file_path, "saved": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


def _run_lab_job(run_id: str, session_id: str, course_id: str, checkpoint_id: str, mode: str):
    db = SessionLocal()
    try:
        run = db.query(LabRun).filter(LabRun.id == run_id).first()
        session = db.query(LabSession).filter(LabSession.id == session_id).first()
        if not run or not session:
            raise ValueError("Lab run or session not found")
        run.status = "running"
        db.commit()
        _, course_root = load_course(course_id)
        manifest, _ = load_course(course_id)
        run_source = lab_artifact_dir(run_id) / "source" if manifest.toolchain == "python" else Path(session.workspace_path)
        result = run_checkpoint(course_root, run_source, checkpoint_id, mode, lab_artifact_dir(run_id))
        for artifact in result.artifacts:
            artifact.url = f"/api/lab-runs/{run_id}/artifacts/{artifact.name}"
        run.result_json = result.model_dump_json()
        run.status = "done"
        run.artifact_path = str(lab_artifact_dir(run_id))
        if mode == "submit" and result.passed:
            passed = progress_ids(session.progress_json)
            passed.add(checkpoint_id)
            session.progress_json = progress_json(passed)
        db.commit()
        return {"run_id": run_id, "result": result.model_dump()}
    except Exception:
        run = db.query(LabRun).filter(LabRun.id == run_id).first()
        if run:
            run.status = "error"
            db.commit()
        raise
    finally:
        db.close()


@router.post("/lab-sessions/{session_id}/runs")
def start_lab_run(session_id: str, body: LabRunRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, course_root = _get_manifest_for_session(session)
        checkpoint = get_checkpoint(manifest, body.checkpoint_id)
        passed = progress_ids(session.progress_json)
        if not all(prerequisite in passed for prerequisite in checkpoint.prerequisites):
            raise HTTPException(status_code=403, detail="Checkpoint is locked")
        active = db.query(LabRun).filter(LabRun.session_id == session_id, LabRun.status.in_(["queued", "running"])).first()
        if active:
            raise HTTPException(status_code=409, detail="Another run is already active")
        run = LabRun(session_id=session_id, checkpoint_id=body.checkpoint_id, mode=body.mode, source_hash=source_hash(Path(session.workspace_path), checkpoint.source_files))
        db.add(run)
        db.flush()
        if manifest.toolchain == "python":
            snapshot = lab_artifact_dir(run.id) / "source"
            snapshot.mkdir(parents=True)
            for relative in checkpoint.source_files:
                origin = Path(session.workspace_path) / relative
                if origin.is_symlink() or not origin.resolve().is_relative_to(Path(session.workspace_path).resolve()):
                    raise HTTPException(status_code=400, detail="Unsafe source path")
                destination = snapshot / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, destination)
            run.source_hash = source_hash(snapshot, checkpoint.source_files)
        job = create_job(f"lab_{body.mode}", db=db)
        db.commit()
        background_tasks.add_task(run_job, job.id, _run_lab_job, run.id, session_id, session.course_id, body.checkpoint_id, body.mode)
        return {"run_id": run.id, "job_id": job.id, "status": "queued"}
    finally:
        db.close()


def _run_payload(run: LabRun) -> dict:
    result = json.loads(run.result_json) if run.result_json else None
    if result and result.get("artifacts"):
        for artifact in result["artifacts"]:
            artifact["url"] = f"/api/lab-runs/{run.id}/artifacts/{artifact['name']}"
    return {"id": run.id, "checkpoint_id": run.checkpoint_id, "mode": run.mode, "status": run.status, "source_hash": run.source_hash, "result": result}


@router.get("/lab-runs/{run_id}")
def get_lab_run(run_id: str):
    db = SessionLocal()
    try:
        run = db.query(LabRun).filter(LabRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Lab run not found")
        return _run_payload(run)
    finally:
        db.close()


@router.get("/lab-runs/{run_id}/artifacts/{artifact_name}")
def get_lab_artifact(run_id: str, artifact_name: str):
    if Path(artifact_name).name != artifact_name or artifact_name not in {"wave.vcd", "public-report.json"}:
        raise HTTPException(status_code=404, detail="Artifact not found")
    db = SessionLocal()
    try:
        run = db.query(LabRun).filter(LabRun.id == run_id).first()
        if not run or run.status != "done" or not run.artifact_path:
            raise HTTPException(status_code=404, detail="Artifact not found")
        path = Path(run.artifact_path) / artifact_name
        registered = json.loads(run.result_json or "{}").get("artifacts", [])
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 20 * 1024 * 1024 or not any(a.get("name") == artifact_name for a in registered):
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(path, media_type="application/octet-stream", filename=artifact_name)
    finally:
        db.close()


@router.get("/lab-sessions/{session_id}/messages", response_model=list[LabMessageResponse])
def get_lab_messages(session_id: str):
    db = SessionLocal()
    try:
        _get_session(db, session_id)
        messages = db.query(LabMessage).filter(LabMessage.session_id == session_id).order_by(LabMessage.created_at.asc()).all()
        return [LabMessageResponse(id=m.id, role=m.role, content=m.content, hint_level=int(m.hint_level), run_id=m.run_id, created_at=str(m.created_at)) for m in messages]
    finally:
        db.close()


@router.post("/lab-sessions/{session_id}/tutor")
def tutor_for_lab(
    session_id: str,
    body: TutorRequest,
    openrouter_api_key: str | None = Header(default=None, alias="X-OpenRouter-Api-Key", max_length=512),
):
    return _tutor_for_lab(session_id, body, openrouter_api_key)


def _tutor_for_lab(session_id, body, openrouter_api_key, on_status=None):
    db = SessionLocal()
    try:
        session = _get_session(db, session_id)
        manifest, course_root = _get_manifest_for_session(session)
        checkpoint = get_checkpoint(manifest, body.checkpoint_id)
        passed = progress_ids(session.progress_json)
        if not all(prerequisite in passed for prerequisite in checkpoint.prerequisites):
            raise HTTPException(status_code=403, detail="Checkpoint is locked")
        workspace = Path(session.workspace_path)
        student_files = {path: read_workspace_file(workspace, path) for path in checkpoint.source_files if (workspace / path).is_file()}
        reference_files = {}
        for path in checkpoint.source_files:
            reference_path = course_root / "reference" / path
            if reference_path.is_file():
                reference_files[path] = reference_path.read_text(encoding="utf-8")
        run_query = db.query(LabRun).filter(
            LabRun.session_id == session_id,
            LabRun.checkpoint_id == body.checkpoint_id,
            LabRun.status == "done",
        )
        run = run_query.filter(LabRun.id == body.run_id).first() if body.run_id else run_query.order_by(LabRun.created_at.desc()).first()
        run_result = LabRunResult.model_validate_json(run.result_json) if run and run.result_json else None
        public_testbench_path = course_root / checkpoint.public_testbench
        public_testbench = public_testbench_path.read_text(encoding="utf-8")
        waveform_pulses = response_pulses(lab_artifact_dir(run.id) / "wave.vcd") if run and run.mode == "test" else []
        source_matches_run = run.source_hash == source_hash(workspace, checkpoint.source_files) if run else True
        checker_changed_since_run = bool(
            run and run.created_at and
            public_testbench_path.stat().st_mtime > run.created_at.replace(tzinfo=timezone.utc).timestamp()
        )
        history = db.query(LabMessage).filter(
            LabMessage.session_id == session_id, LabMessage.checkpoint_id == body.checkpoint_id,
        ).order_by(LabMessage.created_at.desc()).limit(6).all()
        tutor_reply = get_tutor_reply
        theory_context = {}
        if body.theory_page_id:
            if manifest.toolchain != "python" or not (course_root / "theory.json").is_file():
                raise HTTPException(status_code=400, detail="This course has no theory pages")
            from app.ldpc.theory import load_theory
            page = next((p for p in load_theory(course_root) if p.id == body.theory_page_id), None)
            if page is None:
                raise HTTPException(status_code=400, detail="Unknown theory page")
            theory_context = {"theory_page": page.model_dump()}
            # A prior coding failure must not displace a beginner's theory question.
            run_result = None
            run = None
            source_matches_run = True
            checker_changed_since_run = False
        if manifest.toolchain == "python":
            from app.ldpc.tutor import get_python_tutor_reply
            tutor_reply = get_python_tutor_reply
        reply, content = tutor_reply(
            checkpoint, student_files, body.message, run_result, body.requested_hint_level,
            body.selected_file, body.selected_start_line, body.selected_end_line,
            reference_files, public_testbench, waveform_pulses, source_matches_run, checker_changed_since_run,
            model_override=body.model, api_key_override=openrouter_api_key,
            allow_model_fallbacks=body.allow_model_fallbacks,
            session_scope=f"{session_id}:{body.theory_page_id or body.checkpoint_id}",
            conversation_history=[] if body.theory_page_id else [{"role": m.role, "content": m.content[:2000]} for m in reversed(history)],
            on_status=on_status,
            **theory_context,
        )
        user_message = LabMessage(session_id=session_id, checkpoint_id=body.checkpoint_id, run_id=run.id if run else None, role="user", content=body.message, hint_level=str(body.requested_hint_level))
        assistant_message = LabMessage(session_id=session_id, checkpoint_id=body.checkpoint_id, run_id=run.id if run else None, role="assistant", content=content, hint_level=str(reply.hint_level))
        db.add_all([user_message, assistant_message])
        db.commit()
        return {"reply": reply.model_dump(), "content": content, "run_id": run.id if run else None}
    finally:
        db.close()


@router.post("/lab-sessions/{session_id}/tutor/stream")
def stream_tutor_for_lab(
    session_id: str, body: TutorRequest,
    openrouter_api_key: str | None = Header(default=None, alias="X-OpenRouter-Api-Key", max_length=512),
):
    events = queue.Queue()
    cancelled = threading.Event()

    def progress(text):
        if cancelled.is_set():
            raise OpenCodeCancelled()
        if text != progress.last:
            events.put(("status", {"message": text}))
            progress.last = text
    progress.last = None

    def work():
        try:
            progress("Connecting to the guide…")
            result = _tutor_for_lab(session_id, body, openrouter_api_key, progress)
            events.put(("result", result))
        except OpenCodeCancelled:
            pass
        except HTTPException as exc:
            events.put(("error", {"detail": exc.detail}))
        except Exception:
            events.put(("error", {"detail": "The guide request failed. Please retry."}))

    def stream():
        threading.Thread(target=work, daemon=True).start()
        try:
            while True:
                try:
                    kind, data = events.get(timeout=5)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    continue
                yield f"event: {kind}\ndata: {json.dumps(data)}\n\n"
                if kind in {"result", "error"}:
                    break
        finally:
            cancelled.set()

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })
