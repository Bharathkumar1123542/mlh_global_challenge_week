# Data Workflows

## CSV Summary

```python
from collections import Counter

statuses = ["ready", "ready", "draft"]
summary = Counter(statuses)
print(summary)
```

## Pipeline Notice

```javascript
const stages = ['extract', 'transform', 'load'];
console.log('Stages: ' + stages.join(', '));
```

## SQL Reference

```sql
SELECT status, COUNT(*) FROM jobs GROUP BY status;
```
