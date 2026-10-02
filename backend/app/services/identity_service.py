from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.identity import User
from app.repositories import identity_repository
from app.services.feishu_oauth import FeishuIdentity


class AuthFlowError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def resolve_corporate_email(identity: FeishuIdentity) -> str:
    primary_email = identity.enterprise_email
    raw_email = primary_email if isinstance(primary_email, str) and primary_email.strip() else identity.email
    if not isinstance(raw_email, str) or not raw_email.strip():
        raise AuthFlowError("email_not_found")
    email = raw_email.strip().lower()
    local_part, separator, domain = email.rpartition("@")
    if not separator or not local_part or not domain:
        raise AuthFlowError("email_not_found")
    if domain not in settings.corporate_domain_allowlist:
        raise AuthFlowError("unauthorized_domain")
    return email


def provision_internal_user(session: Session, identity: FeishuIdentity) -> User:
    email = resolve_corporate_email(identity)
    user = identity_repository.get_user_by_email(session, email)
    linked_users = identity_repository.get_users_by_feishu_ids(session, identity.open_id, identity.union_id)
    if any((user is None) or linked_user.id != user.id for linked_user in linked_users):
        raise AuthFlowError("identity_conflict")

    if user is not None:
        if user.status != "ACTIVE":
            raise AuthFlowError("user_inactive")
        if user.access_type != "INTERNAL":
            raise AuthFlowError("identity_conflict")
        if identity.open_id and user.feishu_open_id not in (None, identity.open_id):
            raise AuthFlowError("identity_conflict")
        if identity.union_id and user.feishu_union_id not in (None, identity.union_id):
            raise AuthFlowError("identity_conflict")
        if identity.open_id and user.feishu_open_id is None:
            user.feishu_open_id = identity.open_id
        if identity.union_id and user.feishu_union_id is None:
            user.feishu_union_id = identity.union_id
    else:
        if not isinstance(identity.name, str) or not identity.name.strip():
            raise AuthFlowError("identity_conflict")
        user = identity_repository.add_user(
            session,
            email=email,
            name=identity.name.strip(),
            open_id=identity.open_id,
            union_id=identity.union_id,
        )
        role = identity_repository.get_role_by_code(session, "COLLABORATOR")
        if role is None:
            raise AuthFlowError("session_creation_failed")
        identity_repository.add_user_role(session, user.id, role.id)

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return user
