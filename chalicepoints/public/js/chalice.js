"use strict";

$(document).foundation();

angular.module('cpPointsFilters', [])
    .filter('dateMoment', function($filter) {
        var dateFilter = $filter('date');
        return function(dateString, format) {
            var momentDate = moment(dateString).toDate()
            return dateFilter(momentDate, format);
        };
    })
    .filter('join', function($filter) {
        return function(array, delimiter) {
            return array.join(delimiter);
        };
    })
    .filter('amountMax', function($filter) {
        return function(array) {
            var maxAmount = 0;
            for (var idx in array) {
                maxAmount = Math.max(maxAmount, array[idx].amount);
            }

            return maxAmount;
        };
    });

angular.module('cpPointsServices', ['ngResource', 'cpPointsFilters'])
    .factory('Leaderboard', function($resource) {
        return $resource('api/1.0/leaderboard.json', {});
    })
    .factory('User', function($resource) {
        return $resource('api/1.0/user/:userId.json', {
            userId: 'list'
        });
    })
    .factory('Winner', function($resource) {
        return $resource('api/1.0/winners.json', {});
    })
    .factory('CPEvent', function($resource) {
        return $resource('api/1.0/event.json', {});
    })
    .factory('flash', function($rootScope, $timeout) {
        $rootScope.message = {};

        var reset;
        var cleanup = function() {
            $timeout.cancel(reset);
            reset = $timeout(function() {
                $('.alert-box').slideUp(400, function() {
                    $rootScope.message = {};
                });
            }, 2000);
        };

        return function(level, text) {
            $rootScope.message = {
                level: level,
                text: text
            };

            $('.alert-box').slideDown();

            cleanup();
        };
    });

angular.module('cpPoints', ['cpPointsServices'])
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: 'public/partials/leaderboard.html',
                controller: LeaderboardCtrl,
                resolve: LeaderboardCtrl.resolve
            })
            .when('/chart', {
                templateUrl: 'public/partials/chart.html',
                controller: ChartCtrl
            })
            .when('/chart/:mode', {
                templateUrl: 'public/partials/chart.html',
                controller: ChartCtrl
            })
            .when('/user/:userId', {
                templateUrl: 'public/partials/profile.html',
                controller: UserCtrl,
                resolve: UserCtrl.resolve
            })
            .when('/winners', {
                templateUrl: 'public/partials/winners.html',
                controller: WinnersCtrl,
                resolve: WinnersCtrl.resolve
            })
            .otherwise({
                redirectTo: '/'
            });
    }]).run(['$rootScope', function($rootScope) {
        // Publish the user on the root scope.
        var user_json = document.getElementById('user').innerHTML
        $rootScope.user = angular.fromJson(user_json);
    }])

var LeaderboardCtrl = ['$scope', 'flash', 'leaderboard', 'users', 'CPEvent', 'Leaderboard', function($scope, flash, leaderboard, users, CPEvent, Leaderboard) {
    $scope.leaderboard = leaderboard;
    $scope.givers = $scope.leaderboard.given;
    $scope.receivers = $scope.leaderboard.received;
    $scope.users = users;

    $scope.pointsAmount = 1;

    $scope.addEvent = function() {
        if ($scope.pointsTarget == $scope.user.name) {
            flash('alert', 'Really? You can\'t give yourself points.');
            return;
        }

        $scope.pointsAmount = Math.max(Math.min(5, $scope.pointsAmount), 1);

        var cpEvent = new CPEvent({
            target: $scope.pointsTarget,
            amount: $scope.pointsAmount,
            message: $scope.pointsMessage
        });

        cpEvent.$save(function(data) {
            flash('success', 'Chalice Point Given');

            $scope.pointsAmount = 1
            $scope.pointsTarget = ''
            $scope.pointsMessage = ''

            $scope.leaderboard = Leaderboard.get(function() {
                $scope.givers = $scope.leaderboard.given;
                $scope.receivers = $scope.leaderboard.received;
            });
        });
    };
}];

LeaderboardCtrl.resolve = {
    leaderboard: function($q, Leaderboard) {
        var deferred = $q.defer();
        var res = Leaderboard.get(function() {
            deferred.resolve(res);
        });
        return deferred.promise;
    },
    users: function($q, User) {
        var deferred = $q.defer();
        var res = User.query(function() {
            deferred.resolve(res);
        });
        return deferred.promise;
    }
};

var ChartCtrl = ['$scope', '$routeParams', function($scope, $routeParams) {
    $scope.mode = $routeParams.mode ? $routeParams.mode.toLowerCase() : 'received';
    ChalicePoints.Chord($scope.mode);
}];

var WinnersCtrl = ['$scope', 'winners', function($scope, winners) {
    $scope.winners = winners;
}];

