from pydantic import BaseModel


class BaseConfig(BaseModel):
    """
    Pydantic model as common base for configuration models.

    To control chart config changes to trigger model-data regenereration.
    """

    _has_changed: bool = False

    class Config:
        allow_mutation = True
        validate_assignment = True
        underscore_attrs_are_private = True

    def __setattr__(self, name, value):
        """Override setattr to control mutability flag '_has_changed'."""
        super().__setattr__(name, value)
        if name != "_has_changed":
            self._has_changed = True

    @property
    def has_changed(self) -> bool:
        """
        Test if the object has been modified since creation, including childs.
        """
        return self._has_changed or any(
            getattr(field, "has_changed", False)
            for field in self.__dict__.values()
        )

    def commit_changes(self):
        """Reset mutation flag 'has_changed' for the object and its childs."""
        if self.has_changed:
            self._has_changed = False
            for field in self.__dict__.values():
                if hasattr(field, "commit_changes") and field.has_changed:
                    field.commit_changes()
