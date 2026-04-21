from . import (
    application,
    candidate,
    file as file_cmd,
    interview,
    interview_event,
    interview_plan,
    interview_schedule,
    interview_stage,
    interview_stage_group,
    interviewer_pool,
    job,
    job_posting,
)

ALL_GROUPS = [
    candidate.candidate,
    file_cmd.file_group,
    job.job,
    job_posting.job_posting,
    application.application,
    interview_event.interview_event,
    interview_plan.interview_plan,
    interview_schedule.interview_schedule,
    interview_stage.interview_stage,
    interview_stage_group.interview_stage_group,
    interview.interview,
    interviewer_pool.interviewer_pool,
]