WinnersCtrl.resolve = {
    winners: function($q, Winner, $route) {
        var deferred = $q.defer();
        var res = Winner.query(function() {
            deferred.resolve(res);
        });

        return deferred.promise;
    }
};

var UserCtrl = ['$scope', '$routeParams', 'CPEvent', 'User', 'user', function($scope, $routeParams, CPEvent, User, user) {
    user.gravatar += '?s=50&d=mm';
    $scope.user = user;
    $scope.admin = $routeParams.admin ? true : false;

    $scope.removeEvent = function(type, user, dateTime) {
        var source = user;
        var target = $scope.user.name;

        if (type == 'given') {
            source = user;
            target = $scope.user.name;
        }

        var pointEvent = new CPEvent({
            source: source,
            target: target,
            'date': dateTime
        });

        pointEvent.$remove(function(data) {
            $scope.user = User.get({
                userId: $scope.user.name
            });
        });
    };
}];

UserCtrl.resolve = {
    user: function($q, User, $route) {
        var deferred = $q.defer();
        var res = User.get({
            userId: $route.current.params.userId
        }, function() {
            deferred.resolve(res);
        });
        return deferred.promise;
    }
};

var ChalicePoints = {
    type: 'received'
};

ChalicePoints.Chord = function(type) {
    ChalicePoints.type = type || 'received';

    var elem = document.getElementById('chart');
    if (!elem) {
        return false;
    }

    elem.innerHTML = '';

    var width = 650;
    var height = 650;
    var outerRadius = Math.min(width, height) / 2;
    var innerRadius = outerRadius - 45;

    var arc = d3.svg.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    var layout = d3.layout.chord()
        .padding(.04)
        .sortSubgroups(d3.descending)
        .sortChords(d3.ascending);

    var path = d3.svg.chord()
        .radius(innerRadius);

    var svg = d3.select('#chart').append('svg')
        .attr('width', width)
        .attr('height', height)
    .append('g')
        .attr('id', 'circle')
        .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

    svg.append('circle')
        .attr('r', outerRadius);

    var colors = d3.scale.category20();

    d3.json('api/1.0/user.json', function(users) {
        d3.json('api/1.0/matrix/' + ChalicePoints.type + '.json', function(matrix) {
            layout.matrix(matrix);

            var group = svg.selectAll('.group')
                .data(layout.groups)
            .enter().append('g')
                .attr('class', 'group')
                .attr('title', function(d, i) {
                    var title = 'Unknown';
                    if (users[i]) {
                        title = users[i].name + ': ' + Math.round(d.value);
                    }
                    
                    return title;
                })
                .on('mouseover', mouseover);

            group.append('title').text(function(d, i) {
                var title = 'Unknown';
                if (users[i]) {
                    title = users[i].name + ': ' + Math.round(d.value);
                }

                return title;
            });

            var groupPath = group.append('path')
                .attr('id', function(d, i) {
                    return 'group' + i;
                })
                .attr('d', arc)
                .style('fill', function(d, i) {
                    return colors(i);
                });

            var groupText = group.append('text')
                .attr('x', 10)
                .attr('dy', 20);

            groupText.append('textPath')
                .attr('xlink:href', function(d, i) {
                    return '#group' + i;
                })
                .text(function(d, i) {
                    var text = 'Unknown';
                    if (users[i]) {
                        text = users[i].name;
                    }

                    return text;
                });

            groupText.filter(function(d, i) {
                return groupPath[0][i].getTotalLength() / 2 - 10 < this.getComputedTextLength();
            }).remove();

            var chord = svg.selectAll('.chord')
                .data(layout.chords)
            .enter().append('path')
                .attr('class', 'chord')
                .style('fill', function(d) {
                    return colors(d.source.index);
                })
                .attr('d', path);

            chord.append('title').text(function(d) {
                var tooltip = 'Unknown';
                if (ChalicePoints.type == 'received') {
                    if (users[d.source.index] && users[d.target.index]) {
                        tooltip = users[d.source.index].name
                            + ' -> ' + users[d.target.index].name
                            + ': ' + d.target.value
                            + "\n"
                            + users[d.target.index].name
                            + ' -> ' + users[d.source.index].name
                            + ': ' + d.source.value;
                    }
                } else {
                    if (users[d.source.index] && users[d.target.index]) {
                        tooltip = users[d.target.index].name
                            + ' -> ' + users[d.source.index].name
                            + ': ' + d.target.value
                            + "\n"
                            + users[d.source.index].name
                            + ' -> ' + users[d.target.index].name
                            + ': ' + d.source.value;
                    }
                }

                return tooltip;
            });

            function mouseover(d, i) {
                chord.classed('fade', function(p) {
                    return p.source.index != i && p.target.index != i;
                });
            }
        });
    });
};

function matrixChoice(type) {
    ChalicePoints.Chord(type);
}
