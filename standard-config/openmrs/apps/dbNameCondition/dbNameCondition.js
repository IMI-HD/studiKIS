Bahmni.Common.Offline.dbNameCondition.get = function (provider, loginLocation) {
    return loginLocation;
};

if (!window.kasHooked) {
    window.kasHooked = true; setInterval(function () {
        if (window.location.href.indexOf('/bahmni/') > -1 && document.title && !document.title.startsWith('[KAS]')) { document.title = '[KAS] ' + document.title; }
    }, 1000);
}