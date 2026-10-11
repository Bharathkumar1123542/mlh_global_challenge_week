# Python Patterns

Small Python patterns for everyday automation.

## Reading Configuration

```python
from pathlib import Path

config_path = Path("settings.toml")
print(f"Reading {config_path.name}")
```

## Grouping Records

```py
records = [{"team": "A", "score": 8}, {"team": "B", "score": 5}]
by_team = {record["team"]: record["score"] for record in records}
print("Grouped records")
```

```ruby
puts "This block should be ignored"
```
