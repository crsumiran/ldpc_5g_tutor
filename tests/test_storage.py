import uuid
from app.db import SessionLocal
from app.models import Analysis, Job, Project


def test_project_and_analysis_storage():
    db = SessionLocal()
    try:
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            source_type="local",
            source_uri="/home/ranga/opencode/tutor/fixtures/python_etl",
            snapshot_hash="dummy_hash_12345",
            snapshot_path=f"/home/ranga/opencode/tutor/data/projects/{project_id}/source",
        )
        db.add(project)
        db.commit()

        # Read back project
        p = db.query(Project).filter(Project.id == project_id).first()
        assert p is not None
        assert p.source_type == "local"
        assert p.snapshot_hash == "dummy_hash_12345"

        # Create analysis
        analysis_id = str(uuid.uuid4())
        analysis = Analysis(
            id=analysis_id,
            project_id=project_id,
            json='{"project_summary": "test"}',
        )
        db.add(analysis)
        db.commit()

        a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        assert a is not None
        assert a.project_id == project_id
        assert a.json == '{"project_summary": "test"}'
    finally:
        db.close()


def test_job_storage():
    db = SessionLocal()
    try:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            kind="analyze",
            status="queued",
        )
        db.add(job)
        db.commit()

        j = db.query(Job).filter(Job.id == job_id).first()
        assert j is not None
        assert j.status == "queued"

        # Update job
        j.status = "done"
        j.result_json = '{"ok": true}'
        db.commit()

        j2 = db.query(Job).filter(Job.id == job_id).first()
        assert j2.status == "done"
        assert j2.result_json == '{"ok": true}'
    finally:
        db.close()
