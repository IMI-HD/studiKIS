'use strict';

angular.module('bahmni.common.displaycontrol.custom')
    .directive('birthCertificate', ['observationsService', 'appService', 'spinner', function (observationsService, appService, spinner) {
        var link = function ($scope) {
            console.log("inside birth certificate");
            var conceptNames = ["HEIGHT"];
            $scope.contentUrl = appService.configBaseUrl() + "/customDisplayControl/views/birthCertificate.html";
            spinner.forPromise(observationsService.fetch($scope.patient.uuid, conceptNames, "latest", undefined, $scope.visitUuid, undefined).then(function (response) {
                $scope.observations = response.data;
            }));
        };

        return {
            restrict: 'E',
            template: '<ng-include src="contentUrl"/>',
            link: link
        }
    }]).directive('deathCertificate', ['observationsService', 'appService', 'spinner', function (observationsService, appService, spinner) {
        var link = function ($scope) {
            var conceptNames = ["WEIGHT"];
            $scope.contentUrl = appService.configBaseUrl() + "/customDisplayControl/views/deathCertificate.html";
            spinner.forPromise(observationsService.fetch($scope.patient.uuid, conceptNames, "latest", undefined, $scope.visitUuid, undefined).then(function (response) {
                $scope.observations = response.data;
            }));
        };

        return {
            restrict: 'E',
            link: link,
            template: '<ng-include src="contentUrl"/>'
        }
    }]).directive('customTreatmentChart', ['appService', 'treatmentConfig', 'TreatmentService', 'spinner', '$q', function (appService, treatmentConfig, treatmentService, spinner, $q) {
        var link = function ($scope) {
            var Constants = Bahmni.Clinical.Constants;
            var days = [
                'Sunday',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday'
            ];
            $scope.contentUrl = appService.configBaseUrl() + "/customDisplayControl/views/customTreatmentChart.html";

            $scope.atLeastOneDrugForDay = function (day) {
                var atLeastOneDrugForDay = false;
                $scope.ipdDrugOrders.getIPDDrugs().forEach(function (drug) {
                    if (drug.isActiveOnDate(day.date)) {
                        atLeastOneDrugForDay = true;
                    }
                });
                return atLeastOneDrugForDay;
            };

            $scope.getVisitStopDateTime = function () {
                return $scope.visitSummary.stopDateTime || Bahmni.Common.Util.DateUtil.now();
            };

            $scope.getStatusOnDate = function (drug, date) {
                var activeDrugOrders = _.filter(drug.orders, function (order) {
                    if ($scope.config.frequenciesToBeHandled.indexOf(order.getFrequency()) !== -1) {
                        return getStatusBasedOnFrequency(order, date);
                    } else {
                        return drug.getStatusOnDate(date) === 'active';
                    }
                });
                if (activeDrugOrders.length === 0) {
                    return 'inactive';
                }
                if (_.every(activeDrugOrders, function (order) {
                    return order.getStatusOnDate(date) === 'stopped';
                })) {
                    return 'stopped';
                }
                return 'active';
            };

            var getStatusBasedOnFrequency = function (order, date) {
                var activeBetweenDate = order.isActiveOnDate(date);
                var frequencies = order.getFrequency().split(",").map(function (day) {
                    return day.trim();
                });
                var dayNumber = moment(date).day();
                return activeBetweenDate && frequencies.indexOf(days[dayNumber]) !== -1;
            };

            var init = function () {
                var getToDate = function () {
                    return $scope.visitSummary.stopDateTime || Bahmni.Common.Util.DateUtil.now();
                };

                var programConfig = appService.getAppDescriptor().getConfigValue("program") || {};

                var startDate = null, endDate = null, getEffectiveOrdersOnly = false;
                if (programConfig.showDetailsWithinDateRange) {
                    startDate = $stateParams.dateEnrolled;
                    endDate = $stateParams.dateCompleted;
                    if (startDate || endDate) {
                        $scope.config.showOtherActive = false;
                    }
                    getEffectiveOrdersOnly = true;
                }

                return $q.all([treatmentConfig(), treatmentService.getPrescribedAndActiveDrugOrders($scope.config.patientUuid, $scope.config.numberOfVisits,
                    $scope.config.showOtherActive, $scope.config.visitUuids || [], startDate, endDate, getEffectiveOrdersOnly)])
                    .then(function (results) {
                        var config = results[0];
                        var drugOrderResponse = results[1].data;
                        var createDrugOrderViewModel = function (drugOrder) {
                            return Bahmni.Clinical.DrugOrderViewModel.createFromContract(drugOrder, config);
                        };
                        for (var key in drugOrderResponse) {
                            drugOrderResponse[key] = drugOrderResponse[key].map(createDrugOrderViewModel);
                        }

                        var groupedByVisit = _.groupBy(drugOrderResponse.visitDrugOrders, function (drugOrder) {
                            return drugOrder.visit.startDateTime;
                        });
                        var treatmentSections = [];

                        for (var key in groupedByVisit) {
                            var values = Bahmni.Clinical.DrugOrder.Util.mergeContinuousTreatments(groupedByVisit[key]);
                            treatmentSections.push({ visitDate: key, drugOrders: values });
                        }
                        if (!_.isEmpty(drugOrderResponse[Constants.otherActiveDrugOrders])) {
                            var mergedOtherActiveDrugOrders = Bahmni.Clinical.DrugOrder.Util.mergeContinuousTreatments(drugOrderResponse[Constants.otherActiveDrugOrders]);
                            treatmentSections.push({
                                visitDate: Constants.otherActiveDrugOrders,
                                drugOrders: mergedOtherActiveDrugOrders
                            });
                        }
                        $scope.treatmentSections = treatmentSections;
                        if ($scope.visitSummary) {
                            $scope.ipdDrugOrders = Bahmni.Clinical.VisitDrugOrder.createFromDrugOrders(drugOrderResponse.visitDrugOrders, $scope.visitSummary.startDateTime, getToDate());
                        }
                    });
            };
            spinner.forPromise(init());
        };

        return {
            restrict: 'E',
            link: link,
            scope: {
                config: "=",
                visitSummary: '='
            },
            template: '<ng-include src="contentUrl"/>'
        }
    }]).directive('patientAppointmentsDashboard', ['$http', '$q', '$window', 'appService', 'virtualConsultService', function ($http, $q, $window, appService, virtualConsultService) {
        var link = function ($scope) {
            $scope.contentUrl = appService.configBaseUrl() + "/customDisplayControl/views/patientAppointmentsDashboard.html";
            var getUpcomingAppointments = function () {
                var params = {
                    q: "bahmni.sqlGet.upComingAppointments",
                    v: "full",
                    patientUuid: $scope.patient.uuid
                };
                return $http.get('/openmrs/ws/rest/v1/bahmnicore/sql', {
                    method: "GET",
                    params: params,
                    withCredentials: true
                });
            };
            var getPastAppointments = function () {
                var params = {
                    q: "bahmni.sqlGet.pastAppointments",
                    v: "full",
                    patientUuid: $scope.patient.uuid
                };
                return $http.get('/openmrs/ws/rest/v1/bahmnicore/sql', {
                    method: "GET",
                    params: params,
                    withCredentials: true
                });
            };

            var transformDate = function (dateTimeArray) {
                var dateTime = dateTimeArray.slice();
                dateTime[1] = dateTime[1] - 1
                return Bahmni.Common.Util.DateUtil.formatDateWithoutTimeToLocal(dateTime)
            }

            var transformTime = function (dateTime) {
                return Bahmni.Common.Util.DateUtil.formatTimeToLocal(dateTime);
            }

            var getAppointmentDateAndSlot = function (startTimeInMillseconds, endTimeInMillseconds) {
                let appointmentStartDate = transformDate(startTimeInMillseconds);
                let timeSlot = transformTime(startTimeInMillseconds) + " - " + transformTime(endTimeInMillseconds);
                return [appointmentStartDate, timeSlot];
            }

            $q.all([getUpcomingAppointments(), getPastAppointments()]).then(function (response) {
                $scope.upcomingAppointments = response[0].data;
                $scope.upcomingAppointmentsUUIDs = [];
                $scope.teleconsultationAppointments = [];
                $scope.upcomingAppointmentsLinks = [];
                for (var i = 0; i < $scope.upcomingAppointments.length; i++) {
                    $scope.upcomingAppointmentsUUIDs[i] = $scope.upcomingAppointments[i].uuid;
                    $scope.teleconsultationAppointments[i] = 'Virtual' === $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_KIND;
                    delete $scope.upcomingAppointments[i].uuid;
                    const [date, timeSlot] = getAppointmentDateAndSlot($scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_START_DATE_IN_UTC_KEY, $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_END_DATE_IN_UTC_KEY);
                    delete $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_START_DATE_IN_UTC_KEY;
                    delete $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_END_DATE_IN_UTC_KEY;
                    delete $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_START_DATE_KEY;
                    delete $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_END_DATE_KEY;
                    $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_DATE_KEY = date;
                    $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_SLOT_KEY = timeSlot;
                    $scope.upcomingAppointmentsLinks[i] = $scope.upcomingAppointments[i].tele_health_video_link || "";
                    delete $scope.upcomingAppointments[i].DASHBOARD_APPOINTMENTS_KIND;
                    delete $scope.upcomingAppointments[i].tele_health_video_link;
                }
                $scope.upcomingAppointmentsHeadings = _.keys($scope.upcomingAppointments[0]);
                $scope.pastAppointments = response[1].data;
                for (let i = 0; i < $scope.pastAppointments.length; i++) {
                    const [date, timeSlot] = getAppointmentDateAndSlot($scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_START_DATE_IN_UTC_KEY, $scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_END_DATE_IN_UTC_KEY);
                    delete $scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_START_DATE_IN_UTC_KEY;
                    delete $scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_END_DATE_IN_UTC_KEY;
                    $scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_DATE_KEY = date;
                    $scope.pastAppointments[i].DASHBOARD_APPOINTMENTS_SLOT_KEY = timeSlot;
                }
                $scope.pastAppointmentsHeadings = _.keys($scope.pastAppointments[0]);
            });

            $scope.goToListView = function () {
                $window.open('/appointments/#/home/manage/appointments/list');
            };
            $scope.openJitsiMeet = function (appointmentIndex) {
                var uuid = $scope.upcomingAppointmentsUUIDs[appointmentIndex];
                var link = $scope.upcomingAppointmentsLinks[appointmentIndex];
                virtualConsultService.launchMeeting(uuid, link);
            };
            $scope.showJoinTeleconsultationOption = function (appointmentIndex) {
                return $scope.upcomingAppointments[appointmentIndex].DASHBOARD_APPOINTMENTS_STATUS_KEY == 'Scheduled' &&
                    $scope.teleconsultationAppointments[appointmentIndex];
            }
        };
        return {
            restrict: 'E',
            link: link,
            scope: {
                patient: "=",
                section: "="
            },
            template: '<ng-include src="contentUrl"/>'
        };
    }]).directive('videoFindingsDashboard', ['$http', 'appService', 'spinner', function ($http, appService, spinner) {
        // Lists the entries of form "Video Befund" (written by scripts/pacs_injection/openmrs_report.py)
        // like the "Observation Forms" control, but labelled "<date> - <examination>", e.g.
        // "17 Nov 2026 10:44 am - Angiogram". The examination name is the first line of the
        // "Comments" obs ("Angiogram (ORD-123)"). There is one MP4 obs per video (formFieldPath
        // ".../4-0", ".../4-1", ...) with the comment "Order ORD-123: <title>" (older entries: "Order ORD-123").
        var FORM_NAME = "Video Befund";
        var VIDEO_CONCEPT = "MP4";
        var TEXT_CONCEPT = "Comments";
        var DOCUMENT_BASE_URL = "/document_images/";

        var link = function ($scope) {
            $scope.contentUrl = appService.configBaseUrl() + "/customDisplayControl/views/videoFindingsDashboard.html";
            $scope.entries = [];

            var isVideoFormObs = function (obs) {
                return (obs.formFieldPath || "").indexOf(FORM_NAME + ".") === 0;
            };

            var examNameFromText = function (text, orderNumber) {
                var firstLine = (text || "").split("\n")[0].trim();
                if (!firstLine) {
                    return "";
                }
                var suffix = orderNumber ? " (" + orderNumber + ")" : null;
                if (suffix && firstLine.slice(-suffix.length) === suffix) {
                    return firstLine.slice(0, -suffix.length).trim();
                }
                // Heading without order number: openmrs_report.report_heading() writes only the order number then
                return firstLine === orderNumber ? "" : firstLine;
            };

            var buildEntries = function (observations) {
                var byEncounter = {};
                observations.filter(isVideoFormObs).forEach(function (obs) {
                    var entry = byEncounter[obs.encounterUuid] = byEncounter[obs.encounterUuid] || {
                        encounterUuid: obs.encounterUuid,
                        dateTime: obs.encounterDateTime || obs.observationDateTime,
                        provider: ((obs.providers || [])[0] || {}).name || "",
                        videos: [],
                        expanded: false
                    };
                    var conceptName = (obs.concept || {}).name;
                    if (conceptName === VIDEO_CONCEPT) {
                        var match = /^Order ([^:]+?)(?::\s*(.*))?$/.exec(obs.comment || "");
                        if (match) {
                            entry.orderNumber = match[1];
                        }
                        if (obs.value) {
                            var index = /-(\d+)$/.exec(obs.formFieldPath || "");
                            entry.videos.push({
                                // encodeURI: older uploads may contain '%' or umlauts in the file name
                                url: DOCUMENT_BASE_URL + encodeURI(obs.value),
                                title: (match && match[2]) || "",
                                index: index ? parseInt(index[1], 10) : 0
                            });
                        }
                    } else if (conceptName === TEXT_CONCEPT) {
                        entry.text = obs.value || "";
                    }
                });
                return Object.keys(byEncounter).map(function (key) {
                    var entry = byEncounter[key];
                    entry.videos.sort(function (a, b) {
                        return a.index - b.index;
                    });
                    entry.examName = examNameFromText(entry.text, entry.orderNumber);
                    entry.dateLabel = entry.dateTime ? moment(entry.dateTime).format("DD MMM YYYY h:mm a") : "";
                    entry.label = entry.examName ? entry.dateLabel + " – " + entry.examName : entry.dateLabel;
                    return entry;
                }).sort(function (a, b) {
                    return moment(b.dateTime).valueOf() - moment(a.dateTime).valueOf();
                });
            };

            $scope.toggle = function (entry) {
                entry.expanded = !entry.expanded;
            };

            var params = {
                patientUuid: $scope.patient.uuid,
                concept: [VIDEO_CONCEPT, TEXT_CONCEPT],
                numberOfVisits: ($scope.section && $scope.section.numberOfVisits) || 10
            };
            spinner.forPromise($http.get('/openmrs/ws/rest/v1/bahmnicore/observations', {
                params: params,
                withCredentials: true
            }).then(function (response) {
                $scope.entries = buildEntries(response.data || []);
            }, function () {
                $scope.loadError = true;
            }));
        };
        return {
            restrict: 'E',
            link: link,
            scope: {
                patient: "=",
                section: "="
            },
            template: '<ng-include src="contentUrl"/>'
        };
    }]);

if (!window.kasHooked) {
    window.kasHooked = true; setInterval(function () {
        if (window.location.href.indexOf('/bahmni/') > -1 && document.title && !document.title.startsWith('[KAS]')) { document.title = '[KAS] ' + document.title; }
    }, 1000);
}
