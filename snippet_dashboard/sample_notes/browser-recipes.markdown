# Browser Recipes

## Fetch JSON

```javascript
const response = await fetch('/api/items');
const items = await response.json();
console.log(`Loaded ${items.length} items`);
```

## Button Feedback

~~~js
const button = document.querySelector('#save');
button.addEventListener('click', () => {
  console.log('Saved successfully');
});
~~~

~~~html
<button id="save">Save</button>
~~~
