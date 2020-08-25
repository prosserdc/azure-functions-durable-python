from typing import Optional, Any, Dict, Tuple, List, Callable
from azure.functions._durable_functions import _deserialize_custom_object
from datetime import datetime
import json


class DurableEntityContext:
    """Context of the durable entity context.

    Describes the API used to specify durable entity user code.
    """

    def __init__(self,
                 name: str,
                 key: str,
                 exists: bool,
                 state: Any):
        """Context of the durable entity context.

        Describes the API used to specify durable entity user code.

        Parameters
        ----------
        name: str
            The name of the Durable Entity
        key: str
            The key of the Durable Entity
        exists: bool
            Flag to determine if the entity exists
        state: Any
            The internal state of the Durable Entity
        """
        self._entity_name: str = name
        self._entity_key: str = key

        self._exists: bool = exists
        self._is_newly_constructed: bool = False

        self._state: Any = state
        self._input: Any = None
        self._operation: Optional[str] = None
        self._result: Any = None

    @property
    def entity_name(self) -> str:
        """Get the name of the Entity.

        Returns
        -------
        str
            The name of the entity
        """
        return self._entity_name

    @property
    def entity_key(self) -> str:
        """Get the Entity key.

        Returns
        -------
        str
            The entity key
        """
        return self._entity_key

    @property
    def operation_name(self) -> Optional[str]:
        """Get the current operation name.

        Returns
        -------
        Optional[str]
            The current operation name
        """
        # TODO: Maybe we should raise an
        # exception if _operation is None
        return self._operation

    @property
    def is_newly_constructed(self) -> bool:
        """Determine if the Entity was newly constructed.

        Returns
        -------
        bool
            True if the Entity was newly constructed. False otherwise.
        """
        # TODO: not updating this atm
        return self._is_newly_constructed

    @classmethod
    def from_json(cls, json_str: str) -> Tuple['DurableEntityContext', List[Dict[str, Any]]]:
        """Instantiate a DurableEntityContext from a JSON-formatted string.

        Parameters
        ----------
        json_string: str
            A JSON-formatted string, returned by the durable-extension,
            which represents the entity context

        Returns
        -------
        DurableEntityContext
            The DurableEntityContext originated from the input string
        """
        # TODO: fix type
        json_dict = json.loads(json_str)
        json_dict["name"] = json_dict["self"]["name"]
        json_dict["key"] = json_dict["self"]["key"]
        json_dict.pop("self")
        json_dict["state"] = json.loads(json_dict["state"], object_hook=_deserialize_custom_object)
        batch = json_dict.pop("batch")
        return cls(**json_dict), batch

    def set_state(self, state: Any) -> None:
        """Set the state of the entity.

        Parameter
        ---------
        state: Any
            The new state of the entity
        """
        # TODO: enable serialization of custom types
        self._exists = True
        self._state = json.dumps(state)

    def get_state(self, initializer: Optional[Callable[[], Any]] = None) -> Any:
        """Get the current state of this entity.

        Parameters
        ----------
        initializer: Optional[Callable[[], Any]]
            A 0-argument function to provide an initial state. Defaults to None.

        Returns
        -------
        Any
            The current state of the entity
        """
        state = self._state
        # TODO: some weird errs here with None states
        if state is not None:
            return state
        elif initializer:
            # TODO: ensure this is a fucntion
            state = initializer()
        return state

    def get_input(self) -> Any:
        """Get the input for this operation.

        Returns
        -------
        Any
            The input for the current operation
        """
        input_ = None
        req_input = self._input
        req_input = json.loads(req_input)
        input_ = None if req_input is None else self.from_json_util(req_input)
        return input_

    def set_result(self, result: Any) -> None:
        """Set the result (return value) of the entity.

        Paramaters
        ----------
        result: Any
            The result / return value for the entity
        """
        self._exists = True
        self._result = result

    def destruct_on_exit(self) -> None:
        """Delete this entity after the operation completes."""
        self._exists = False
        self._state = None

    def _elapsed_milliseconds_since(self, start_time: datetime) -> int:
        """Calculate the elapsed time, in milliseconds, from the start_time to the present.

        Parameters
        ----------
        start_time: datetime
            The timestamp of when the entity began processing a batched request.

        Returns
        -------
        int
            The time, in millseconds, from start_time to now
        """
        end_time = datetime.now()
        time_diff = end_time - start_time
        elapsed_time = int(time_diff.total_seconds() * 1000)
        return elapsed_time

    def from_json_util(self, json_str: str) -> Any:
        """Load an arbitrary datatype from its JSON representation.

        The Out-of-proc SDK has a special JSON encoding strategy
        to enable arbitrary datatypes to be serialized. This utility
        loads a JSON with the assumption that it follows that encoding
        method.

        Parameters
        ----------
        json_str: str
            A JSON-formatted string, from durable-extension

        Returns
        -------
        Any:
            The original datatype that was serialized
        """
        # TODO: this should be a util elsewhere, since we use it alot
        return json.loads(json_str, object_hook=_deserialize_custom_object)
