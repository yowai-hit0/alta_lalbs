from fastapi import HTTPException, status


def require_roles(*roles: str):
    def checker(user: dict):
        if user.get('global_role') not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
        return True
    return checker




