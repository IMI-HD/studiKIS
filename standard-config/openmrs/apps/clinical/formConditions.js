```javascript
Bahmni.ConceptSet.FormConditions.rules = {};

if (!window.kasHooked) {
    window.kasHooked = true;
    setInterval(function () {
        if (window.location.href.indexOf('/bahmni/') > -1 && document.title && !document.title.startsWith('[KAS]')) {
            document.title = '[KAS] ' + document.title;
        }
    }, 1000);
}
```