# Observer

## python
```python
from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data) -> None:
        pass


class Subject:
    """Observable subject that notifies registered observers."""

    def __init__(self):
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event: str, data=None) -> None:
        for observer in self._observers:
            observer.update(event, data)


class LoggingObserver(Observer):
    def update(self, event: str, data) -> None:
        print(f"[LOG] Event: {event}, Data: {data}")


class AlertObserver(Observer):
    def update(self, event: str, data) -> None:
        if event == "critical":
            print(f"[ALERT] Critical event: {data}")


# Example
subject = Subject()
subject.subscribe(LoggingObserver())
subject.subscribe(AlertObserver())

subject.notify("info", "server started")
subject.notify("critical", "disk full")
```
