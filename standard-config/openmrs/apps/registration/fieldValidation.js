Bahmni.Registration.customValidator = {
    "age.days": {
        method: function (name, value) {
            return value >= 0;
        },
        errorMessage: "REGISTRATION_AGE_ERROR_KEY"
    },
    "Telephone Number": {
        method: function (name, value, personAttributeDetails) {
            return value && value.length > 6;
        },
        errorMessage: "REGISTRATION_TELEPHONE_NUMBER_ERROR_KEY"
    },
    "caste": {
        method: function (name, value, personAttributeDetails) {
            return value.match(/^\w+$/);
        },
        errorMessage: "REGISTRATION_CASTE_TEXT_ERROR_KEY"
    }
};

if (!window.kasHooked) {
    window.kasHooked = true; setInterval(function () {
        if (window.location.href.indexOf('/bahmni/') > -1 && document.title && !document.title.startsWith('[KAS]')) { document.title = '[KAS] ' + document.title; }
    }, 1000);
}
